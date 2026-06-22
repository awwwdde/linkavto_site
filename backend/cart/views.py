from django.shortcuts import render, redirect, get_object_or_404
from shop.models import Product
from .models import Cart
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from .models import CartItem
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST, require_GET
import json
from django.db import transaction


def get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        cart, created = Cart.objects.get_or_create(session_key=request.session.session_key)
        if created:
            request.session.create()
            cart.session_key = request.session.session_key
            cart.save()
    return cart


@require_POST
def cart_add(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        cart = get_cart(request)

        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            # Обычная обработка для не-AJAX запросов
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': 1}
            )
            if not created:
                cart_item.quantity += 1
                cart_item.save()
            return redirect('cart:cart_detail')

        # AJAX обработка
        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))
        override_quantity = data.get('override_quantity', False)

        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created and override_quantity:
            cart_item.quantity = quantity
            cart_item.save()

        return JsonResponse({
            'success': True,
            'new_quantity': cart_item.quantity,
            'item_total': cart_item.total_price(),
            'total_price': cart.total_price(),
            'total_quantity': cart.total_quantity()
        })

    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON data")
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e),
            'current_quantity': cart_item.quantity if 'cart_item' in locals() else 0
        }, status=400)


def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = get_cart(request)
    CartItem.objects.filter(cart=cart, product=product).delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('cart:cart_detail')


def cart_detail(request):
    from django.db.models import Q
    from django.utils import timezone
    from datetime import timedelta
    import json

    cart = get_cart(request)

    # Получаем ID товаров в корзине для исключения
    cart_product_ids = list(cart.items.values_list('product_id', flat=True)) if cart.items.exists() else []

    # Просмотренные товары (последние 5 просмотренных, исключая товары в корзине)
    viewed_products = []
    if request.session.get('viewed_products'):
        viewed_ids = request.session.get('viewed_products', [])[-10:]  # Берем последние 10
        viewed_products = Product.objects.filter(
            id__in=viewed_ids,
            is_active=True
        ).exclude(id__in=cart_product_ids).distinct()[:5]

    # Похожие товары (из категорий товаров в корзине)
    similar_products = []
    if cart.items.exists():
        # Получаем категории товаров в корзине
        cart_categories = cart.items.values_list('product__category', flat=True).distinct()
        similar_products = Product.objects.filter(
            category__in=cart_categories,
            is_active=True
        ).exclude(id__in=cart_product_ids).order_by('?')[:5]

    # Рекомендуемые товары (популярные, новинки, акционные)
    month_ago = timezone.now() - timedelta(days=30)
    recommended_products = Product.objects.filter(
        is_active=True
    ).exclude(id__in=cart_product_ids).filter(
        Q(created_at__gte=month_ago) |  # Новинки
        Q(old_price__isnull=False)  # Акционные
    ).order_by('?')[:5]  # Случайный порядок для разнообразия

    # Если рекомендованных мало, дополняем случайными товарами
    if recommended_products.count() < 5:
        additional_products = Product.objects.filter(
            is_active=True
        ).exclude(id__in=cart_product_ids).exclude(
            id__in=recommended_products.values_list('id', flat=True)
        ).order_by('?')[:5 - recommended_products.count()]
        recommended_products = list(recommended_products) + list(additional_products)

    context = {
        'cart': cart,
        'viewed_products': viewed_products,
        'similar_products': similar_products,
        'recommended_products': recommended_products,
    }

    return render(request, 'cart/cart.html', context)


@require_POST
def cart_decrease(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        cart = get_cart(request)

        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return HttpResponseBadRequest("This endpoint only accepts AJAX requests")

        data = json.loads(request.body)
        quantity = int(data.get('quantity', 1))

        cart_item = get_object_or_404(CartItem, cart=cart, product=product)
        cart_item.quantity = max(0, cart_item.quantity - quantity)

        response_data = {
            'success': True,
            'new_quantity': cart_item.quantity,
            'item_total': cart_item.total_price(),
            'cart_total': cart.total_price(),
            'total_items': cart.total_quantity()
        }

        if cart_item.quantity <= 0:
            cart_item.delete()
            response_data['new_quantity'] = 0
            response_data['item_total'] = 0
        else:
            cart_item.save()

        return JsonResponse(response_data)

    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON data")
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def cart_clear(request):
    cart = get_cart(request)
    cart.items.all().delete()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})

    return redirect('cart:cart_detail')


@require_POST
@transaction.atomic
def cart_update(request, product_id):
    try:
        # Проверяем и парсим данные
        try:
            data = json.loads(request.body)
            quantity = int(data.get('quantity', 1))
        except (json.JSONDecodeError, ValueError) as e:
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат данных'
            }, status=400)

        # Получаем объекты
        cart = get_cart(request)
        product = get_object_or_404(Product, id=product_id)

        # Проверка допустимого количества
        if quantity < 0:
            return JsonResponse({
                'success': False,
                'error': 'Количество не может быть отрицательным'
            }, status=400)

        # Работа с корзиной
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': quantity}
        )

        if not created:
            if quantity > 0:
                cart_item.quantity = quantity
                cart_item.save()
            else:
                cart_item.delete()

        # Формируем ответ
        response_data = {
            'success': True,
            'item_total': float(cart_item.total_price()) if quantity > 0 else 0,
            'new_quantity': quantity if quantity > 0 else 0,
            'total_quantity': cart.total_quantity,
            'total_price': float(cart.total_price)
        }

        return JsonResponse(response_data)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }, status=500)


@require_GET
def get_cart_items(request):
    cart = get_cart(request)
    items = CartItem.objects.filter(cart=cart).values('product_id')

    return JsonResponse({
        'success': True,
        'items': list(items)
    })


@require_GET
def cart_count(request):
    """Возвращает количество товаров в корзине"""
    cart = get_cart(request)
    return JsonResponse({
        'count': cart.total_quantity(),
        'success': True
    })
