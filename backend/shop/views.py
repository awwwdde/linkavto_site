import random
import string
from cart.models import Cart
from orders.models import Order, Payment
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404, HttpResponse
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from .models import Product, Review, ProductView, MaintenanceKit
from .forms import ReviewForm
from django.core.cache import cache
from django.db.models import Q, Count, F
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
import time
import hashlib
import requests
from django.conf import settings
from django.urls import reverse
from urllib.parse import urlencode
from django.views.decorators.http import require_GET

# Импорт моделей
from .models import (
    Category, Product, Manufacturer,
    CarBrand, CarModel, CarGeneration, CarType,
    TruckBrand, TruckModel, TruckGeneration, TruckType,
    MotoBrand, MotoModel, MotoGeneration, MotoType,
    SpecialBrand, SpecialModel, SpecialGeneration, SpecialType,
    AccessoryCategory, AccessoryBrand,
    ManufacturerCategoryRelation, Tag,
    CarBrandCategoryRelation, TruckBrandCategoryRelation,
    MotoBrandCategoryRelation, SpecialBrandCategoryRelation, OilAndChemistryBrand, MaintenanceBrand, TireAndWheelBrand,
    ToolBrand, AutoElectricBrand, OilAndChemistryCategory, MaintenanceCategory, TireAndWheelCategory, ToolCategory,
    AutoElectricCategory, PartSubcategory, MaintenanceKit, CarModification, TruckModification, MotoModification,
    SpecialModification, ProductBrand, ProductBrandCategoryRelation,
    CarouselSlide, SiteDocument,
)
from search.models import SearchQuery


