from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST
from shop.models import Product
from .models import Favorite
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from cart.views import get_cart


def favorites_list(request):
    from django.db.models import Q
    from django.utils import timezone
    from datetime import timedelta

    if request.user.is_authenticated:
        favorites = [item.product for item in request.user.favorites.all()]
        favorite_ids = list(request.user.favorites.values_list('product_id', flat=True))
    else:
        favorite_ids = request.session.get('favorites', [])
        favorites = Product.objects.filter(id__in=favorite_ids)

    # Похожие товары (из категорий избранных товаров)
    similar_products = []
    if favorites:
        # Получаем категории избранных товаров
        favorite_categories = [product.category for product in favorites if product.category]
        similar_products = Product.objects.filter(
            category__in=favorite_categories,
            is_active=True
        ).exclude(id__in=favorite_ids).order_by('?')[:5]

    # Рекомендуемые товары (популярные, новинки, акционные)
    month_ago = timezone.now() - timedelta(days=30)
    recommended_products = Product.objects.filter(
        is_active=True
    ).exclude(id__in=favorite_ids).filter(
        Q(created_at__gte=month_ago) |  # Новинки
        Q(old_price__isnull=False)  # Акционные
    ).order_by('?')[:5]

    # Если рекомендованных мало, дополняем случайными товарами
    if recommended_products.count() < 5:
        additional_products = Product.objects.filter(
            is_active=True
        ).exclude(id__in=favorite_ids).exclude(
            id__in=recommended_products.values_list('id', flat=True)
        ).order_by('?')[:5 - recommended_products.count()]
        recommended_products = list(recommended_products) + list(additional_products)

    return render(request, 'favorites/list.html', {
        'favorites': favorites,
        'similar_products': similar_products,
        'recommended_products': recommended_products,
        'is_authenticated': request.user.is_authenticated
    })


@require_POST
def toggle_favorites(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    response_data = {'success': False}

    if request.user.is_authenticated:
        favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
        if not created:
            favorite.delete()
            response_data = {'success': True, 'action': 'removed', 'is_favorite': False}
        else:
            response_data = {'success': True, 'action': 'added', 'is_favorite': True}

        response_data['count'] = request.user.favorites.count()
    else:
        favorites = request.session.get('favorites', [])
        product_id_str = str(product_id)

        if product_id_str in favorites:
            favorites.remove(product_id_str)
            action = 'removed'
            is_favorite = False
        else:
            favorites.append(product_id_str)
            action = 'added'
            is_favorite = True

        request.session['favorites'] = favorites
        request.session.modified = True
        response_data = {
            'success': True,
            'action': action,
            'is_favorite': is_favorite,
            'count': len(favorites)
        }

    return JsonResponse(response_data)


def sync_favorites(request):
    """
    Синхронизация избранного при авторизации пользователя
    """
    if request.user.is_authenticated and 'favorites' in request.session:
        favorites_ids = request.session.get('favorites', [])
        for product_id in favorites_ids:
            product = get_object_or_404(Product, id=product_id)
            Favorite.objects.get_or_create(user=request.user, product=product)
        del request.session['favorites']
        return JsonResponse({'status': 'synced'})
    return JsonResponse({'status': 'no_sync_needed'})


def favorites_status(request):
    """
    Проверка наличия избранных товаров (для JS)
    """
    try:
        if request.user.is_authenticated:
            has_favorites = request.user.favorites.exists()
        else:
            has_favorites = bool(request.session.get('favorites', []))

        return JsonResponse({'has_favorites': has_favorites})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def get_favorite_ids(request):
    """
    Возвращает список ID товаров в избранном для текущего пользователя/сессии
    """
    if request.user.is_authenticated:
        favorite_ids = list(request.user.favorites.values_list('product_id', flat=True))
    else:
        favorite_ids = [int(id) for id in request.session.get('favorites', []) if id.isdigit()]

    return JsonResponse({'favorite_ids': favorite_ids})


def product_list(request):
    products = Product.objects.all()

    # Получаем избранное
    if request.user.is_authenticated:
        favorite_ids = list(request.user.favorites.values_list('product_id', flat=True))
    else:
        favorite_ids = [int(id) for id in request.session.get('favorites', []) if id.isdigit()]

    # Получаем корзину
    cart = get_cart(request)
    cart_product_ids = list(cart.items.values_list('product_id', flat=True))

    return render(request, 'shop/product_list.html', {
        'products': products,
        'favorite_ids': favorite_ids,
        'cart_product_ids': cart_product_ids  # Добавляем IDs товаров в корзине
    })


def favorite_count(request):
    if request.user.is_authenticated:
        count = Favorite.objects.filter(user=request.user).count()
    else:
        # Для неавторизованных пользователей можно использовать сессию
        favorites = request.session.get('favorites', [])
        count = len(favorites)

    return JsonResponse({'count': count})