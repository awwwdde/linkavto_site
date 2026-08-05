from django.db.models import Prefetch
from django.conf import settings
from .models import (
    Category, CarBrand, TruckBrand, MotoBrand, SpecialBrand,
    CarBrandCategoryRelation, TruckBrandCategoryRelation,
    MotoBrandCategoryRelation, SpecialBrandCategoryRelation,
    AccessoryCategory, OilAndChemistryCategory, TireAndWheelCategory,
    ToolCategory, AutoElectricCategory, PartSubcategory,
    SiteSettings,
)
from favorites.models import Favorite



def social_providers(request):
    """
    Context processor для списка настроенных соц. провайдеров (только с заполненными credentials).
    Используется для показа кнопок входа через Яндекс, ВК, Telegram.
    """
    providers = []
    sp = getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
    if sp.get('yandex', {}).get('APP', {}).get('client_id'):
        providers.append(('yandex', 'Яндекс'))
    if sp.get('vk', {}).get('APP', {}).get('client_id'):
        providers.append(('vk', 'ВКонтакте'))
    if sp.get('telegram', {}).get('APP', {}).get('client_id'):
        providers.append(('telegram', 'Telegram'))
    return {'enabled_social_providers': providers}


def categories(request):
    # Получаем все корневые категории с предзагруженными данными
    try:
        categories = Category.objects.filter(
            parent__isnull=True,
            is_active=True
        ).prefetch_related(
        Prefetch(
            'car_brand_relations__brand',
            queryset=CarBrand.objects.filter(is_active=True),
            to_attr='prefetched_car_brands'
        ),
        Prefetch(
            'truck_brand_relations__brand',
            queryset=TruckBrand.objects.filter(is_active=True),
            to_attr='prefetched_truck_brands'
        ),
        Prefetch(
            'moto_brand_relations__brand',
            queryset=MotoBrand.objects.filter(is_active=True),
            to_attr='prefetched_moto_brands'
        ),
        Prefetch(
            'special_brand_relations__brand',
            queryset=SpecialBrand.objects.filter(is_active=True),
            to_attr='prefetched_special_brands'
        ),
        Prefetch(
            'children',
            queryset=Category.objects.filter(is_active=True).prefetch_related(
                Prefetch(
                    'children',
                    queryset=Category.objects.filter(is_active=True).order_by('order', 'name')
                )
            ).order_by('order', 'name')
        ),
        # Префетчим другие специализированные категории
        Prefetch(
            'oil_chemistry_subcategories',
            queryset=OilAndChemistryCategory.objects.filter(is_active=True),
            to_attr='_prefetched_oil_categories'
        ),
        Prefetch(
            'tire_wheel_subcategories',
            queryset=TireAndWheelCategory.objects.filter(is_active=True),
            to_attr='_prefetched_tire_categories'
        ),
        Prefetch(
            'tool_subcategories',
            queryset=ToolCategory.objects.filter(is_active=True),
            to_attr='_prefetched_tool_categories'
        ),
        Prefetch(
            'auto_electric_subcategories',
            queryset=AutoElectricCategory.objects.filter(is_active=True),
            to_attr='_prefetched_electric_categories'
        ),
        # Префетчим подкатегории запчастей
        Prefetch(
            'part_subcategories',
            queryset=PartSubcategory.objects.all(),
            to_attr='_prefetched_part_subcategories'
        )
    ).order_by('order')

        # Добавляем временные атрибуты с брендами и подкатегориями
        for category in categories:
            # Создаем временный атрибут brands (не brand_list)
            if category.show_brands:
                if category.show_in == 'cars':
                    category.brands = getattr(category, 'prefetched_car_brands', [])
                elif category.show_in == 'trucks':
                    category.brands = getattr(category, 'prefetched_truck_brands', [])
                elif category.show_in == 'moto':
                    category.brands = getattr(category, 'prefetched_moto_brands', [])
                elif category.show_in == 'special':
                    category.brands = getattr(category, 'prefetched_special_brands', [])
            else:
                category.brands = []

        # Добавляем подкатегории в зависимости от типа категории
        for category in categories:
            if category.show_in == 'accessories':
                category.subcategories = getattr(category, '_prefetched_accessory_categories', [])
            elif category.show_in == 'chemistry':
                category.subcategories = getattr(category, '_prefetched_oil_categories', [])
            elif category.show_in == 'tires':
                category.subcategories = getattr(category, '_prefetched_tire_categories', [])
            elif category.show_in == 'tools':
                category.subcategories = getattr(category, '_prefetched_tool_categories', [])
            elif category.show_in == 'electrics':
                category.subcategories = getattr(category, '_prefetched_electric_categories', [])
            else:
                category.subcategories = getattr(category, '_prefetched_part_subcategories', [])

        # Определяем текущую категорию (остальной код без изменений)
        current_category = None
        current_category_brands = []
        url_kwargs = getattr(request.resolver_match, 'kwargs', {})
        url_name = getattr(request.resolver_match, 'url_name', '')

        if 'slug' in url_kwargs:
            try:
                current_category = Category.objects.get(
                    slug=url_kwargs['slug'],
                    is_active=True
                )
            except Category.DoesNotExist:
                pass

        elif 'brand_slug' in url_kwargs:
            try:
                if url_name in ['car_models', 'brand_products']:
                    brand = CarBrand.objects.get(slug=url_kwargs['brand_slug'])
                    relation = brand.category_relations.filter(is_main=True).first()
                    if relation:
                        current_category = relation.category
            except Exception:
                pass

        if current_category and current_category.show_brands:
            if current_category.show_in == 'cars':
                current_category_brands = current_category.car_brands_list()
            elif current_category.show_in == 'trucks':
                current_category_brands = current_category.truck_brands_list()
            elif current_category.show_in == 'moto':
                current_category_brands = current_category.moto_brands_list()
            elif current_category.show_in == 'special':
                current_category_brands = current_category.special_brands_list()

        return {
            'categories': categories,
            'current_category': current_category,
            'current_category_brands': current_category_brands
        }
    except Exception as e:
        # В случае ошибки возвращаем пустые данные
        print(f"Error in categories context processor: {e}")
        return {
            'categories': [],
            'current_category': None,
            'current_category_brands': []
        }


def favorites_count(request):
    """
    Context processor для получения количества избранных товаров
    """
    try:
        if request.user.is_authenticated:
            favorites_count = Favorite.objects.filter(user=request.user).count()
        else:
            # Для неавторизованных пользователей используем сессию
            favorites = request.session.get('favorites', [])
            favorites_count = len(favorites)
        
        return {
            'favorites_count': favorites_count
        }
    except Exception as e:
        print(f"Error in favorites_count context processor: {e}")
        return {
            'favorites_count': 0
        }


def site_settings(request):
    try:
        return {'site_settings': SiteSettings.get()}
    except Exception:
        return {'site_settings': None}


def api_keys(request):
    """Прокидывает ключи внешних API в шаблоны."""
    return {
        'YANDEX_MAPS_API_KEY': getattr(settings, 'YANDEX_MAPS_API_KEY', ''),
        'DADATA_TOKEN': getattr(settings, 'DADATA_TOKEN', ''),
    }