# Для фильтров
def category_view(request, slug):
    # Получаем основную категорию
    category = get_object_or_404(
        Category.objects.prefetch_related('manufacturers'),
        slug=slug,
        is_active=True
    )

    # ---------------------------------------------------------------------
    # ВАЖНО (ТЗ):
    # - Родительская категория должна показывать товары из ВСЕХ вложенных подкатегорий (любая глубина)
    # - Фильтры Марка/Модель/Поколение/Модификация/Бренд(производитель) должны поддерживать множественный выбор
    #   (в URL приходят либо повторяющиеся параметры, либо CSV через запятую).
    # ---------------------------------------------------------------------

    def _get_multi_param(key: str) -> list[str]:
        """
        Поддерживает оба формата:
        - ?brand=a&brand=b
        - ?brand=a,b
        Возвращает уникальный список значений в порядке появления.
        """
        raw_list = request.GET.getlist(key) or []
        if not raw_list:
            raw = request.GET.get(key)
            raw_list = [raw] if raw else []

        out: list[str] = []
        for item in raw_list:
            if not item:
                continue
            for part in str(item).split(','):
                val = part.strip()
                if val and val not in out:
                    out.append(val)
        return out

    # Получаем все дочерние категории (любая глубина) за 1 запрос и строим дерево в памяти
    children_map: dict[int | None, list[int]] = {}
    for cid, pid in Category.objects.filter(is_active=True).values_list('id', 'parent_id'):
        children_map.setdefault(pid, []).append(cid)

    category_ids: list[int] = []
    stack: list[int] = [category.id]
    while stack:
        cid = stack.pop()
        category_ids.append(cid)
        stack.extend(children_map.get(cid, []))

    # Базовый queryset продуктов - включаем товары из всех вложенных подкатегорий (только одобренные)
    # а также товары, у которых эта категория указана как дополнительная
    products = Product.objects.visible_to_public().filter(
        Q(category_id__in=category_ids) | Q(extra_categories__in=category_ids)
    ).distinct().select_related(
        'manufacturer', 'category', 'part_subcategory'
    ).prefetch_related(
        'car_models', 'car_generations',
        'truck_models', 'truck_generations',
        'moto_models', 'moto_generations',
        'special_models', 'special_generations',
        'car_modifications', 'truck_modifications', 'moto_modifications', 'special_modifications',
        'tire_details__diameter',
        'tire_details__seasonality',
        'tire_details__profile_width',
        'tire_details__profile_height',
        'wheel_details__diameter',
        'wheel_details__width',
        'wheel_details__offset_type',
        'wheel_details__wheel_type',
        'wheel_details__pcd',
        'wheel_details__center_bore'
    )

    # --- GET параметры фильтрации ---
    brand_slugs = _get_multi_param('brand')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    in_stock = request.GET.get('in_stock')
    on_order = request.GET.get('on_order')
    is_original = request.GET.get('is_original')
    model_slugs = _get_multi_param('model')
    generation_slugs = _get_multi_param('generation')
    modification_slugs = _get_multi_param('modification')
    part_category_slug = request.GET.get('part_category')
    part_subcat_slug = request.GET.get('part_subcategory')
    part_subsubcategory_slug = request.GET.get('part_subsubcategory')
    manufacturer_slugs = _get_multi_param('manufacturer')
    product_brand_slugs = _get_multi_param('product_brand')
    car_type_slugs = _get_multi_param('car_type')
    moto_type_slugs = _get_multi_param('moto_type')
    truck_type_slugs = _get_multi_param('truck_type')
    special_type_slugs = _get_multi_param('special_type')
    sort = request.GET.get('sort')

    # --- НОВЫЕ ФИЛЬТРЫ ДЛЯ ШИН И ДИСКОВ ---
    tire_wheel_type = request.GET.get('tire_wheel_type')
    vehicle_type = request.GET.get('vehicle_type')
    tire_diameter = request.GET.get('tire_diameter')
    tire_seasonality = request.GET.get('tire_seasonality')
    tire_width = request.GET.get('tire_width')
    tire_height = request.GET.get('tire_height')
    tire_spikes = request.GET.get('tire_spikes')
    wheel_diameter = request.GET.get('wheel_diameter')
    wheel_width = request.GET.get('wheel_width')
    wheel_offset_type = request.GET.get('wheel_offset_type')
    wheel_type = request.GET.get('wheel_type')
    wheel_pcd = request.GET.get('wheel_pcd')

    # --- Обработка категории/подкатегории/подподкатегории запчастей ---
    subcategory = None
    if part_subsubcategory_slug:
        try:
            part_node = PartSubcategory.objects.get(
                slug=part_subsubcategory_slug,
                parent_category=category
            )
            subcategory = part_node
            products = products.filter(part_subcategory=part_node)
        except PartSubcategory.DoesNotExist:
            try:
                # Подподкатегория — потомок category на любой глубине
                candidate = Category.objects.get(
                    slug=part_subsubcategory_slug,
                    is_active=True
                )
                # Проверяем что candidate является потомком category
                cur = candidate.parent
                while cur is not None:
                    if cur.id == category.id:
                        subcategory = candidate
                        products = products.filter(category=candidate)
                        break
                    cur = cur.parent
            except Category.DoesNotExist:
                pass
    elif part_subcat_slug:
        try:
            part_node = PartSubcategory.objects.get(
                slug=part_subcat_slug,
                parent_category=category
            )
            subcategory = part_node
            ids = part_node.get_self_and_descendant_ids()
            products = products.filter(part_subcategory_id__in=ids)
        except PartSubcategory.DoesNotExist:
            try:
                subcategory = Category.objects.get(
                    slug=part_subcat_slug,
                    parent=category,
                    is_active=True
                )
                products = products.filter(category=subcategory)
            except Category.DoesNotExist:
                pass
    elif part_category_slug:
        try:
            part_node = PartSubcategory.objects.get(
                slug=part_category_slug,
                parent_category=category
            )
            subcategory = part_node
            ids = part_node.get_self_and_descendant_ids()
            products = products.filter(part_subcategory_id__in=ids)
        except PartSubcategory.DoesNotExist:
            pass

    # --- Фильтрация ---
    need_distinct = False

    if brand_slugs:
        brand_q = Q()
        for b in brand_slugs:
            brand_q |= (
                    Q(car_brand__slug=b) |
                    Q(car_models__brand__slug=b) |
                    Q(truck_brand__slug=b) |
                    Q(truck_models__brand__slug=b) |
                    Q(moto_brand__slug=b) |
                    Q(moto_models__brand__slug=b) |
                    Q(special_brand__slug=b) |
                    Q(special_models__brand__slug=b)
            )
        products = products.filter(brand_q)
        need_distinct = True

    if price_min:
        try:
            products = products.filter(price__gte=float(price_min))
        except (ValueError, TypeError):
            pass

    if price_max:
        try:
            products = products.filter(price__lte=float(price_max))
        except (ValueError, TypeError):
            pass

    if in_stock and not on_order:
        products = products.filter(stock__gt=0)
    elif on_order and not in_stock:
        products = products.filter(stock=0)

    if is_original:
        # Поддерживаем различные форматы: 'on', '1', 'true', 'yes' или просто наличие параметра
        if str(is_original).lower() not in ('false', '0', 'no', 'off', ''):
            products = products.filter(is_original=True)

    if model_slugs:
        if category.show_in == 'cars':
            products = products.filter(car_models__slug__in=model_slugs)
            need_distinct = True
        elif category.show_in == 'trucks':
            products = products.filter(truck_models__slug__in=model_slugs)
            need_distinct = True
        elif category.show_in == 'moto':
            products = products.filter(moto_models__slug__in=model_slugs)
            need_distinct = True
        elif category.show_in == 'special':
            products = products.filter(special_models__slug__in=model_slugs)
            need_distinct = True

    if generation_slugs:
        if category.show_in == 'cars':
            products = products.filter(car_generations__slug__in=generation_slugs)
            need_distinct = True
        elif category.show_in == 'trucks':
            products = products.filter(truck_generations__slug__in=generation_slugs)
            need_distinct = True
        elif category.show_in == 'moto':
            products = products.filter(moto_generations__slug__in=generation_slugs)
            need_distinct = True
        elif category.show_in == 'special':
            products = products.filter(special_generations__slug__in=generation_slugs)
            need_distinct = True

    if modification_slugs:
        if category.show_in == 'cars':
            products = products.filter(car_modifications__slug__in=modification_slugs)
            need_distinct = True
        elif category.show_in == 'trucks':
            products = products.filter(truck_modifications__slug__in=modification_slugs)
            need_distinct = True
        elif category.show_in == 'moto':
            products = products.filter(moto_modifications__slug__in=modification_slugs)
            need_distinct = True
        elif category.show_in == 'special':
            products = products.filter(special_modifications__slug__in=modification_slugs)
            need_distinct = True

    if manufacturer_slugs:
        products = products.filter(manufacturer__slug__in=manufacturer_slugs)

    if product_brand_slugs:
        products = products.filter(product_brand__slug__in=product_brand_slugs)

    # --- Фильтрация по типу кузова/техники (берется из типа модели) ---
    if car_type_slugs:
        products = products.filter(car_models__type__slug__in=car_type_slugs)
        need_distinct = True
    if moto_type_slugs:
        products = products.filter(moto_models__type__slug__in=moto_type_slugs)
        need_distinct = True
    if truck_type_slugs:
        products = products.filter(truck_models__type__slug__in=truck_type_slugs)
        need_distinct = True
    if special_type_slugs:
        products = products.filter(special_models__type__slug__in=special_type_slugs)
        need_distinct = True

    # --- НОВАЯ ФИЛЬТРАЦИЯ ДЛЯ ШИН И ДИСКОВ ---
    if tire_wheel_type:
        products = products.filter(tire_wheel_type=tire_wheel_type)

    if vehicle_type:
        products = products.filter(vehicle_type=vehicle_type)

    # Фильтрация по характеристикам шин
    if tire_diameter:
        products = products.filter(
            tire_details__diameter__value=tire_diameter
        )

    if tire_seasonality:
        products = products.filter(
            tire_details__seasonality__code=tire_seasonality
        )

    if tire_width:
        products = products.filter(
            tire_details__profile_width__value=tire_width
        )

    if tire_height:
        products = products.filter(
            tire_details__profile_height__value=tire_height
        )

    if tire_spikes:
        products = products.filter(
            tire_details__has_spikes=True
        )

    # Фильтрация по характеристикам дисков
    if wheel_diameter:
        products = products.filter(
            wheel_details__diameter__value=wheel_diameter
        )

    if wheel_width:
        products = products.filter(
            wheel_details__width__value=wheel_width
        )

    if wheel_offset_type:
        products = products.filter(
            wheel_details__offset_type__code=wheel_offset_type
        )

    if wheel_type:
        products = products.filter(
            wheel_details__wheel_type__code=wheel_type
        )

    if wheel_pcd:
        products = products.filter(
            wheel_details__pcd__value=wheel_pcd
        )

    if need_distinct:
        products = products.distinct()

    # --- Сортировка ---
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created_at')
    elif sort == 'popular':
        products = products.order_by('-views', '-created_at')
    else:
        products = products.order_by('-created_at')

    # --- Получаем списки для фильтров (категория → подкатегория → подподкатегория) ---
    part_categories = PartSubcategory.objects.filter(
        parent_category=category,
        parent__isnull=True
    ).annotate(
        product_count=Count('products', filter=Q(products__is_active=True))
    ).order_by('name')
    # Загружаем ВСЕ подкатегории (уровень 2 и 3) для клиентской фильтрации
    part_subcategories = PartSubcategory.objects.filter(
        parent_category=category,
        parent__isnull=False,
        parent__parent__isnull=True,
    ).select_related('parent').order_by('name')
    part_subsubcategories = PartSubcategory.objects.filter(
        parent_category=category,
        parent__isnull=False,
        parent__parent__isnull=False,
    ).select_related('parent').order_by('name')

    # Производители для фильтра:
    # раньше брали только привязанных к категории через ManufacturerCategoryRelation,
    # из-за чего "производители из админки" без привязки не появлялись.
    # Теперь показываем всех производителей, у которых есть активные товары в данной категории (включая вложенные).
    manufacturer_ids = (
        Product.objects
        .filter(is_active=True)
        .filter(Q(category_id__in=category_ids) | Q(extra_categories__in=category_ids))
        .exclude(manufacturer_id__isnull=True)
        .values_list('manufacturer_id', flat=True)
        .distinct()
    )
    manufacturers = Manufacturer.objects.filter(is_active=True, id__in=manufacturer_ids).order_by('name')

    # Бренды товаров для фильтра — показываем только те, у которых привязка к данной категории (или её предкам)
    # и есть активные товары в текущей выборке категорий.
    ancestor_and_self_ids = [c.id for c in category.get_ancestors(include_self=True)]
    product_brands = ProductBrand.objects.filter(
        is_active=True,
        category_relations__category_id__in=ancestor_and_self_ids,
        category_relations__is_active=True,
    ).distinct().order_by('name')

    # --- НОВЫЕ ДАННЫЕ ДЛЯ ФИЛЬТРОВ ШИН И ДИСКОВ ---
    tire_diameters = []
    tire_seasonalities = []
    tire_widths = []
    tire_heights = []
    wheel_diameters = []
    wheel_widths = []
    wheel_offset_types = []
    wheel_types = []
    wheel_pcds = []

    # Загружаем данные для фильтров только если это категория шин/дисков
    if category.slug in ['shiny-i-diski', 'diski', 'shiny']:
        from .models import (
            TireDiameter, TireSeasonality, TireProfileWidth, TireProfileHeight,
            WheelDiameter, WheelWidth, WheelOffsetType, WheelType, WheelPCD
        )

        tire_diameters = TireDiameter.objects.all().order_by('value')
        tire_seasonalities = TireSeasonality.objects.all().order_by('name')
        tire_widths = TireProfileWidth.objects.all().order_by('value')
        tire_heights = TireProfileHeight.objects.all().order_by('value')
        wheel_diameters = WheelDiameter.objects.all().order_by('value')
        wheel_widths = WheelWidth.objects.all().order_by('value')
        wheel_offset_types = WheelOffsetType.objects.all().order_by('name')
        wheel_types = WheelType.objects.all().order_by('name')
        wheel_pcds = WheelPCD.objects.all().order_by('value')

    # --- ДАННЫЕ ДЛЯ ФИЛЬТРОВ АВТОХИМИИ ---
    oil_types = []
    oil_viscosities = []
    oil_volumes = []
    oil_base_types = []
    oil_seasons = []

    if category.slug == 'avtohimiya-i-masla' or category.show_in == 'chemistry':
        from .models import OilAndChemistryDetails

        # Типы продуктов
        oil_types = OilAndChemistryDetails.OIL_TYPES

        # Вязкости (уникальные значения из базы)
        oil_viscosities = OilAndChemistryDetails.objects.filter(
            product__category=category,
            product__is_active=True,
            viscosity__isnull=False
        ).exclude(viscosity='').values_list('viscosity', flat=True).distinct().order_by('viscosity')

        # Объемы (уникальные значения из базы)
        oil_volumes = OilAndChemistryDetails.objects.filter(
            product__category=category,
            product__is_active=True,
            volume__isnull=False
        ).values_list('volume', flat=True).distinct().order_by('volume')

        # Основы масел
        oil_base_types = [
            ('mineral', 'Минеральное'),
            ('synthetic', 'Синтетическое'),
            ('semi_synthetic', 'Полусинтетическое'),
        ]

        # Сезонность
        oil_seasons = OilAndChemistryDetails.SEASONS

    # --- Логика для брендов, моделей и поколений ---
    brands = []
    models_qs = []
    gens_qs = []
    current_vehicle_type = None  # 'car'|'truck'|'moto'|'special'|None
    car_types = []
    truck_types = []
    moto_types = []
    special_types = []

    match category.show_in:
        case 'cars':
            current_vehicle_type = 'car'
            brands = CarBrand.objects.filter(is_active=True).order_by('name')
            models_qs = CarModel.objects.filter(is_active=True).select_related('brand').order_by('brand__name', 'name')
            gens_qs = CarGeneration.objects.filter(is_active=True).select_related('model').order_by('model__name', '-year_start')
            car_types = CarType.objects.filter(is_active=True).order_by('name')
        case 'trucks':
            current_vehicle_type = 'truck'
            brands = TruckBrand.objects.filter(is_active=True).order_by('name')
            models_qs = TruckModel.objects.filter(is_active=True).select_related('brand').order_by('brand__name', 'name')
            gens_qs = TruckGeneration.objects.filter(is_active=True).select_related('model').order_by('model__name', '-year_start')
            truck_types = TruckType.objects.filter(is_active=True).order_by('name')
        case 'moto':
            current_vehicle_type = 'moto'
            brands = MotoBrand.objects.filter(is_active=True).order_by('name')
            models_qs = MotoModel.objects.filter(is_active=True).select_related('brand').order_by('brand__name', 'name')
            gens_qs = MotoGeneration.objects.filter(is_active=True).select_related('model').order_by('model__name', '-year_start')
            moto_types = MotoType.objects.filter(is_active=True).order_by('name')
        case 'special':
            current_vehicle_type = 'special'
            brands = SpecialBrand.objects.filter(is_active=True).order_by('name')
            models_qs = SpecialModel.objects.filter(is_active=True).select_related('brand').order_by('brand__name', 'name')
            gens_qs = SpecialGeneration.objects.filter(is_active=True).select_related('model').order_by('model__name', '-year_start')
            special_types = SpecialType.objects.filter(is_active=True).order_by('name')
        case _:
            # Для шин, аксессуаров и прочих категорий — грузим бренды по выбранному типу ТС
            if vehicle_type == 'car':
                current_vehicle_type = 'car'
                brands = CarBrand.objects.filter(is_active=True).order_by('name')
                models_qs = CarModel.objects.filter(is_active=True).select_related('brand').order_by('brand__name', 'name')
                gens_qs = CarGeneration.objects.filter(is_active=True).select_related('model').order_by('model__name', '-year_start')
            elif vehicle_type == 'truck':
                current_vehicle_type = 'truck'
                brands = TruckBrand.objects.filter(is_active=True).order_by('name')
                models_qs = TruckModel.objects.filter(is_active=True).select_related('brand').order_by('brand__name', 'name')
                gens_qs = TruckGeneration.objects.filter(is_active=True).select_related('model').order_by('model__name', '-year_start')
            elif vehicle_type == 'moto':
                current_vehicle_type = 'moto'
                brands = MotoBrand.objects.filter(is_active=True).order_by('name')
                models_qs = MotoModel.objects.filter(is_active=True).select_related('brand').order_by('brand__name', 'name')
                gens_qs = MotoGeneration.objects.filter(is_active=True).select_related('model').order_by('model__name', '-year_start')
            elif vehicle_type == 'special':
                current_vehicle_type = 'special'
                brands = SpecialBrand.objects.filter(is_active=True).order_by('name')
                models_qs = SpecialModel.objects.filter(is_active=True).select_related('brand').order_by('brand__name', 'name')
                gens_qs = SpecialGeneration.objects.filter(is_active=True).select_related('model').order_by('model__name', '-year_start')
            else:
                # По умолчанию (vehicle_type не выбран) показываем марки легковых авто
                current_vehicle_type = 'car'
                brands = CarBrand.objects.filter(is_active=True).order_by('name')
                models_qs = CarModel.objects.filter(is_active=True).select_related('brand').order_by('brand__name', 'name')
                gens_qs = CarGeneration.objects.filter(is_active=True).select_related('model').order_by('model__name', '-year_start')

    # Получаем подразделы для текущей категории используя тот же механизм, что и в мега-меню
    if category.show_in == 'accessories':
        subcategories = AccessoryCategory.objects.filter(
            main_category=category,
            is_active=True
        ).order_by('name')
    elif category.show_in == 'chemistry':
        # ИСПРАВЛЕНИЕ: для автохимии берем все активные категории
        subcategories = OilAndChemistryCategory.objects.filter(
            is_active=True
        ).order_by('name')
    elif category.show_in == 'tires':
        subcategories = TireAndWheelCategory.objects.filter(
            categories=category,
            is_active=True
        ).order_by('name')
    elif category.show_in == 'tools':
        subcategories = ToolCategory.objects.filter(
            categories=category,
            is_active=True
        ).order_by('name')
    elif category.show_in == 'electrics':
        subcategories = AutoElectricCategory.objects.filter(
            categories=category,
            is_active=True
        ).order_by('name')
    else:
        # Для обычных категорий используем дочерние категории (как в мега-меню)
        # В БД иногда встречаются дубли по name среди дочерних категорий (например "Двигатель" 2 раза).
        # Для UI (селект подкатегорий) показываем только одну запись на имя.
        # Выбираем "лучшую" категорию по количеству активных товаров (чтобы не оставить пустую).
        raw_subcategories = list(category.children.filter(is_active=True).order_by('name'))
        if raw_subcategories:
            ids = [c.id for c in raw_subcategories]
            counts_qs = (
                Product.objects
                .filter(is_active=True, category_id__in=ids)
                .values('category_id')
                .annotate(cnt=Count('id'))
            )
            counts_by_id = {row['category_id']: row['cnt'] for row in counts_qs}

            best_by_name: dict[str, Category] = {}
            best_count_by_name: dict[str, int] = {}
            for c in raw_subcategories:
                key = (c.name or '').strip().lower()
                cnt = counts_by_id.get(c.id, 0)
                prev = best_by_name.get(key)
                prev_cnt = best_count_by_name.get(key, -1)
                if prev is None or cnt > prev_cnt or (cnt == prev_cnt and c.id < prev.id):
                    best_by_name[key] = c
                    best_count_by_name[key] = cnt

            # Стабильная сортировка по отображаемому имени
            subcategories = sorted(best_by_name.values(), key=lambda x: (x.name or '').lower())
        else:
            subcategories = []

    # Подподкатегории для ветки Category — загружаем ВСЕ для клиентской фильтрации
    sub_subcategories = []
    if subcategories:
        parent_ids = [s.id for s in subcategories if hasattr(s, 'id')]
        if parent_ids:
            sub_subcategories = list(
                Category.objects.filter(
                    parent_id__in=parent_ids,
                    is_active=True
                ).select_related('parent').order_by('name')
            )

    # --- Хлебные крошки: Главная / тип ТС / категория / подкатегория ---
    breadcrumb_l2 = None  # (name, query_string) для уровня «категория»
    breadcrumb_l3 = None  # (name,) для уровня «подкатегория» (активный)
    if part_subsubcategory_slug and subcategory:
        if hasattr(subcategory, 'parent_category'):  # PartSubcategory
            part_cat = getattr(subcategory.parent, 'parent', None) or subcategory.parent
            if part_cat:
                breadcrumb_l2 = (part_cat.name, urlencode({'part_category': part_cat.slug}))
            breadcrumb_l3 = (subcategory.name,)
        else:  # Category (внук)
            breadcrumb_l2 = (subcategory.parent.name, urlencode({'part_subcategory': subcategory.parent.slug}))
            breadcrumb_l3 = (subcategory.name,)
    elif part_subcat_slug and subcategory:
        if hasattr(subcategory, 'parent_category'):  # PartSubcategory
            if subcategory.parent:
                breadcrumb_l2 = (subcategory.parent.name, urlencode({'part_category': subcategory.parent.slug}))
            breadcrumb_l3 = (subcategory.name,)
        else:  # Category (ребёнок)
            breadcrumb_l2 = (subcategory.name, urlencode({'part_subcategory': part_subcat_slug}))
    elif part_category_slug:
        try:
            part_cat = PartSubcategory.objects.get(
                slug=part_category_slug,
                parent_category=category,
                parent__isnull=True
            )
            breadcrumb_l2 = (part_cat.name, urlencode({'part_category': part_category_slug}))
        except PartSubcategory.DoesNotExist:
            pass

    # Список модификаций — загружаем все для текущего типа ТС (фильтрация на стороне клиента)
    if current_vehicle_type == 'car':
        modifications_qs = CarModification.objects.select_related('generation').order_by('generation__name', 'name')
    elif current_vehicle_type == 'truck':
        modifications_qs = TruckModification.objects.select_related('generation').order_by('generation__name', 'name')
    elif current_vehicle_type == 'moto':
        modifications_qs = MotoModification.objects.select_related('generation').order_by('generation__name', 'name')
    elif current_vehicle_type == 'special':
        modifications_qs = SpecialModification.objects.select_related('generation').order_by('generation__name', 'name')
    else:
        modifications_qs = []

    # --- Пагинация (ПОСЛЕ всех фильтров и сортировки) ---
    paginator = Paginator(products, 24)  # 24 товара на страницу
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        "category": category,
        "products": page_obj,
        "page_obj": page_obj,
        "is_paginated": paginator.num_pages > 1,
        "total_products": products.count(),  # Общее количество товаров
        "brands": brands,
        "models": models_qs,
        "generations": gens_qs,
        "current_vehicle_type": current_vehicle_type,
        "car_types": car_types,
        "truck_types": truck_types,
        "moto_types": moto_types,
        "special_types": special_types,
        "part_categories": part_categories,
        "part_subcategories": part_subcategories,
        "part_subsubcategories": part_subsubcategories,
        "part_category_slug": part_category_slug,
        "part_subsubcategory_slug": part_subsubcategory_slug,
        "manufacturers": manufacturers,
        "product_brands": product_brands,
        "selected_brand": request.GET.get('brand'),
        "selected_brand_slugs": brand_slugs,
        "selected_model_slugs": model_slugs,
        "selected_generation_slugs": generation_slugs,
        "selected_modification_slugs": modification_slugs,
        "selected_manufacturer_slugs": manufacturer_slugs,
        "selected_product_brand_slugs": product_brand_slugs,
        "subcategory": subcategory,  # Информация о подкатегории
        "subcategories": subcategories,  # Подразделы для отображения
        "sub_subcategories": sub_subcategories,  # Внуки категории (для ветки Category)
        "breadcrumb_l2": breadcrumb_l2,  # (name, query_string) для уровня «категория»
        "breadcrumb_l3": breadcrumb_l3,  # (name,) для уровня «подкатегория»
        "modifications": modifications_qs,

        # --- НОВЫЕ ДАННЫЕ ДЛЯ ФИЛЬТРОВ ШИН И ДИСКОВ ---
        "tire_diameters": tire_diameters,
        "tire_seasonalities": tire_seasonalities,
        "tire_widths": tire_widths,
        "tire_heights": tire_heights,
        "wheel_diameters": wheel_diameters,
        "wheel_widths": wheel_widths,
        "wheel_offset_types": wheel_offset_types,
        "wheel_types": wheel_types,
        "wheel_pcds": wheel_pcds,

        # Данные для фильтров автохимии
        "oil_types": oil_types,
        "oil_viscosities": oil_viscosities,
        "oil_volumes": oil_volumes,
        "oil_base_types": oil_base_types,
        "oil_seasons": oil_seasons,
    }

    # Обработка AJAX запросов для сортировки
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        from django.template.loader import render_to_string
        from django.http import JsonResponse

        # Отладочная информация
        print(
            f"AJAX request received. Sort: {request.GET.get('sort')}, Part subcategory: {request.GET.get('part_subcategory')}")

        # Получаем данные о состоянии избранного и корзины для пользователя
        favorite_ids = []
        cart_product_ids = []

        if request.user.is_authenticated:
            # Получаем избранные товары
            from favorites.models import Favorite
            favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('product_id', flat=True))

            # Получаем товары в корзине
            from cart.models import Cart, CartItem
            try:
                cart = Cart.objects.get(user=request.user)
                cart_product_ids = list(CartItem.objects.filter(cart=cart).values_list('product_id', flat=True))
            except Cart.DoesNotExist:
                cart_product_ids = []

        # Рендерим только блок с товарами
        products_html = render_to_string('shop/partials/products_grid.html', {
            'products': page_obj,
            'is_paginated': paginator.num_pages > 1,
            'page_obj': page_obj,
            'request': request,  # Добавляем request для доступа к GET параметрам
            'favorite_ids': favorite_ids,  # Добавляем данные об избранном
            'cart_product_ids': cart_product_ids,  # Добавляем данные о корзине
        })

        # Рендерим список моделей для десктопного выпадающего фильтра (обновляется без перезагрузки)
        desktop_models_dropdown_options_html = render_to_string(
            'shop/partials/desktop_models_dropdown_options.html',
            {
                'models': models_qs,
                'request': request,
            }
        )

        # Поколения (зависят от выбранных моделей)
        desktop_generations_dropdown_options_html = render_to_string(
            'shop/partials/desktop_generations_dropdown_options.html',
            {
                'generations': gens_qs,
                'request': request,
            }
        )

        # Модификации (зависят от выбранных поколений)
        desktop_modifications_dropdown_options_html = render_to_string(
            'shop/partials/desktop_modifications_dropdown_options.html',
            {
                'modifications': modifications_qs,
                'request': request,
            }
        )

        # Типы кузова (для легковых) — можно сузить под выбранные бренды/модели
        car_types_for_filter = car_types
        if current_vehicle_type == 'car' and models_qs:
            # Фильтруем типы кузова только по выбранным моделям
            # Это гарантирует, что показываются только типы кузова для выбранных моделей
            car_types_for_filter = (
                CarType.objects.filter(is_active=True, carmodel__in=models_qs)
                .distinct()
                .order_by('name')
            )
        desktop_car_types_dropdown_options_html = render_to_string(
            'shop/partials/desktop_car_types_dropdown_options.html',
            {
                'car_types': car_types_for_filter,
                'request': request,
            }
        )

        # --- Мобильные модалки: обновляем списки без перезагрузки ---
        mobile_models_modal_list_html = render_to_string(
            'shop/partials/mobile_models_modal_list.html',
            {'models': models_qs, 'request': request}
        )
        mobile_generations_modal_list_html = render_to_string(
            'shop/partials/mobile_generations_modal_list.html',
            {'generations': gens_qs, 'request': request}
        )
        mobile_modifications_modal_list_html = render_to_string(
            'shop/partials/mobile_modifications_modal_list.html',
            {'modifications': modifications_qs, 'request': request}
        )

        # Типы кузова/техники для мобильных модалок (можно сузить под выбранные бренды/модели)
        moto_types_for_filter = moto_types
        truck_types_for_filter = truck_types
        special_types_for_filter = special_types
        if current_vehicle_type == 'moto' and (brand_slugs or model_slugs):
            moto_types_for_filter = (
                MotoType.objects.filter(is_active=True, motomodel__in=models_qs)
                .distinct()
                .order_by('name')
            )
        if current_vehicle_type == 'truck' and (brand_slugs or model_slugs):
            truck_types_for_filter = (
                TruckType.objects.filter(is_active=True, truckmodel__in=models_qs)
                .distinct()
                .order_by('name')
            )
        if current_vehicle_type == 'special' and (brand_slugs or model_slugs):
            special_types_for_filter = (
                SpecialType.objects.filter(is_active=True, specialmodel__in=models_qs)
                .distinct()
                .order_by('name')
            )

        mobile_car_types_modal_list_html = render_to_string(
            'shop/partials/mobile_car_types_modal_list.html',
            {'car_types': car_types_for_filter, 'request': request}
        )
        mobile_moto_types_modal_list_html = render_to_string(
            'shop/partials/mobile_moto_types_modal_list.html',
            {'moto_types': moto_types_for_filter, 'request': request}
        )
        mobile_truck_types_modal_list_html = render_to_string(
            'shop/partials/mobile_truck_types_modal_list.html',
            {'truck_types': truck_types_for_filter, 'request': request}
        )
        mobile_special_types_modal_list_html = render_to_string(
            'shop/partials/mobile_special_types_modal_list.html',
            {'special_types': special_types_for_filter, 'request': request}
        )

        return JsonResponse({
            'success': True,
            'products_html': products_html,
            'desktop_models_dropdown_options_html': desktop_models_dropdown_options_html,
            'desktop_generations_dropdown_options_html': desktop_generations_dropdown_options_html,
            'desktop_modifications_dropdown_options_html': desktop_modifications_dropdown_options_html,
            'desktop_car_types_dropdown_options_html': desktop_car_types_dropdown_options_html,
            'mobile_models_modal_list_html': mobile_models_modal_list_html,
            'mobile_generations_modal_list_html': mobile_generations_modal_list_html,
            'mobile_modifications_modal_list_html': mobile_modifications_modal_list_html,
            'mobile_car_types_modal_list_html': mobile_car_types_modal_list_html,
            'mobile_moto_types_modal_list_html': mobile_moto_types_modal_list_html,
            'mobile_truck_types_modal_list_html': mobile_truck_types_modal_list_html,
            'mobile_special_types_modal_list_html': mobile_special_types_modal_list_html,
            'total_products': paginator.count,
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'favorite_ids': favorite_ids,  # Передаем данные об избранном
            'cart_product_ids': cart_product_ids,  # Передаем данные о корзине
        })

    return render(request, "shop/category.html", context)


