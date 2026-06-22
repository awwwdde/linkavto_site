import re

from django.db.models import Avg, Case, IntegerField, Q, When

from shop.models import Product, ProductCrossReference, normalize_article_number
from .fuzzy_search import FuzzySearchService


VIN_PATTERN = re.compile(r'^[A-Z0-9]{17}$', re.IGNORECASE)
LICENSE_PLATE_PATTERN = re.compile(r'^[ABEKMHOPCTYX]\d{3}[ABEKMHOPCTYX]{2}\d{2,3}$')
LICENSE_PLATE_TRANSLATION = str.maketrans({
    'А': 'A',
    'В': 'B',
    'Е': 'E',
    'К': 'K',
    'М': 'M',
    'Н': 'H',
    'О': 'O',
    'Р': 'P',
    'С': 'C',
    'Т': 'T',
    'У': 'Y',
    'Х': 'X',
})


def normalize_vehicle_identifier(value):
    if not value:
        return ''
    value = ''.join(char for char in str(value).upper() if char.isalnum())
    return value.translate(LICENSE_PLATE_TRANSLATION)


class SearchService:
    @staticmethod
    def detect_search_type(query):
        normalized_vehicle = normalize_vehicle_identifier(query)
        normalized_article = normalize_article_number(query)

        if VIN_PATTERN.match(normalized_vehicle):
            return 'vin'
        if LICENSE_PLATE_PATTERN.match(normalized_vehicle):
            return 'license_plate'
        if len(normalized_article) >= 3 and any(char.isdigit() for char in normalized_article):
            return 'part_number'
        return 'text'

    @staticmethod
    def search_products(query, filters=None):
        if not query:
            return Product.objects.none()

        filters = filters or {}
        search_type = filters.get('search_type') or SearchService.detect_search_type(query)
        filters['search_type'] = search_type
        filters['is_vin_search'] = search_type == 'vin'
        filters['is_plate_search'] = search_type == 'license_plate'

        base_queryset = Product.objects.filter(is_active=True).select_related(
            'category', 'manufacturer', 'seller', 'product_brand'
        ).prefetch_related(
            'cross_references',
            'car_models', 'car_generations', 'car_modifications',
            'truck_models', 'truck_generations', 'truck_modifications',
            'moto_models', 'moto_generations', 'moto_modifications',
            'special_models', 'special_generations', 'special_modifications',
        )
        queryset = SearchService._apply_filters(base_queryset, filters)

        normalized_vehicle = normalize_vehicle_identifier(query)
        normalized_article = normalize_article_number(query)

        ordered_ids = []
        SearchService._extend_unique(
            ordered_ids,
            SearchService._exact_product_ids(queryset, query, normalized_vehicle, normalized_article)
        )
        SearchService._extend_unique(
            ordered_ids,
            SearchService._cross_and_analog_product_ids(queryset, normalized_article)
        )
        SearchService._extend_unique(
            ordered_ids,
            SearchService._vehicle_product_ids(queryset, query, search_type, filters.get('user'))
        )

        fuzzy_results = FuzzySearchService.search_products(queryset, query, filters)
        SearchService._extend_unique(ordered_ids, [result['product'].id for result in fuzzy_results])
        SearchService._extend_unique(
            ordered_ids,
            SearchService._fallback_product_ids(queryset, query, normalized_vehicle, normalized_article)
        )

        if ordered_ids:
            return SearchService._queryset_in_order(queryset, ordered_ids)

        return Product.objects.none()

    @staticmethod
    def autocomplete(query, limit=8):
        if not query or len(query.strip()) < 2:
            return []
        return FuzzySearchService.autocomplete(query, limit)

    @staticmethod
    def search_by_vin(vin_query, exact_match=False):
        if not vin_query:
            return Product.objects.none()

        normalized_query = normalize_vehicle_identifier(vin_query)
        if exact_match:
            return Product.objects.filter(vin__iexact=normalized_query)

        fuzzy_results = FuzzySearchService.search_by_vin(normalized_query, exact_match=False)
        if fuzzy_results:
            product_ids = [product.id for product in fuzzy_results]
            return Product.objects.filter(id__in=product_ids)
        return Product.objects.filter(vin__icontains=normalized_query)

    @staticmethod
    def _exact_product_ids(queryset, query, normalized_vehicle, normalized_article):
        conditions = Q(name__iexact=query)

        if normalized_article:
            conditions |= Q(normalized_part_number=normalized_article)
            conditions |= Q(internal_code__iexact=query)
            conditions |= Q(cross_references__is_active=True, cross_references__normalized_article=normalized_article)
            conditions |= Q(
                incoming_cross_references__is_active=True,
                incoming_cross_references__normalized_article=normalized_article,
            )

        if normalized_vehicle and VIN_PATTERN.match(normalized_vehicle):
            conditions |= Q(vin__iexact=normalized_vehicle)

        return list(queryset.filter(conditions).distinct().values_list('id', flat=True)[:200])

    @staticmethod
    def _fallback_product_ids(queryset, query, normalized_vehicle, normalized_article):
        conditions = (
            Q(name__icontains=query) |
            Q(part_number__icontains=query) |
            Q(description__icontains=query) |
            Q(vin__icontains=normalized_vehicle or query)
        )

        if normalized_article:
            conditions |= Q(normalized_part_number__icontains=normalized_article)
            conditions |= Q(cross_references__is_active=True, cross_references__normalized_article__icontains=normalized_article)
            conditions |= Q(
                incoming_cross_references__is_active=True,
                incoming_cross_references__normalized_article__icontains=normalized_article,
            )

        return list(queryset.filter(conditions).distinct().values_list('id', flat=True)[:500])

    @staticmethod
    def _cross_and_analog_product_ids(queryset, normalized_article):
        if not normalized_article or len(normalized_article) < 3:
            return []

        product_ids = []
        seed_ids = list(queryset.filter(
            Q(normalized_part_number=normalized_article) |
            Q(cross_references__is_active=True, cross_references__normalized_article=normalized_article) |
            Q(incoming_cross_references__is_active=True, incoming_cross_references__normalized_article=normalized_article)
        ).distinct().values_list('id', flat=True)[:200])

        SearchService._extend_unique(product_ids, seed_ids)

        cross_refs = ProductCrossReference.objects.filter(is_active=True).filter(
            Q(normalized_article=normalized_article) |
            Q(product_id__in=seed_ids) |
            Q(analog_product_id__in=seed_ids)
        )

        related_articles = {normalized_article}
        related_product_ids = []
        for cross_ref in cross_refs:
            related_articles.add(cross_ref.normalized_article)
            related_product_ids.append(cross_ref.product_id)
            if cross_ref.analog_product_id:
                related_product_ids.append(cross_ref.analog_product_id)

        if related_articles:
            related_product_ids.extend(
                queryset.filter(normalized_part_number__in=related_articles).values_list('id', flat=True)[:500]
            )

        SearchService._extend_unique(product_ids, related_product_ids)
        return product_ids

    @staticmethod
    def _vehicle_product_ids(queryset, query, search_type, user):
        if search_type not in ('vin', 'license_plate') or not user or not user.is_authenticated:
            return []

        vehicle = SearchService._find_user_vehicle(query, search_type, user)
        if not vehicle:
            return []

        vehicle_filter = SearchService._vehicle_compatibility_filter(vehicle)
        if not vehicle_filter:
            return []

        return list(queryset.filter(vehicle_filter).distinct().values_list('id', flat=True)[:500])

    @staticmethod
    def _find_user_vehicle(query, search_type, user):
        from garage.models import Vehicle

        normalized_query = normalize_vehicle_identifier(query)
        vehicles = Vehicle.objects.filter(user=user, is_active=True)

        for vehicle in vehicles:
            value = vehicle.vin if search_type == 'vin' else vehicle.license_plate
            if normalize_vehicle_identifier(value) == normalized_query:
                return vehicle

        return None

    @staticmethod
    def _vehicle_compatibility_filter(vehicle):
        vehicle_type = vehicle.get_vehicle_type()
        type_map = {
            'cars': ('car', 'car'),
            'trucks': ('truck', 'truck'),
            'moto': ('moto', 'moto'),
            'special': ('special', 'special'),
        }
        product_type, prefix = type_map.get(vehicle_type, ('car', 'car'))

        specific_filter = Q()
        if vehicle.brand_object_id:
            specific_filter |= Q(**{f'{prefix}_brand_id': vehicle.brand_object_id})
        if vehicle.model_object_id:
            specific_filter |= Q(**{f'{prefix}_models__id': vehicle.model_object_id})
        if vehicle.generation_object_id:
            specific_filter |= Q(**{f'{prefix}_generations__id': vehicle.generation_object_id})
        if vehicle.modification_object_id:
            specific_filter |= Q(**{f'{prefix}_modifications__id': vehicle.modification_object_id})

        compatibility_filter = Q(vehicle_type='universal')
        if specific_filter:
            compatibility_filter |= Q(vehicle_type=product_type) & specific_filter
        else:
            compatibility_filter |= Q(vehicle_type=product_type)

        return compatibility_filter

    @staticmethod
    def _queryset_in_order(queryset, product_ids):
        unique_ids = []
        SearchService._extend_unique(unique_ids, product_ids)
        ordering = [
            When(pk=product_id, then=position)
            for position, product_id in enumerate(unique_ids)
        ]
        return queryset.filter(pk__in=unique_ids).distinct().annotate(
            search_order=Case(
                *ordering,
                default=len(unique_ids),
                output_field=IntegerField(),
            )
        ).order_by('search_order', '-created_at')

    @staticmethod
    def _extend_unique(target, values):
        seen = set(target)
        for value in values or []:
            if value and value not in seen:
                target.append(value)
                seen.add(value)

    @staticmethod
    def _apply_filters(queryset, filters):
        filters = filters or {}

        if price_min := filters.get('price_min'):
            queryset = queryset.filter(price__gte=price_min)

        if price_max := filters.get('price_max'):
            queryset = queryset.filter(price__lte=price_max)

        if filters.get('category'):
            queryset = queryset.filter(category__slug=filters['category'])

        if filters.get('brand'):
            queryset = queryset.filter(
                Q(car_brand__slug=filters['brand']) |
                Q(truck_brand__slug=filters['brand']) |
                Q(moto_brand__slug=filters['brand']) |
                Q(special_brand__slug=filters['brand']) |
                Q(oil_chem_brand__slug=filters['brand']) |
                Q(maintenance_brand__slug=filters['brand']) |
                Q(tire_wheel_brand__slug=filters['brand']) |
                Q(tool_brand__slug=filters['brand']) |
                Q(auto_electric_brand__slug=filters['brand']) |
                Q(product_brand__slug=filters['brand'])
            )

        if filters.get('in_stock') or (filters.get('in_stock') and filters.get('on_order')):
            queryset = queryset.filter(stock__gt=0)

        if filters.get('on_order') and not filters.get('in_stock'):
            queryset = queryset.filter(stock=0)

        if filters.get('is_original'):
            queryset = queryset.filter(is_original=True)

        if filters.get('rating'):
            queryset = queryset.annotate(
                avg_rating=Avg('reviews__rating', filter=Q(reviews__is_published=True))
            ).filter(avg_rating__gte=float(filters['rating']))

        return queryset
