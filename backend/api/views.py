from datetime import timedelta

from django.db.models import Q, F, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from shop.models import Product, Category, CarouselSlide
from cart.cart import Cart

from .serializers import (
    ProductCardSerializer,
    CategorySerializer,
    CarouselSlideSerializer,
)


def _qs_visible():
    """Базовый queryset публично видимых товаров (с фолбэком)."""
    try:
        return Product.objects.visible_to_public()
    except Exception:
        return Product.objects.filter(is_active=True)


def _ser_products(products, request):
    return ProductCardSerializer(products, many=True, context={'request': request}).data


@api_view(['GET'])
def home(request):
    """Данные для главной страницы (повторяет shop.views.index)."""
    base = _qs_visible()

    new_products = list(
        base.filter(
            Q(is_new=True) | Q(created_at__gte=timezone.now() - timedelta(days=14))
        ).select_related('category', 'manufacturer')[:12]
    )
    sale_products = list(
        base.filter(old_price__isnull=False, old_price__gt=F('price'))
        .select_related('category', 'manufacturer')[:12]
    )
    popular_products = list(
        base.annotate(order_count=Count('order_items'))
        .order_by('-views', '-order_count')[:12]
    )
    featured_products = list(
        base.filter(is_featured=True)
        .select_related('category', 'manufacturer')[:12]
    )
    month_ago = timezone.now() - timedelta(days=30)
    bestsellers = list(
        base.filter(order_items__order__created_at__gte=month_ago)
        .distinct().annotate(sales_count=Count('order_items'))
        .order_by('-sales_count')[:8]
    )

    if not new_products and not sale_products and not popular_products and not bestsellers:
        new_products = list(base.select_related('category', 'manufacturer')[:12])

    carousel = list(CarouselSlide.objects.filter(is_active=True).order_by('order', 'created_at'))

    return Response({
        'carousel_slides': CarouselSlideSerializer(carousel, many=True, context={'request': request}).data,
        'new_products': _ser_products(new_products, request),
        'sale_products': _ser_products(sale_products, request),
        'popular_products': _ser_products(popular_products, request),
        'featured_products': _ser_products(featured_products, request),
        'bestsellers': _ser_products(bestsellers, request),
    })


@api_view(['GET'])
def categories(request):
    """Список активных категорий."""
    qs = Category.objects.filter(is_active=True).order_by('order', 'name')
    parent = request.GET.get('parent')
    if parent == 'root':
        qs = qs.filter(parent__isnull=True)
    elif parent:
        qs = qs.filter(parent_id=parent)
    return Response(CategorySerializer(qs, many=True, context={'request': request}).data)


@api_view(['GET'])
def product_list(request):
    """Каталог товаров с фильтрами/поиском/сортировкой/пагинацией."""
    qs = _qs_visible().select_related('category', 'manufacturer')

    category_slug = request.GET.get('category')
    if category_slug:
        qs = qs.filter(Q(category__slug=category_slug) | Q(category__parent__slug=category_slug))

    search = request.GET.get('search') or request.GET.get('q')
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(part_number__icontains=search))

    ordering = request.GET.get('ordering')
    allowed = {'price', '-price', 'name', '-name', '-created_at', 'created_at'}
    if ordering in allowed:
        qs = qs.order_by(ordering)

    try:
        page = max(1, int(request.GET.get('page', 1)))
    except (TypeError, ValueError):
        page = 1
    page_size = 24
    total = qs.count()
    start = (page - 1) * page_size
    items = list(qs[start:start + page_size])

    return Response({
        'count': total,
        'page': page,
        'page_size': page_size,
        'num_pages': (total + page_size - 1) // page_size,
        'results': _ser_products(items, request),
    })


@api_view(['GET'])
def product_detail(request, slug):
    product = get_object_or_404(_qs_visible(), slug=slug)
    data = ProductCardSerializer(product, context={'request': request}).data
    data['description'] = getattr(product, 'description', '') or ''
    data['short_description'] = getattr(product, 'short_description', '') or ''
    return Response(data)


# --------------------------------------------------------------------------
# Корзина (сессионная, поверх cart.cart.Cart)
# --------------------------------------------------------------------------

def _cart_payload(cart, request):
    items = []
    for item in cart:
        product = item['product']
        items.append({
            'product': ProductCardSerializer(product, context={'request': request}).data,
            'quantity': item['quantity'],
            'price': item['price'],
            'total_price': item['total_price'],
        })
    return {
        'items': items,
        'total_price': cart.get_total_price(),
        'total_quantity': len(cart),
    }


@api_view(['GET'])
def cart_detail(request):
    return Response(_cart_payload(Cart(request), request))


@api_view(['POST'])
def cart_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    try:
        quantity = int(request.data.get('quantity', 1))
    except (TypeError, ValueError):
        quantity = 1
    update = bool(request.data.get('update', False))
    cart.add(product, quantity=quantity, update_quantity=update)
    return Response(_cart_payload(cart, request))


@api_view(['POST'])
def cart_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart = Cart(request)
    cart.remove(product)
    return Response(_cart_payload(cart, request))


@api_view(['POST'])
def cart_clear(request):
    cart = Cart(request)
    cart.clear()
    return Response(_cart_payload(cart, request))