def product_detail(request, slug):
    """
    Детальная страница товара с изображениями и атрибутами.
    """
    import json
    from favorites.models import Favorite
    from cart.models import Cart
    from django.db.models import Q, Count, Avg
    from django.utils import timezone
    from datetime import timedelta

    product = get_object_or_404(
        Product.objects.visible_to_public().select_related('seller', 'seller__review_summary'),
        slug=slug
    )

    # Получаем ID товаров в избранном
    if request.user.is_authenticated:
        favorite_ids = list(Favorite.objects.filter(user=request.user).values_list('product_id', flat=True))
        is_favorite = product.id in favorite_ids
    else:
        favorite_ids = []
        is_favorite = False

    # Получаем ID товаров в корзине
    cart_product_ids = []
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).first()
        if cart:
            cart_product_ids = list(cart.items.values_list('product_id', flat=True))
    else:
        session_cart = request.session.get('cart', {})
        cart_product_ids = []
        for pid in session_cart.keys():
            try:
                cart_product_ids.append(int(pid))
            except (ValueError, TypeError):
                continue

    is_in_cart = product.id in cart_product_ids

    # Похожие товары (из той же категории, исключая текущий)
    similar_products = Product.objects.visible_to_public().filter(
        category=product.category
    ).exclude(id=product.id)

    # Уточняем похожие товары по дополнительным критериям
    if product.manufacturer:
        similar_products = similar_products.filter(
            Q(manufacturer=product.manufacturer) |
            Q(part_number__icontains=product.part_number[:5]) |  # Частичное совпадение артикула
            Q(name__icontains=product.name.split()[0])  # Первое слово из названия
        ).distinct()

    # Если похожих товаров мало, дополняем товарами из категории
    if similar_products.count() < 4:
        additional_similar = Product.objects.visible_to_public().filter(
            category=product.category
        ).exclude(id=product.id).exclude(id__in=similar_products.values_list('id', flat=True))
        similar_products = list(similar_products) + list(additional_similar[:8 - len(similar_products)])

    # Рекомендуемые товары (популярные, с высоким рейтингом, новинки)
    month_ago = timezone.now() - timedelta(days=30)

    # Используем Count для подсчета отзывов вместо свойства review_count
    recommended_products = Product.objects.visible_to_public().exclude(id=product.id).annotate(
        avg_rating=Avg('reviews__rating'),
        reviews_count=Count('reviews')  # Переименовываем чтобы не конфликтовать со свойством
    ).filter(
        Q(avg_rating__gte=4.0, reviews_count__gte=3) |  # Высокий рейтинг
        Q(created_at__gte=month_ago) |  # Новинки
        Q(old_price__isnull=False)  # Акционные
    ).order_by('-avg_rating', '-views', '-created_at').distinct()[:8]

    # Если рекомендуемых товаров мало, дополняем случайными популярными
    if recommended_products.count() < 4:
        additional_recommended = Product.objects.visible_to_public().exclude(id=product.id).exclude(id__in=recommended_products.values_list('id', flat=True))
        additional_recommended = additional_recommended.order_by('?')[:8 - len(recommended_products)]
        recommended_products = list(recommended_products) + list(additional_recommended)

    # Сохраняем ID просмотренного товара в сессии
    if 'viewed_products' not in request.session:
        request.session['viewed_products'] = []

    viewed_products = request.session['viewed_products']

    # Удаляем текущий товар если он уже есть в списке
    if product.id in viewed_products:
        viewed_products.remove(product.id)

    # Добавляем текущий товар в начало
    viewed_products.append(product.id)

    # Ограничиваем список 20 товарами
    if len(viewed_products) > 20:
        viewed_products = viewed_products[-20:]

    request.session['viewed_products'] = viewed_products
    request.session.modified = True

    # Получаем информацию о голосах пользователя за полезность отзывов
    user_review_votes = {}
    if request.user.is_authenticated:
        from shop.models import ReviewFeedback
        review_ids = list(product.reviews.filter(is_published=True).values_list('id', flat=True))
        if review_ids:
            votes = ReviewFeedback.objects.filter(
                review_id__in=review_ids,
                user=request.user
            ).values('review_id', 'helpful')
            # Преобразуем ключи в int для надежности
            user_review_votes = {int(vote['review_id']): bool(vote['helpful']) for vote in votes}

    # Проверяем, может ли пользователь оставить отзыв
    can_review = False
    if request.user.is_authenticated:
        can_review = product.user_has_purchased(request.user)

    context = {
        'product': product,
        'favorite_ids': json.dumps(favorite_ids),
        'cart_product_ids': json.dumps(cart_product_ids),
        'is_favorite': is_favorite,
        'is_in_cart': is_in_cart,
        'similar_products': similar_products[:8],
        'recommended_products': recommended_products[:8],
        'user_review_votes': user_review_votes,
        'can_review': can_review,
    }

    return render(request, 'shop/product_detail.html', context)


