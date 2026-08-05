import re
from typing import Any, Dict, List

from rapidfuzz import fuzz

from shop.models import Product, ProductCrossReference, normalize_article_number


CYRILLIC_TO_LATIN = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
}


def transliterate_cyrillic(text: str) -> str:
    return ''.join(CYRILLIC_TO_LATIN.get(char, char) for char in text.lower())


class FuzzySearchService:
    MIN_SIMILARITY_THRESHOLD = 60
    VIN_SIMILARITY_THRESHOLD = 70
    PART_NUMBER_SIMILARITY_THRESHOLD = 70
    NAME_SIMILARITY_THRESHOLD = 60

    @staticmethod
    def search_products(queryset, query: str, filters: Dict = None) -> List[Dict[str, Any]]:
        if not query or len(query.strip()) < 2:
            return []
        return FuzzySearchService._fuzzy_search_products(queryset, query.strip())

    @staticmethod
    def autocomplete(query: str, limit: int = 8) -> List[Dict[str, Any]]:
        if not query or len(query.strip()) < 2:
            return []

        products = Product.objects.filter(is_active=True).values(
            'id', 'name', 'part_number', 'normalized_part_number', 'vin', 'slug'
        )
        return FuzzySearchService._fuzzy_autocomplete(products, query.strip(), limit)

    @staticmethod
    def _detect_search_type(query: str) -> str:
        normalized_query = normalize_article_number(query)
        if re.match(r'^[A-Z0-9]{17}$', normalized_query):
            return 'vin'
        if re.match(r'^[A-Z0-9]{3,}$', normalized_query):
            return 'part_number'
        return 'name'

    @staticmethod
    def _fuzzy_search_products(products, query: str) -> List[Dict[str, Any]]:
        results = []
        normalized_query = normalize_article_number(query)
        transliterated_query = transliterate_cyrillic(query)

        for product in products:
            scores = []

            if product.vin:
                normalized_vin = normalize_article_number(product.vin)
                vin_score = fuzz.ratio(normalized_query, normalized_vin)
                if vin_score >= FuzzySearchService.VIN_SIMILARITY_THRESHOLD:
                    scores.append(('vin', vin_score, product.vin))

            if product.part_number:
                normalized_part = getattr(product, 'normalized_part_number', '') or normalize_article_number(product.part_number)
                part_score = max(
                    fuzz.ratio(query.upper(), product.part_number.upper()),
                    fuzz.ratio(normalized_query, normalized_part),
                    fuzz.partial_ratio(normalized_query, normalized_part),
                )
                if part_score >= FuzzySearchService.PART_NUMBER_SIMILARITY_THRESHOLD:
                    scores.append(('part_number', part_score, product.part_number))

            cross_references = getattr(product, '_prefetched_objects_cache', {}).get('cross_references')
            if cross_references is None:
                cross_references = product.cross_references.filter(is_active=True)

            for cross_reference in cross_references:
                cross_score = max(
                    fuzz.ratio(normalized_query, cross_reference.normalized_article),
                    fuzz.partial_ratio(normalized_query, cross_reference.normalized_article),
                )
                if cross_score >= FuzzySearchService.PART_NUMBER_SIMILARITY_THRESHOLD:
                    scores.append(('cross_reference', cross_score, cross_reference.article_number))

            if product.name:
                name_scores = [
                    fuzz.ratio(query.lower(), product.name.lower()),
                    fuzz.partial_ratio(query.lower(), product.name.lower()),
                    fuzz.token_sort_ratio(query.lower(), product.name.lower()),
                    fuzz.token_set_ratio(query.lower(), product.name.lower()),
                ]

                if transliterated_query != query.lower():
                    name_scores.extend([
                        fuzz.ratio(transliterated_query, product.name.lower()),
                        fuzz.partial_ratio(transliterated_query, product.name.lower()),
                        fuzz.token_sort_ratio(transliterated_query, product.name.lower()),
                        fuzz.token_set_ratio(transliterated_query, product.name.lower()),
                    ])

                name_score = max(name_scores)
                if product.name.lower().startswith(query.lower()):
                    name_score = min(100, name_score + 10)
                if name_score >= FuzzySearchService.NAME_SIMILARITY_THRESHOLD:
                    scores.append(('name', name_score, product.name))

            if scores:
                match_type, score, matched_text = max(scores, key=lambda item: item[1])
                results.append({
                    'product': product,
                    'score': score,
                    'match_type': match_type,
                    'matched_text': matched_text,
                    'query': query,
                })

        type_priority = {'vin': 0, 'part_number': 1, 'cross_reference': 2, 'name': 3}
        results.sort(key=lambda item: (type_priority.get(item['match_type'], 9), -item['score']))
        return results

    @staticmethod
    def _fuzzy_autocomplete(products, query: str, limit: int) -> List[Dict[str, Any]]:
        suggestions = []
        added_values = set()
        normalized_query = normalize_article_number(query)
        transliterated_query = transliterate_cyrillic(query)
        search_items = []

        for product in products:
            if product['vin']:
                search_items.append({
                    'value': product['vin'],
                    'normalized_value': normalize_article_number(product['vin']),
                    'display': f"VIN: {product['vin']}",
                    'type': 'vin',
                    'product_id': product['id'],
                    'slug': product['slug'],
                })

            if product['part_number']:
                search_items.append({
                    'value': product['part_number'],
                    'normalized_value': product.get('normalized_part_number') or normalize_article_number(product['part_number']),
                    'display': f"Артикул: {product['part_number']}",
                    'type': 'part_number',
                    'product_id': product['id'],
                    'slug': product['slug'],
                })

            if product['name']:
                search_items.append({
                    'value': product['name'],
                    'display': product['name'],
                    'type': 'name',
                    'product_id': product['id'],
                    'slug': product['slug'],
                })

        cross_references = ProductCrossReference.objects.filter(
            is_active=True,
            product__is_active=True,
        ).select_related('product', 'analog_product')[:5000]

        for cross_reference in cross_references:
            target_product = cross_reference.analog_product or cross_reference.product
            brand = f"{cross_reference.brand} " if cross_reference.brand else ""
            search_items.append({
                'value': cross_reference.article_number,
                'normalized_value': cross_reference.normalized_article,
                'display': f"Кросс: {brand}{cross_reference.article_number}",
                'type': 'cross_reference',
                'product_id': target_product.id,
                'slug': target_product.slug,
            })

        for item in search_items:
            dedupe_key = (item['type'], item['value'], item['slug'])
            if dedupe_key in added_values:
                continue

            if item['type'] in ('vin', 'part_number', 'cross_reference') and item.get('normalized_value'):
                scores = [
                    fuzz.ratio(normalized_query, item['normalized_value']),
                    fuzz.partial_ratio(normalized_query, item['normalized_value']),
                ]
            else:
                scores = [
                    fuzz.ratio(query.lower(), item['value'].lower()),
                    fuzz.partial_ratio(query.lower(), item['value'].lower()),
                    fuzz.token_sort_ratio(query.lower(), item['value'].lower()),
                    fuzz.token_set_ratio(query.lower(), item['value'].lower()),
                ]
                if transliterated_query != query.lower():
                    scores.extend([
                        fuzz.ratio(transliterated_query, item['value'].lower()),
                        fuzz.partial_ratio(transliterated_query, item['value'].lower()),
                        fuzz.token_sort_ratio(transliterated_query, item['value'].lower()),
                        fuzz.token_set_ratio(transliterated_query, item['value'].lower()),
                    ])

            score = max(scores)
            if item['type'] == 'name' and item['value'].lower().startswith(query.lower()):
                score = min(100, score + 15)

            min_threshold = {
                'vin': FuzzySearchService.VIN_SIMILARITY_THRESHOLD,
                'part_number': FuzzySearchService.PART_NUMBER_SIMILARITY_THRESHOLD,
                'cross_reference': FuzzySearchService.PART_NUMBER_SIMILARITY_THRESHOLD,
                'name': FuzzySearchService.NAME_SIMILARITY_THRESHOLD,
            }.get(item['type'], FuzzySearchService.MIN_SIMILARITY_THRESHOLD)

            if score >= min_threshold:
                suggestions.append({
                    'id': item['product_id'],
                    'slug': item['slug'],
                    'text': item['display'],
                    'value': item['value'],
                    'type': item['type'],
                    'score': score,
                })
                added_values.add(dedupe_key)

        type_priority = {'vin': 0, 'part_number': 1, 'cross_reference': 2, 'name': 3}
        suggestions.sort(key=lambda item: (type_priority.get(item['type'], 9), -item['score']))
        return suggestions[:limit]

    @staticmethod
    def search_by_vin(vin_query: str, exact_match: bool = False):
        if not vin_query:
            return Product.objects.none()

        normalized_query = normalize_article_number(vin_query)
        if exact_match:
            return Product.objects.filter(vin__iexact=normalized_query)

        products = Product.objects.filter(vin__isnull=False, is_active=True)
        results = []
        for product in products:
            normalized_vin = normalize_article_number(product.vin)
            score = fuzz.ratio(normalized_query, normalized_vin)
            if score >= FuzzySearchService.VIN_SIMILARITY_THRESHOLD:
                results.append((product, score))

        results.sort(key=lambda item: item[1], reverse=True)
        return [product for product, _ in results]