def search_view(request):
    """
    Поиск товаров по названию, артикулу, VIN и описанию.
    Использует нечеткий поиск и нормализацию VIN.
    """
    from search.services import SearchService

    query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)
    sort = request.GET.get('sort', '')

    filters = {
        'category': request.GET.get('category'),
        'brand': request.GET.get('brand'),
        'price_min': request.GET.get('price_min'),
        'price_max': request.GET.get('price_max'),
        'in_stock': request.GET.get('in_stock') == 'on',
        'on_order': request.GET.get('on_order') == 'on',
        'rating': request.GET.get('rating'),
        'sort': sort,
        'is_vin_search': False,
        'is_plate_search': False,
    }

    history_queries = SearchQuery.get_user_history(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key
    )

    ctx = {
        'query': query,
        'filters': filters,
        'sort': sort,
        'is_vin_search': False,
        'is_plate_search': False,
        'search_type': 'text',
        'history_queries': history_queries,
    }

    if not query:
        return render(request, 'shop/search.html', ctx)

    # Нормализуем запрос для VIN (убираем пробелы и дефисы)
    search_type = SearchService.detect_search_type(query)

    # Определяем VIN-поиск
    is_vin_search = search_type == 'vin'
    is_plate_search = search_type == 'license_plate'
    filters['is_vin_search'] = is_vin_search
    filters['is_plate_search'] = is_plate_search
    ctx['is_vin_search'] = is_vin_search
    ctx['is_plate_search'] = is_plate_search
    ctx['search_type'] = search_type

    # Используем нормализованный query для VIN поиска
    service_filters = filters.copy()
    service_filters['search_type'] = search_type
    service_filters['user'] = request.user

    # Поиск
    results = SearchService.search_products(query, service_filters)

    # Сортировка
    if sort == 'price_asc':
        results = results.order_by('price')
    elif sort == 'price_desc':
        results = results.order_by('-price')
    elif sort == 'new':
        results = results.order_by('-created_at')
    elif sort == 'popular':
        results = results.order_by('-views')

    paginator = Paginator(results, 20)
    ctx['results'] = paginator.get_page(page_number)

    return render(request, 'shop/search.html', ctx)


def car_brands(request):
    """
    Список брендов легковых автомобилей.
    """
    brands = CarBrand.objects.filter(
        is_active=True
    ).order_by('name')

    return render(request, 'shop/car_brands.html', {
        'brands': brands
    })


def car_models(request, brand_slug):
    """
    Список моделей для конкретного бренда легковых авто.
    """
    brand = get_object_or_404(CarBrand, slug=brand_slug)
    models = CarModel.objects.filter(
        brand=brand,
        is_active=True
    ).select_related('type').order_by('name')

    return render(request, 'shop/car_models.html', {
        'brand': brand,
        'models': models
    })


def brand_products(request, brand_slug):
    """Товары для конкретного бренда с поддержкой фильтрации."""

    brand = None
    brand_type = None
    category = None

    brand_models = {
        'car': (CarBrand, 'car_brand'),
        'truck': (TruckBrand, 'truck_brand'),
        'moto': (MotoBrand, 'moto_brand'),
        'special': (SpecialBrand, 'special_brand')
    }

    for model, field in brand_models.values():
        try:
            brand = model.objects.get(slug=brand_slug)
            brand_type = field
            break
        except model.DoesNotExist:
            continue

    if not brand:
        raise Http404("Бренд не найден")

    # Определяем основную категорию бренда
    if hasattr(brand, 'category_relations'):
        category_rel = brand.category_relations.filter(is_active=True).first()
        if category_rel:
            category = category_rel.category

    # Фильтры из GET-параметров
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    is_original = request.GET.get('is_original')
    model_slug = request.GET.get('model')
    generation_slug = request.GET.get('generation')
    part_cat_slug = request.GET.get('part_category')
    manufacturer_slug = request.GET.get('manufacturer')
    in_stock = request.GET.get('in_stock')
    on_order = request.GET.get('on_order')
    sort = request.GET.get('sort')

    # Получаем товары (только одобренные для публичного каталога)
    products = Product.objects.visible_to_public().filter(**{brand_type: brand}).select_related('category',
                                                                                            'manufacturer').prefetch_related(
        'car_models', 'car_generations',
        'truck_models', 'truck_generations',
        'moto_models', 'moto_generations',
        'special_models', 'special_generations'
    )

    if price_min:
        products = products.filter(price__gte=price_min)
    if price_max:
        products = products.filter(price__lte=price_max)
    if is_original:
        # Поддерживаем различные форматы: 'on', '1', 'true', 'yes' или просто наличие параметра
        if str(is_original).lower() not in ('false', '0', 'no', 'off', ''):
            products = products.filter(is_original=True)
    if in_stock and not on_order:
        products = products.filter(stock__gt=0)
    elif on_order and not in_stock:
        products = products.filter(stock=0)
    if manufacturer_slug:
        products = products.filter(manufacturer__slug=manufacturer_slug)
    if part_cat_slug:
        products = products.filter(part_subcategory__slug=part_cat_slug)

    # Фильтр: модель и поколение
    if model_slug:
        if brand_type == 'car_brand':
            products = products.filter(car_models__slug=model_slug)
        elif brand_type == 'truck_brand':
            products = products.filter(truck_models__slug=model_slug)
        elif brand_type == 'moto_brand':
            products = products.filter(moto_models__slug=model_slug)
        elif brand_type == 'special_brand':
            products = products.filter(special_models__slug=model_slug)

    if generation_slug:
        if brand_type == 'car_brand':
            products = products.filter(car_generations__slug=generation_slug)
        elif brand_type == 'truck_brand':
            products = products.filter(truck_generations__slug=generation_slug)
        elif brand_type == 'moto_brand':
            products = products.filter(moto_generations__slug=generation_slug)
        elif brand_type == 'special_brand':
            products = products.filter(special_generations__slug=generation_slug)

    # Сортировка
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'new':
        products = products.order_by('-created_at')

    # Подготовка списков для селектов
    match brand_type:
        case 'car_brand':
            models_qs = CarModel.objects.filter(brand=brand)
            generations = CarGeneration.objects.filter(
                model__slug=model_slug) if model_slug else CarGeneration.objects.none()
        case 'truck_brand':
            models_qs = TruckModel.objects.filter(brand=brand)
            generations = TruckGeneration.objects.filter(
                model__slug=model_slug) if model_slug else TruckGeneration.objects.none()
        case 'moto_brand':
            models_qs = MotoModel.objects.filter(brand=brand)
            generations = MotoGeneration.objects.filter(
                model__slug=model_slug) if model_slug else MotoGeneration.objects.none()
        case 'special_brand':
            models_qs = SpecialModel.objects.filter(brand=brand)
            generations = SpecialGeneration.objects.filter(
                model__slug=model_slug) if model_slug else SpecialGeneration.objects.none()
        case _:
            models_qs = []
            generations = []

    part_categories = PartSubcategory.objects.filter(parent_category=category).order_by('name') if category else []
    manufacturers = category.manufacturers.all().order_by('name') if category and hasattr(category,
                                                                                          'manufacturers') else []

    return render(request, 'shop/brand_products.html', {
        'brand': brand,
        'products': products,
        'brand_type': brand_type.split('_')[0],
        'models': models_qs,
        'generations': generations,
        'part_categories': part_categories,
        'manufacturers': manufacturers,
        'sort': sort,
    })


def brand_category_products(request, brand_slug, category_slug):
    """
    Товары бренда в конкретной категории.
    """
    # Определяем тип бренда и соответствие с полями модели Product
    brand = None
    brand_type = None
    relation_model = None

    # Маппинг: модель бренда -> название поля в Product
    brand_mapping = [
        (CarBrand, 'car_brand', CarBrandCategoryRelation),
        (TruckBrand, 'truck_brand', TruckBrandCategoryRelation),
        (MotoBrand, 'moto_brand', MotoBrandCategoryRelation),
        (SpecialBrand, 'special_brand', SpecialBrandCategoryRelation)
    ]

    for model, field_name, relation in brand_mapping:
        try:
            brand = model.objects.get(slug=brand_slug)
            brand_type = field_name
            relation_model = relation
            break
        except model.DoesNotExist:
            continue

    if not brand or not brand_type:
        raise Http404("Бренд не найден")

    # Находим связь бренда с категорией
    brand_category = get_object_or_404(
        relation_model.objects.select_related('category'),
        brand=brand,
        category__slug=category_slug
    )

    # Получаем товары, используя динамическое имя поля (только одобренные)
    filter_kwargs = {brand_type: brand}
    products = Product.objects.visible_to_public().filter(
        category=brand_category.category,
        **filter_kwargs
    ).select_related('manufacturer')

    return render(request, 'shop/brand_category.html', {
        'brand': brand,
        'brand_category': brand_category,
        'products': products
    })


def cars_main(request):
    """
    Главная страница раздела легковых автомобилей.
    Группирует бренды по буквам и показывает категории.
    """
    brands = CarBrand.objects.filter(is_active=True).order_by('name')
    brand_groups = {}

    for brand in brands:
        first_letter = brand.name[0].upper()
        if first_letter not in brand_groups:
            brand_groups[first_letter] = []
        brand_groups[first_letter].append(brand)

    # Основные категории для легковых авто
    categories = Category.objects.filter(
        show_in='cars',
        is_active=True,
        parent__isnull=True
    ).order_by('order')

    return render(request, 'shop/cars_main.html', {
        'brand_groups': brand_groups,
        'categories': categories
    })


def all_brands_category(request, category_slug):
    """
    Товары всех брендов в конкретной категории.
    """
    category = get_object_or_404(Category, slug=category_slug)

    products = Product.objects.visible_to_public().filter(
        category=category
    ).select_related('manufacturer', 'car_brand')

    return render(request, 'shop/all_brands_category.html', {
        'category': category,
        'products': products
    })


def brand_models(request, brand_slug):
    """
    Список моделей для бренда (универсальный для всех типов транспорта).
    """
    brand = None

    # Проверяем все возможные типы брендов
    for model in [CarBrand, TruckBrand, MotoBrand, SpecialBrand]:
        try:
            brand = model.objects.prefetch_related('models').get(slug=brand_slug)
            break
        except model.DoesNotExist:
            continue

    if not brand:
        raise Http404("Бренд не найден")

    return render(request, 'shop/brand_models.html', {
        'brand': brand,
        'models': brand.models.filter(is_active=True).order_by('name')
    })


@require_POST
@login_required
def create_order(request):
    """
    Создание заказа из корзины с сохранением адреса доставки.
    """
    cart = Cart.get_cart(request)
    if not cart.items.exists():
        return JsonResponse({'status': 'error', 'message': 'Корзина пуста'})

    # Получаем ID выбранного адреса
    address_id = request.POST.get('selected_address_id')
    delivery_address = None

    if address_id:
        try:
            # Получаем адрес из модели Address (предполагается, что она существует)
            from accounts.models import Address
            delivery_address = Address.objects.get(id=address_id, user=request.user)
        except Address.DoesNotExist:
            pass

    # Создаем заказ
    order = Order.objects.create(
        user=request.user,
        name=request.POST.get('name'),
        email=request.POST.get('email'),
        phone=request.POST.get('phone'),
        address=delivery_address.full_address if delivery_address else request.POST.get('address', ''),
        comment=request.POST.get('comment', ''),
        delivery_address=delivery_address  # Сохраняем ссылку на модель Address
    )

    # Добавляем товары из корзины
    for item in cart.items.select_related('product').all():
        order.items.create(
            product=item.product,
            price=item.product.price,
            quantity=item.quantity
        )

    # Очищаем корзину
    cart.items.all().delete()

    return JsonResponse({
        'status': 'success',
        'order_id': order.id
    })


@require_POST
@login_required
def process_payment(request):
    """
    Обработка платежа для заказа.
    """
    order_id = request.POST.get('order_id')
    payment_method = request.POST.get('payment_method')

    order = get_object_or_404(
        Order.objects.select_related('user'),
        id=order_id,
        user=request.user
    )

    # Создаем платеж
    payment = Payment.objects.create(
        order=order,
        amount=order.total_cost,
        method=payment_method
    )

    if payment_method == 'card':
        # Обработка карточного платежа
        card_number = request.POST.get('card_number', '')
        payment.card_last4 = card_number[-4:] if card_number else ''

        # Имитация успешной оплаты (90% успеха)
        if random.random() < 0.9:
            payment.status = 'succeeded'
            payment.transaction_id = ''.join(random.choices(string.digits, k=12))
        else:
            payment.status = 'failed'

    elif payment_method == 'sbp':
        # Обработка СБП
        payment.status = 'pending'
        payment.transaction_id = ''.join(random.choices(string.digits, k=12))

    payment.save()

    return JsonResponse({
        'status': payment.status,
        'payment_id': payment.id,
        'transaction_id': payment.transaction_id
    })


@login_required
def payment_status(request, order_id):
    """
    Проверка статуса платежа.
    """
    order = get_object_or_404(Order, id=order_id, user=request.user)
    payment = order.payments.last()

    if not payment:
        return JsonResponse({'status': 'error', 'message': 'Платеж не найден'})

    # Имитация успешного платежа через 10 секунд для СБП
    if payment.method == 'sbp' and payment.status == 'pending':
        if (timezone.now() - payment.created_at).seconds > 10:
            payment.status = 'succeeded'
            payment.save()

    return JsonResponse({
        'status': payment.status,
        'payment_id': payment.id,
        'method': payment.method
    })


# Классовые представления для грузовиков
class TruckBrandListView(ListView):
    model = TruckBrand
    template_name = 'trucks/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)

        # Фильтрация по стране
        country = self.request.GET.get('country')
        if country:
            queryset = queryset.filter(country=country)

        return queryset.select_related('country').order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['countries'] = TruckBrand.objects.values_list(
            'country', flat=True
        ).distinct().exclude(country__isnull=True)
        return context


class TruckBrandDetailView(DetailView):
    model = TruckBrand
    template_name = 'trucks/brand_detail.html'
    context_object_name = 'brand'

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'models',
            'truckbrandcategoryrelation_set__category'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['models'] = self.object.models.filter(is_active=True)
        context['main_categories'] = self.object.categories.filter(
            truckbrandcategoryrelation__is_main=True
        )
        return context


class TruckModelDetailView(DetailView):
    model = TruckModel
    template_name = 'trucks/model_detail.html'
    context_object_name = 'model'

    def get_queryset(self):
        return super().get_queryset().select_related('brand', 'type')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['generations'] = self.object.generations.filter(is_active=True)
        return context


# Классовые представления для мототехники
class MotoBrandListView(ListView):
    model = MotoBrand
    template_name = 'moto/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset().filter(is_active=True)

        # Фильтрация по категории если передана
        category_slug = self.request.GET.get('category')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug, show_in='moto')
            queryset = queryset.filter(
                motobrandcategoryrelation__category=category
            )

        return queryset.select_related('country').prefetch_related('categories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_categories'] = Category.objects.filter(show_in='moto')
        return context


class MotoBrandDetailView(DetailView):
    model = MotoBrand
    template_name = 'moto/brand_detail.html'
    context_object_name = 'brand'

    def get_queryset(self):
        return super().get_queryset().prefetch_related(
            'models__generations',
            'motobrandcategoryrelation_set__category'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        brand = self.object

        # Основные категории бренда
        context['main_categories'] = brand.motobrandcategoryrelation_set.filter(
            is_main=True
        ).select_related('category')

        # Все модели бренда с поколениями
        context['models'] = brand.models.filter(
            is_active=True
        ).prefetch_related('generations')

        return context


# Классовые представления для спецтехники
class SpecialBrandListView(ListView):
    model = SpecialBrand
    template_name = 'special/brand_list.html'
    context_object_name = 'brands'
    paginate_by = 20

    def get_queryset(self):
        return SpecialBrand.objects.filter(is_active=True).order_by('name')


class SpecialBrandDetailView(DetailView):
    model = SpecialBrand
    template_name = 'special/brand_detail.html'
    context_object_name = 'brand'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['models'] = SpecialModel.objects.filter(
            brand=self.object,
            is_active=True
        ).select_related('special_type')
        return context


# Классовые представления для аксессуаров
class AccessoryCategoryListView(ListView):
    model = AccessoryCategory
    template_name = 'accessories/category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class AccessoryBrandListView(ListView):
    model = AccessoryBrand
    template_name = 'accessories/brand_list.html'
    context_object_name = 'brands'

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


def category_list(request):
    categories = Category.objects.filter(parent__isnull=True)
    return render(request, 'shop/category_list.html', {'categories': categories})


class TruckGenerationDetailView(DetailView):
    model = TruckGeneration
    template_name = 'trucks/generation_detail.html'
    context_object_name = 'generation'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_parts'] = self.object.model.brand.categories.all()
        return context


def truck_type_list(request, type_slug):
    truck_type = get_object_or_404(TruckType, slug=type_slug)
    brands = TruckBrand.objects.filter(
        truck_types=truck_type,
        is_active=True
    ).order_by('name')

    return render(request, 'trucks/type_list.html', {
        'truck_type': truck_type,
        'brands': brands
    })


def truck_category_parts(request, brand_slug, category_slug):
    brand = get_object_or_404(TruckBrand, slug=brand_slug)
    category = get_object_or_404(Category, slug=category_slug)

    return render(request, 'trucks/category_parts.html', {
        'brand': brand,
        'category': category,
        'models': brand.models.filter(is_active=True)
    })


class MotoModelDetailView(DetailView):
    model = MotoModel
    template_name = 'moto/model_detail.html'
    context_object_name = 'model'

    def get_queryset(self):
        return super().get_queryset().select_related(
            'brand', 'moto_type'
        ).prefetch_related(
            'generations'
        )


def moto_category_tree(request):
    """Дерево категорий для мототехники"""
    categories = Category.objects.filter(
        show_in='moto'
    ).select_related('parent')

    return render(request, 'moto/category_tree.html', {
        'categories': categories
    })


def moto_category_detail(request, category_slug):
    """Детальная страница категории с привязанными брендами"""
    category = get_object_or_404(
        Category,
        slug=category_slug,
        show_in='moto'
    )

    # Бренды с этой категорией как основной
    main_brands = MotoBrand.objects.filter(
        category_relations__category=category,
        category_relations__is_main=True,
        is_active=True
    )

    # Бренды с этой категорией как дополнительной
    other_brands = MotoBrand.objects.filter(
        category_relations__category=category,
        category_relations__is_main=False,
        is_active=True
    ).exclude(
        id__in=main_brands.values_list('id', flat=True)
    )

    return render(request, 'moto/category_detail.html', {
        'category': category,
        'main_brands': main_brands,
        'other_brands': other_brands,
        'parent_categories': category.get_ancestors()
    })


class SpecialModelDetailView(DetailView):
    """Детальная страница модели с поколениями"""
    model = SpecialModel
    template_name = 'special/model_detail.html'
    context_object_name = 'model'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['generations'] = SpecialGeneration.objects.filter(
            model=self.object,
            is_active=True
        ).order_by('year_start')
        return context


class SpecialTypeListView(ListView):
    """Список типов спецтехники (экскаваторы, бульдозеры и т.д.)"""
    model = SpecialType
    template_name = 'special/type_list.html'
    context_object_name = 'types'


class SpecialTypeDetailView(DetailView):
    """Список брендов по типу спецтехники"""
    model = SpecialType
    template_name = 'special/type_detail.html'
    context_object_name = 'type'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = SpecialBrand.objects.filter(
            special_types=self.object,
            is_active=True
        ).order_by('name')
        return context


def navbar_categories(request):
    categories = Category.objects.filter(parent=None).prefetch_related(
        'category_set',
        'accessorycategory_set'
    ).select_related('parent').all()

    # Получаем все бренды по типам
    car_brands = CarBrand.objects.filter(is_active=True)
    truck_brands = TruckBrand.objects.filter(is_active=True)
    moto_brands = MotoBrand.objects.filter(is_active=True)
    special_brands = SpecialBrand.objects.filter(is_active=True)

    context = {
        'categories': categories,
        'car_brands': car_brands,
        'truck_brands': truck_brands,
        'moto_brands': moto_brands,
        'special_brands': special_brands,
    }
    return render(request, 'your_template.html', context)


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    return render(request, 'shop/category_list.html', {'category': category})


def oil_chemistry_products(request):
    # Получаем все активные одобренные товары категории "Автохимия и масла"
    products = Product.objects.visible_to_public().filter(
        oil_chem_category__isnull=False
    ).select_related(
        'oil_chem_category',
        'oil_chem_brand'
    ).prefetch_related('images')

    # Получаем подкатегории и бренды для фильтрации
    subcategories = OilAndChemistryCategory.objects.filter(
        is_active=True,
        parent__isnull=False
    )

    brands = OilAndChemistryBrand.objects.filter(is_active=True)

    context = {
        'products': products,
        'subcategories': subcategories,
        'brands': brands,
        'category_name': 'Автохимия и масла',
    }

    return render(request, 'shop/oil_chemistry_products.html', context)


@login_required
def add_review(request, product_slug):
    from django.contrib import messages

    product = get_object_or_404(Product, slug=product_slug)

    # Проверяем, купил ли пользователь этот товар
    if not product.user_has_purchased(request.user):
        messages.error(request, 'Только покупатели могут оставить отзыв об этом товаре.')
        return redirect('shop:product_detail', slug=product_slug)

    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)  # Добавляем request.FILES для обработки изображений
        if form.is_valid():
            # Проверяем, не оставлял ли пользователь уже отзыв
            review, created = Review.objects.get_or_create(
                product=product,
                user=request.user,
                defaults={
                    'rating': form.cleaned_data['rating'],
                    'comment': form.cleaned_data['comment'],
                    'image': form.cleaned_data.get('image'),  # Добавляем обработку изображения
                    'is_published': False  # По умолчанию отзыв на модерации
                }
            )

            if not created:
                # Обновляем существующий отзыв
                review.rating = form.cleaned_data['rating']
                review.comment = form.cleaned_data['comment']
                if 'image' in form.cleaned_data:
                    review.image = form.cleaned_data['image']
                review.is_published = False  # Сбрасываем публикацию для повторной модерации
                review.save()

            messages.success(request, 'Ваш отзыв отправлен на модерацию. Спасибо!')
            return redirect('shop:product_detail', slug=product_slug)

    else:
        form = ReviewForm()

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'review_form': form
    })


@login_required
def review_helpful_vote(request, review_id):
    """
    API endpoint для голосования за полезность отзыва
    """
    from shop.models import ReviewFeedback
    import json

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Метод не разрешен'}, status=405)

    # Review уже импортирован в начале файла
    review = get_object_or_404(Review, id=review_id, is_published=True)

    try:
        data = json.loads(request.body)
        helpful = data.get('helpful')

        if helpful is None:
            return JsonResponse({'success': False, 'error': 'Параметр helpful обязателен'}, status=400)

        helpful = bool(helpful)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'success': False, 'error': 'Неверный формат данных'}, status=400)

    # Проверяем, не голосовал ли уже пользователь за этот отзыв
    feedback, created = ReviewFeedback.objects.get_or_create(
        review=review,
        user=request.user,
        defaults={'helpful': helpful}
    )

    if not created:
        # Если пользователь уже голосовал, обновляем его голос
        feedback.helpful = helpful
        feedback.save()

    # Возвращаем обновленные счетчики
    return JsonResponse({
        'success': True,
        'helpful_yes': review.helpful_yes,
        'helpful_no': review.helpful_no,
        'user_vote': helpful
    })


def terms_view(request):
    return terms(request)


def privacy_view(request):
    return privacy_policy(request)


def product_list_view(request, products_queryset, title, template_name='shop/product_list.html'):
    """Универсальная view для списка товаров с пагинацией"""

    # Сортировка
    sort_by = request.GET.get('sort', 'created_at')
    order = request.GET.get('order', 'desc')

    valid_sort_fields = ['price', 'created_at', 'name', 'views', 'rating']
    if sort_by not in valid_sort_fields:
        sort_by = 'created_at'

    order_prefix = '-' if order == 'desc' else ''
    products = products_queryset.order_by(f'{order_prefix}{sort_by}')

    # Пагинация
    paginator = Paginator(products, 24)  # 24 товара на страницу
    page = request.GET.get('page')

    try:
        products_page = paginator.page(page)
    except PageNotAnInteger:
        products_page = paginator.page(1)
    except EmptyPage:
        products_page = paginator.page(paginator.num_pages)

    context = {
        'products': products_page,
        'title': title,
        'sort_by': sort_by,
        'order': order,
        'paginator': paginator,
    }

    return render(request, template_name, context)


def new_products(request):
    products = Product.objects.visible_to_public().filter(
        Q(is_new=True) | Q(created_at__gte=timezone.now() - timedelta(days=30))
    ).select_related('category', 'manufacturer')

    return product_list_view(request, products, 'Новинки')


def sale_products(request):
    products = Product.objects.visible_to_public().filter(
        old_price__isnull=False,
        old_price__gt=F('price')
    ).select_related('category', 'manufacturer')

    return product_list_view(request, products, 'Распродажа')


def popular_products(request):
    products = Product.objects.visible_to_public().annotate(
        order_count=Count('order_items'),
        rating=Avg('reviews__rating')
    )

    return product_list_view(request, products, 'Популярные товары')


def get_cached_products(key, queryset, timeout=1800):
    """Универсальная функция для кэширования продуктов. Пустой список не кэшируем — при следующем запросе перезапросим БД."""
    cached_data = cache.get(key)
    if cached_data is None or (isinstance(cached_data, list) and len(cached_data) == 0):
        data = list(queryset)
        if len(data) > 0:
            cache.set(key, data, timeout)
        return data
    return cached_data


def index(request):
    # Ключи для кэширования
    cache_keys = {
        'new_products': 'home_new_products',
        'sale_products': 'home_sale_products',
        'popular_products': 'home_popular_products',
        'featured_products': 'home_featured_products',
        'bestsellers': 'home_bestsellers',

    }

    # Новинки (кэшируем на 1 час)
    new_products = get_cached_products(
        cache_keys['new_products'],
        Product.objects.visible_to_public().filter(
            Q(is_new=True) | Q(created_at__gte=timezone.now() - timedelta(days=14))
        ).select_related('category', 'manufacturer')[:12],
        3600
    )

    # Распродажа (кэшируем на 2 часа)
    sale_products = get_cached_products(
        cache_keys['sale_products'],
        Product.objects.visible_to_public().filter(
            old_price__isnull=False,
            old_price__gt=F('price')
        ).select_related('category', 'manufacturer')[:12],
        7200
    )

    # Популярные товары (кэшируем на 4 часа)
    popular_products = get_cached_products(
        cache_keys['popular_products'],
        Product.objects.visible_to_public()
        .annotate(order_count=Count('order_items'))
        .order_by('-views', '-order_count')[:12],
        14400
    )

    # Рекомендуемые товары (кэшируем на 3 часа)
    featured_products = get_cached_products(
        cache_keys['featured_products'],
        Product.objects.visible_to_public().filter(
            is_featured=True
        ).select_related('category', 'manufacturer')[:12],
        10800
    )

    # Лидеры продаж (кэшируем на 6 часов)
    month_ago = timezone.now() - timedelta(days=30)
    bestsellers = get_cached_products(
        cache_keys['bestsellers'],
        Product.objects.visible_to_public().filter(
            order_items__order__created_at__gte=month_ago
        ).distinct().annotate(sales_count=Count('order_items'))
        .order_by('-sales_count')[:8],
        21600
    )
    # Если все блоки пустые — показываем хотя бы любые активные товары в блоке «Новинки»
    if not new_products and not sale_products and not popular_products and not bestsellers:
        new_products = list(
            Product.objects.visible_to_public()
            .select_related('category', 'manufacturer')[:12]
        )

    carousel_slides = list(CarouselSlide.objects.filter(is_active=True).order_by('order', 'created_at'))

    context = {
        'new_products': new_products,
        'sale_products': sale_products,
        'popular_products': popular_products,
        'featured_products': featured_products,
        'bestsellers': bestsellers,
        'carousel_slides': carousel_slides,
    }

    return render(request, 'shop/index.html', context)


@csrf_exempt
@require_POST
def track_product_click(request, product_id):
    """Отслеживание кликов по товарам (AJAX)"""
    try:
        product = Product.objects.get(id=product_id)

        ProductClick.objects.create(
            product=product,
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key,
            ip_address=get_client_ip(request),
            referrer=request.META.get('HTTP_REFERER')
        )

        return JsonResponse({'status': 'success'})

    except Product.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_recommendations(request, product=None):
    """Получение рекомендаций на основе статистики"""
    if request.user.is_authenticated:
        # Рекомендации на основе истории просмотров пользователя
        recently_viewed = ProductView.objects.filter(
            user=request.user
        ).order_by('-timestamp').values_list('product_id', flat=True)[:10]

        if recently_viewed:
            return Product.objects.visible_to_public().filter(
                category__in=Product.objects.visible_to_public().filter(
                    id__in=recently_viewed
                ).values('category')
            ).exclude(id__in=recently_viewed)[:8]

    # Рекомендации на основе популярности
    return Product.objects.visible_to_public().annotate(
        order_count=Count('order_items'),
        view_count=Count('view_stats')
    ).order_by('-order_count', '-view_count')[:8]


def maintenance_selection(request):
    """Главная страница подбора ТО"""
    return render(request, 'shop/selection.html')


def select_vehicle_type(request, vehicle_type):
    """Выбор типа транспорта"""
    brands = CarBrand.objects.filter(vehicle_type=vehicle_type)
    return render(request, 'shop/select_brand.html', {
        'vehicle_type': vehicle_type,
        'brands': brands
    })


def select_model(request, vehicle_type, brand_slug):
    """Выбор модели транспорта"""

    # Получаем бренд в зависимости от типа транспорта
    if vehicle_type == 'car':
        brand = CarBrand.objects.get(slug=brand_slug, is_active=True)
        models = CarModel.objects.filter(brand=brand, is_active=True)
    elif vehicle_type == 'truck':
        brand = TruckBrand.objects.get(slug=brand_slug, is_active=True)
        models = TruckModel.objects.filter(brand=brand, is_active=True)
    elif vehicle_type == 'moto':
        brand = MotoBrand.objects.get(slug=brand_slug, is_active=True)
        models = MotoModel.objects.filter(brand=brand, is_active=True)
    elif vehicle_type == 'special':
        brand = SpecialBrand.objects.get(slug=brand_slug, is_active=True)
        models = SpecialModel.objects.filter(brand=brand, is_active=True)
    else:
        brand = None
        models = []

    vehicle_names = {
        'car': 'легковых автомобилей',
        'truck': 'грузовых автомобилей',
        'moto': 'мототехники',
        'special': 'спецтехники'
    }

    return render(request, 'shop/select_model.html', {
        'vehicle_type': vehicle_type,
        'vehicle_type_name': vehicle_names.get(vehicle_type, 'транспорта'),
        'brand': brand,
        'models': models
    })


def maintenance_for_vehicle(request, vehicle_type, brand_slug, model_slug, generation_slug=None):
    """Страница ТО для выбранного авто"""
    brand = get_object_or_404(CarBrand, slug=brand_slug)
    model = get_object_or_404(CarModel, slug=model_slug, brand=brand)
    generation = get_object_or_404(CarGeneration, slug=generation_slug) if generation_slug else None

    # Получаем товары для ТО (только одобренные)
    maintenance_products = Product.objects.visible_to_public().filter(
        product_type='maintenance',
        car_brand=brand,
        car_models=model
    )

    if generation:
        maintenance_products = maintenance_products.filter(car_generations=generation)

    # Группируем по типам
    products_by_type = {}
    for product in maintenance_products:
        if product.maintenance_type not in products_by_type:
            products_by_type[product.maintenance_type] = []
        products_by_type[product.maintenance_type].append(product)

    # Получаем комплекты ТО
    kits = MaintenanceKit.objects.filter(
        is_active=True,
        vehicle_type=vehicle_type,
        car_brand=brand,
        car_models=model
    )

    return render(request, 'shop/for_vehicle.html', {
        'brand': brand,
        'model': model,
        'generation': generation,
        'products_by_type': products_by_type,
        'kits': kits,
        'vehicle_type': vehicle_type
    })


def maintenance_category(request, vehicle_type, brand_slug, model_slug, generation_slug, maintenance_type):
    """Фильтрация внутри категории ТО"""
    brand = get_object_or_404(CarBrand, slug=brand_slug)
    model = get_object_or_404(CarModel, slug=model_slug, brand=brand)
    generation = get_object_or_404(CarGeneration, slug=generation_slug) if generation_slug else None

    products = Product.objects.visible_to_public().filter(
        product_type='maintenance',
        maintenance_type=maintenance_type,
        car_brand=brand,
        car_models=model
    )

    if generation:
        products = products.filter(car_generations=generation)

    # Фильтры в зависимости от типа
    filters = {}
    if maintenance_type == 'engine_oil':
        filters['viscosity'] = products.values_list('viscosity', flat=True).distinct()
        filters['brand'] = products.values_list('manufacturer__name', flat=True).distinct()

    # Применяем фильтры из GET-параметров
    viscosity = request.GET.get('viscosity')
    if viscosity:
        products = products.filter(viscosity=viscosity)

    brand_filter = request.GET.get('brand')
    if brand_filter:
        products = products.filter(manufacturer__name=brand_filter)

    return render(request, 'shop/category.html', {
        'products': products,
        'maintenance_type': maintenance_type,
        'filters': filters,
        'brand': brand,
        'model': model,
        'generation': generation
    })


def select_brand(request, vehicle_type):
    """Выбор марки автомобиля"""

    # Выбираем соответствующую модель бренда в зависимости от типа транспорта
    if vehicle_type == 'car':
        brands = CarBrand.objects.filter(is_active=True)
        vehicle_name = 'Легковые автомобили'
    elif vehicle_type == 'truck':
        brands = TruckBrand.objects.filter(is_active=True)
        vehicle_name = 'Грузовые автомобили'
    elif vehicle_type == 'moto':
        brands = MotoBrand.objects.filter(is_active=True)
        vehicle_name = 'Мототехника'
    elif vehicle_type == 'special':
        brands = SpecialBrand.objects.filter(is_active=True)
        vehicle_name = 'Спецтехника'
    else:
        brands = []
        vehicle_name = 'Транспорт'

    return render(request, 'shop/select_brand.html', {
        'vehicle_type': vehicle_type,
        'vehicle_name': vehicle_name,
        'brands': brands
    })


def select_year(request, vehicle_type, brand_slug, model_slug):
    """Выбор года выпуска"""
    # Здесь логика для выбора года
    return render(request, 'shop/select_year.html', {
        'vehicle_type': vehicle_type,
        'brand_slug': brand_slug,
        'model_slug': model_slug
    })


def for_vehicle(request, vehicle_type, brand_slug, model_slug, generation_slug=None, modification_slug=None):
    """Страница с товарами для конкретного автомобиля с фильтрацией"""

    # Словарь для отображения типа транспорта в человекочитаемый вид
    vehicle_names = {
        'car': 'Легковые',
        'truck': 'Грузовые',
        'moto': 'Мотоциклы',
        'special': 'Спецтехника'
    }

    # Получаем бренд и модель в зависимости от типа транспорта
    if vehicle_type == 'car':
        brand = CarBrand.objects.get(slug=brand_slug, is_active=True)
        model = CarModel.objects.get(slug=model_slug, brand=brand, is_active=True)
        brand_field = 'car_brand'
        models_field = 'car_models'
        modifications_field = 'car_modifications'

        # Получаем поколение если указано
        generation = None
        if generation_slug and generation_slug != 'all':
            try:
                generation = CarGeneration.objects.get(slug=generation_slug, model=model, is_active=True)
            except CarGeneration.DoesNotExist:
                generation = None

        # Получаем модификацию если указана
        modification = None
        if modification_slug and modification_slug != 'all':
            try:
                modification = CarModification.objects.get(
                    slug=modification_slug,
                    generation=generation if generation else None
                )
            except CarModification.DoesNotExist:
                modification = None

    elif vehicle_type == 'truck':
        brand = TruckBrand.objects.get(slug=brand_slug, is_active=True)
        model = TruckModel.objects.get(slug=model_slug, brand=brand, is_active=True)
        brand_field = 'truck_brand'
        models_field = 'truck_models'
        modifications_field = 'truck_modifications'
        generation = None
        modification = None

        if generation_slug and generation_slug != 'all':
            try:
                generation = TruckGeneration.objects.get(slug=generation_slug, model=model, is_active=True)
            except TruckGeneration.DoesNotExist:
                generation = None

        if modification_slug and modification_slug != 'all':
            try:
                modification = TruckModification.objects.get(
                    slug=modification_slug,
                    generation=generation if generation else None
                )
            except TruckModification.DoesNotExist:
                modification = None

    elif vehicle_type == 'moto':
        brand = MotoBrand.objects.get(slug=brand_slug, is_active=True)
        model = MotoModel.objects.get(slug=model_slug, brand=brand, is_active=True)
        brand_field = 'moto_brand'
        models_field = 'moto_models'
        modifications_field = 'moto_modifications'
        generation = None
        modification = None

        if generation_slug and generation_slug != 'all':
            try:
                generation = MotoGeneration.objects.get(slug=generation_slug, model=model, is_active=True)
            except MotoGeneration.DoesNotExist:
                generation = None

        if modification_slug and modification_slug != 'all':
            try:
                modification = MotoModification.objects.get(
                    slug=modification_slug,
                    generation=generation if generation else None
                )
            except MotoModification.DoesNotExist:
                modification = None

    elif vehicle_type == 'special':
        brand = SpecialBrand.objects.get(slug=brand_slug, is_active=True)
        model = SpecialModel.objects.get(slug=model_slug, brand=brand, is_active=True)
        brand_field = 'special_brand'
        models_field = 'special_models'
        modifications_field = 'special_modifications'
        generation = None
        modification = None

        if generation_slug and generation_slug != 'all':
            try:
                generation = SpecialGeneration.objects.get(slug=generation_slug, model=model, is_active=True)
            except SpecialGeneration.DoesNotExist:
                generation = None

        if modification_slug and modification_slug != 'all':
            try:
                modification = SpecialModification.objects.get(
                    slug=modification_slug,
                    generation=generation if generation else None
                )
            except SpecialModification.DoesNotExist:
                modification = None

    else:
        brand = None
        model = None
        brand_field = ''
        models_field = ''
        modifications_field = ''
        generation = None
        modification = None

    # Получаем комплекты ТО для данного транспорта
    if brand and model:
        # Создаем условия фильтрации для комплектов
        kit_filters = Q(vehicle_type=vehicle_type) & Q(is_active=True)

        # Добавляем условие для бренда
        if brand_field:
            kit_filters &= (Q(**{brand_field: brand}) | Q(**{f"{brand_field}__isnull": True}))

        # Добавляем условие для модели
        if models_field:
            kit_filters &= (Q(**{f"{models_field}__in": [model]}) | Q(**{f"{models_field}__isnull": True}))

        kits = MaintenanceKit.objects.filter(kit_filters).distinct()

        # Получаем товары для данного транспорта
        product_filters = Q(vehicle_type=vehicle_type) & Q(is_active=True)

        if brand_field and hasattr(Product, brand_field):
            product_filters &= (Q(**{brand_field: brand}) | Q(**{f"{brand_field}__isnull": True}))

        if models_field and hasattr(Product, models_field):
            product_filters &= (Q(**{f"{models_field}__in": [model]}) | Q(**{f"{models_field}__isnull": True}))

        # Фильтрация по поколению
        if generation and hasattr(Product, 'car_generations'):
            product_filters &= (Q(car_generations=generation) | Q(car_generations__isnull=True))

        # Фильтрация по модификации
        if modification and hasattr(Product, modifications_field):
            product_filters &= (Q(**{f"{modifications_field}__in": [modification]}) | Q(
                **{f"{modifications_field}__isnull": True}))

        products = Product.objects.visible_to_public().filter(product_filters).distinct()

        # --- ФИЛЬТРАЦИЯ ИЗ GET-ПАРАМЕТРОВ ---
        price_min = request.GET.get('price_min')
        price_max = request.GET.get('price_max')
        maintenance_type_filter = request.GET.get('maintenance_type')
        manufacturer_filter = request.GET.get('manufacturer')
        is_original_filter = request.GET.get('is_original')
        has_discount_filter = request.GET.get('has_discount')
        in_stock_filter = request.GET.get('in_stock')
        viscosity_filter = request.GET.get('viscosity')
        volume_filter = request.GET.get('volume')

        # Применяем фильтры
        if price_min:
            products = products.filter(price__gte=price_min)
        if price_max:
            products = products.filter(price__lte=price_max)
        if maintenance_type_filter:
            products = products.filter(maintenance_type=maintenance_type_filter)
        if manufacturer_filter:
            products = products.filter(manufacturer__slug=manufacturer_filter)
        if is_original_filter:
            products = products.filter(is_original=True)
        if has_discount_filter:
            products = products.filter(old_price__isnull=False, old_price__gt=F('price'))
        if in_stock_filter:
            products = products.filter(stock__gt=0)
        if viscosity_filter:
            products = products.filter(viscosity=viscosity_filter)
        if volume_filter:
            products = products.filter(volume=volume_filter)

        # Сортировка
        sort = request.GET.get('sort')
        if sort == 'price_asc':
            products = products.order_by('price')
        elif sort == 'price_desc':
            products = products.order_by('-price')
        elif sort == 'newest':
            products = products.order_by('-created_at')
        elif sort == 'popular':
            products = products.annotate(order_count=Count('order_items')).order_by('-order_count', '-views')

    else:
        kits = MaintenanceKit.objects.none()
        products = Product.objects.none()

    # Группируем товары по типам ТО
    products_by_type = {}
    if hasattr(Product, 'maintenance_type'):
        for product in products:
            if product.maintenance_type not in products_by_type:
                products_by_type[product.maintenance_type] = []
            products_by_type[product.maintenance_type].append(product)

        # Сортируем товары внутри каждой категории
        for maintenance_type in products_by_type:
            products_by_type[maintenance_type].sort(key=lambda x: x.price)

    # Получаем данные для фильтров
    maintenance_types = Product.MAINTENANCE_TYPES
    manufacturers = Manufacturer.objects.filter(
        product__in=products
    ).distinct().order_by('name')

    viscosities = Product.objects.filter(
        viscosity__isnull=False,
        id__in=products.values_list('id', flat=True)
    ).values_list('viscosity', flat=True).distinct().order_by('viscosity')

    volumes = Product.objects.filter(
        volume__isnull=False,
        id__in=products.values_list('id', flat=True)
    ).values_list('volume', flat=True).distinct().order_by('volume')

    # Получаем ID избранных товаров и товаров в корзине для текущего пользователя
    favorite_ids = []
    cart_product_ids = []
    cart_kit_ids = []

    if request.user.is_authenticated:
        # Избранное
        favorite_ids = list(request.user.favorites.values_list('product_id', flat=True))

        # Корзина товаров
        cart = Cart.get_cart(request)
        cart_product_ids = list(cart.items.values_list('product_id', flat=True))

        # Корзина комплектов
        cart_kit_ids = list(cart.kit_items.values_list('kit_id', flat=True)) if hasattr(cart, 'kit_items') else []

    # Строим хлебные крошки
    breadcrumbs = [
        {'name': 'Главная', 'url': reverse('shop:index')},
        {'name': 'Для ТО', 'url': reverse('shop:maintenance_selection')},
        {'name': vehicle_names.get(vehicle_type, 'Транспорт'),
         'url': reverse('shop:maintenance_select_brand', kwargs={'vehicle_type': vehicle_type})},
        {'name': brand.name,
         'url': reverse('shop:maintenance_select_model', kwargs={
             'vehicle_type': vehicle_type,
             'brand_slug': brand_slug})},
        {'name': model.name,
         'url': reverse('shop:select_generation', kwargs={
             'vehicle_type': vehicle_type,
             'brand_slug': brand_slug,
             'model_slug': model_slug})},
    ]

    if generation and generation_slug != 'all':
        breadcrumbs.append({
            'name': generation.name,
            'url': reverse('shop:select_modification', kwargs={
                'vehicle_type': vehicle_type,
                'brand_slug': brand_slug,
                'model_slug': model_slug,
                'generation_slug': generation_slug
            })
        })

    if modification and modification_slug != 'all':
        breadcrumbs.append({'name': modification.name, 'url': '#'})

    context = {
        'vehicle_type': vehicle_type,
        'brand': brand,
        'model': model,
        'generation': generation,
        'modification': modification,
        'kits': kits,
        'products_by_type': products_by_type,
        'products_count': products.count(),
        'breadcrumbs': breadcrumbs,

        # Данные для фильтров
        'maintenance_types': maintenance_types,
        'manufacturers': manufacturers,
        'viscosities': viscosities,
        'volumes': volumes,

        # Состояния пользователя
        'favorite_ids': favorite_ids,
        'cart_product_ids': cart_product_ids,
        'cart_kit_ids': cart_kit_ids,

        # Передаем GET-параметры для сохранения состояния фильтров
        'request': request,
    }

    return render(request, 'shop/for_vehicle.html', context)


def select_generation(request, vehicle_type, brand_slug, model_slug):
    """Выбор поколения модели (теперь перенаправляет на выбор модификации)"""

    # Получаем бренд и модель
    if vehicle_type == 'car':
        brand = CarBrand.objects.get(slug=brand_slug, is_active=True)
        model = CarModel.objects.get(slug=model_slug, brand=brand, is_active=True)
        generations = CarGeneration.objects.filter(model=model, is_active=True)
    elif vehicle_type == 'truck':
        brand = TruckBrand.objects.get(slug=brand_slug, is_active=True)
        model = TruckModel.objects.get(slug=model_slug, brand=brand, is_active=True)
        generations = TruckGeneration.objects.filter(model=model, is_active=True)
    elif vehicle_type == 'moto':
        brand = MotoBrand.objects.get(slug=brand_slug, is_active=True)
        model = MotoModel.objects.get(slug=model_slug, brand=brand, is_active=True)
        generations = MotoGeneration.objects.filter(model=model, is_active=True)
    elif vehicle_type == 'special':
        brand = SpecialBrand.objects.get(slug=brand_slug, is_active=True)
        model = SpecialModel.objects.get(slug=model_slug, brand=brand, is_active=True)
        generations = SpecialGeneration.objects.filter(model=model, is_active=True)
    else:
        raise Http404("Тип транспорта не найден")

    vehicle_names = {
        'car': 'легковых автомобилей',
        'truck': 'грузовых автомобилей',
        'moto': 'мототехники',
        'special': 'спецтехники'
    }

    return render(request, 'shop/select_generation.html', {
        'vehicle_type': vehicle_type,
        'vehicle_type_name': vehicle_names.get(vehicle_type, 'транспорта'),
        'brand': brand,
        'model': model,
        'generations': generations
    })


# Выбор модификации поколения
def select_modification(request, vehicle_type, brand_slug, model_slug, generation_slug):
    """Выбор модификации поколения"""

    # Получаем бренд, модель и поколение
    if vehicle_type == 'car':
        brand = CarBrand.objects.get(slug=brand_slug, is_active=True)
        model = CarModel.objects.get(slug=model_slug, brand=brand, is_active=True)
        generation = CarGeneration.objects.get(slug=generation_slug, model=model, is_active=True)
        modifications = CarModification.objects.filter(generation=generation)
    elif vehicle_type == 'truck':
        brand = TruckBrand.objects.get(slug=brand_slug, is_active=True)
        model = TruckModel.objects.get(slug=model_slug, brand=brand, is_active=True)
        generation = TruckGeneration.objects.get(slug=generation_slug, model=model, is_active=True)
        modifications = TruckModification.objects.filter(generation=generation)
    elif vehicle_type == 'moto':
        brand = MotoBrand.objects.get(slug=brand_slug, is_active=True)
        model = MotoModel.objects.get(slug=model_slug, brand=brand, is_active=True)
        generation = MotoGeneration.objects.get(slug=generation_slug, model=model, is_active=True)
        modifications = MotoModification.objects.filter(generation=generation)
    elif vehicle_type == 'special':
        brand = SpecialBrand.objects.get(slug=brand_slug, is_active=True)
        model = SpecialModel.objects.get(slug=model_slug, brand=brand, is_active=True)
        generation = SpecialGeneration.objects.get(slug=generation_slug, model=model, is_active=True)
        modifications = SpecialModification.objects.filter(generation=generation)
    else:
        raise Http404("Тип транспорта не найден")

    vehicle_names = {
        'car': 'легковых автомобилей',
        'truck': 'грузовых автомобилей',
        'moto': 'мототехники',
        'special': 'спецтехники'
    }

    return render(request, 'shop/select_modification.html', {
        'vehicle_type': vehicle_type,
        'vehicle_type_name': vehicle_names.get(vehicle_type, 'транспорта'),
        'brand': brand,
        'model': model,
        'generation': generation,
        'modifications': modifications
    })


def slider_captcha_view(request):
    """Отображение страницы со слайдер-капчей (Cloudflare Turnstile)"""
    return render(request, 'shop/slider_captcha.html', {
        'site_key': settings.TURNSTILE_SITE_KEY
    })


def verify_slider_captcha(request):
    """Проверка Cloudflare Turnstile капчи"""
    if request.method == 'POST':
        turnstile_response = request.POST.get('cf-turnstile-response')
        next_url = request.POST.get('next', '/').strip()
        # Защита от open redirect: только относительные пути
        if not next_url.startswith('/') or next_url.startswith('//'):
            next_url = '/'

        if not getattr(settings, 'TURNSTILE_SECRET_KEY', ''):
            return render(request, 'shop/slider_captcha.html', {
                'error': 'Капча не настроена: отсутствует TURNSTILE_SECRET_KEY в настройках.',
                'next': next_url,
                'site_key': getattr(settings, 'TURNSTILE_SITE_KEY', ''),
            })

        if not turnstile_response:
            return render(request, 'shop/slider_captcha.html', {
                'error': 'Пожалуйста, пройдите проверку.',
                'next': next_url,
                'site_key': getattr(settings, 'TURNSTILE_SITE_KEY', ''),
            })

        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        remote_ip = x_forwarded_for.split(',')[0].strip() if x_forwarded_for else request.META.get('REMOTE_ADDR')

        verify_url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
        payload = {
            'secret': settings.TURNSTILE_SECRET_KEY,
            'response': turnstile_response,
            'remoteip': remote_ip,
        }

        try:
            response = requests.post(verify_url, data=payload)
            result = response.json()

            if result.get('success'):
                request.session['captcha_passed'] = True
                request.session['captcha_timestamp'] = time.time()
                request.session.modified = True
                return redirect(next_url)
            else:
                return render(request, 'shop/slider_captcha.html', {
                    'error': 'Проверка не пройдена. Попробуйте еще раз.',
                    'next': next_url,
                    'site_key': settings.TURNSTILE_SITE_KEY
                })
        except requests.exceptions.RequestException:
            return render(request, 'shop/slider_captcha.html', {
                'error': 'Ошибка соединения с сервером проверки. Попробуйте позже.',
                'next': next_url,
                'site_key': settings.TURNSTILE_SITE_KEY
            })

    return redirect('shop:slider_captcha_view')


######## Теги ###########

def tag_detail(request, slug):
    """Страница с товарами по тегу"""
    tag = get_object_or_404(Tag, slug=slug, is_active=True)
    products = tag.products.filter(is_active=True).select_related(
        'category', 'manufacturer'
    ).prefetch_related('images')

    # Пагинация
    paginator = Paginator(products, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'tag': tag,
        'products': page_obj,
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'title': f'Товары с тегом #{tag.name}'
    }

    return render(request, 'shop/tag_detail.html', context)


def about(request):
    """Страница 'О нас'"""
    context = {
        'title': 'О нас | LinkAvto',
        'meta_description': 'Информация о компании LinkAvto - интернет-магазине автозапчастей. Наша миссия, ценности и история.',
    }
    return render(request, 'shop/about.html', context)


def help(request):
    """Страница 'Помощь'"""
    # Список часто задаваемых вопросов
    faqs = [
        {
            'question': 'Как оформить заказ?',
            'answer': 'Для оформления заказа добавьте товары в корзину и перейдите к оформлению заказа.'
        },
        {
            'question': 'Какие способы оплаты доступны?',
            'answer': 'Мы принимаем банковские карты, электронные кошельки и наличные при получении.'
        },
        {
            'question': 'Как отследить мой заказ?',
            'answer': 'После отправки заказа вам придет трек-номер для отслеживания.'
        },
        {
            'question': 'Какие условия доставки?',
            'answer': 'Доставка осуществляется по всей России. Сроки и стоимость зависят от региона.'
        },
        {
            'question': 'Можно ли вернуть товар?',
            'answer': 'Да, вы можете вернуть товар в течение 14 дней с момента получения.'
        },
        {
            'question': 'Как связаться с поддержкой?',
            'answer': 'Вы можете написать нам на email linkavto@linkavto.ru или позвонить по телефону.'
        },
    ]

    context = {
        'title': 'Помощь | LinkAvto',
        'meta_description': 'Часто задаваемые вопросы, помощь по оформлению заказа, доставке, оплате и возврату товаров.',
        'faqs': faqs,
    }
    return render(request, 'shop/help.html', context)


def terms(request):
    doc = SiteDocument.objects.filter(doc_type='terms', is_active=True).first()
    context = {
        'title': (doc.title if doc else 'Пользовательское соглашение') + ' | LinkAvto',
        'meta_description': 'Условия использования сайта LinkAvto. Правила оформления заказов и пользования услугами магазина.',
        'document': doc,
    }
    return render(request, 'shop/terms.html', context)


def return_policy(request):
    doc = SiteDocument.objects.filter(doc_type='return_policy', is_active=True).first()
    context = {
        'title': (doc.title if doc else 'Условия возврата') + ' | LinkAvto',
        'meta_description': 'Условия возврата товаров в интернет-магазине LinkAvto. Порядок возврата денежных средств.',
        'document': doc,
    }
    return render(request, 'shop/return_policy.html', context)


def privacy_policy(request):
    doc = SiteDocument.objects.filter(doc_type='privacy', is_active=True).first()
    context = {
        'title': (doc.title if doc else 'Политика конфиденциальности') + ' | LinkAvto',
        'meta_description': 'Политика конфиденциальности и обработки персональных данных интернет-магазина LinkAvto.',
        'document': doc,
    }
    return render(request, 'shop/privacy.html', context)


def personal_data(request):
    doc = SiteDocument.objects.filter(doc_type='personal_data', is_active=True).first()
    context = {
        'title': (doc.title if doc else 'Обработка персональных данных') + ' | LinkAvto',
        'meta_description': 'Политика обработки персональных данных интернет-магазина LinkAvto.',
        'document': doc,
    }
    return render(request, 'shop/document.html', context)


def public_offer(request):
    doc = SiteDocument.objects.filter(doc_type='offer', is_active=True).first()
    context = {
        'title': (doc.title if doc else 'Публичная оферта') + ' | LinkAvto',
        'meta_description': 'Публичная оферта интернет-магазина LinkAvto.',
        'document': doc,
    }
    return render(request, 'shop/document.html', context)


def buyer_rules(request):
    doc = SiteDocument.objects.filter(doc_type='buyer_rules', is_active=True).first()
    context = {
        'title': (doc.title if doc else 'Правила покупки') + ' | LinkAvto',
        'meta_description': 'Правила покупки товаров в интернет-магазине LinkAvto.',
        'document': doc,
    }
    return render(request, 'shop/document.html', context)


def seller_rules(request):
    doc = SiteDocument.objects.filter(doc_type='seller_rules', is_active=True).first()
    context = {
        'title': (doc.title if doc else 'Правила продажи') + ' | LinkAvto',
        'meta_description': 'Правила продажи товаров на платформе LinkAvto.',
        'document': doc,
    }
    return render(request, 'shop/document.html', context)


def tech_recommendations(request):
    doc = SiteDocument.objects.filter(doc_type='tech_recommendations', is_active=True).first()
    context = {
        'title': (doc.title if doc else 'Рекомендуемые технологии') + ' | LinkAvto',
        'meta_description': 'Рекомендуемые технологии для работы с сайтом LinkAvto.',
        'document': doc,
    }
    return render(request, 'shop/document.html', context)


# Подключение прелоадера
@require_GET
def set_preloader_shown(request):
    """Устанавливает флаг, что прелоадер был показан"""
    request.session['preloader_shown'] = True
    request.session.modified = True
    return JsonResponse({'status': 'ok'})


@require_GET
def category_children_api(request, slug):
    """Публичный API: дочерние категории по slug (для динамических фильтров)"""
    try:
        cat = Category.objects.get(slug=slug, is_active=True)
        children = Category.objects.filter(parent=cat, is_active=True).order_by('name')
        return JsonResponse([
            {'slug': c.slug, 'name': c.name}
            for c in children
        ], safe=False)
    except Category.DoesNotExist:
        return JsonResponse([], safe=False)
