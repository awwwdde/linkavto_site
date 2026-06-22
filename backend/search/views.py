import re
import logging
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .services import SearchService
from .models import SearchQuery
from .serializers import SearchHistorySerializer

logger = logging.getLogger(__name__)

User = get_user_model()

# VIN-шаблон: 17 символов, буквы и цифры
# Стандартный VIN исключает I, O, Q, но в базе могут быть и такие
VIN_PATTERN = re.compile(r'^[A-Z0-9]{17}$', re.IGNORECASE)


@require_GET
def search_view(request):
    query = request.GET.get('q', '').strip()
    page_number = request.GET.get('page', 1)
    sort = request.GET.get('sort', '')

    # Нормализуем запрос для VIN (убираем пробелы и дефисы)
    search_type = SearchService.detect_search_type(query)
    
    # Определяем VIN-поиск
    is_vin_search = search_type == 'vin'
    is_plate_search = search_type == 'license_plate'

    filters = {
        'category': request.GET.get('category'),
        'brand': request.GET.get('brand'),
        'price_min': request.GET.get('price_min'),
        'price_max': request.GET.get('price_max'),
        'in_stock': request.GET.get('in_stock') == 'on',
        'on_order': request.GET.get('on_order') == 'on',
        'rating': request.GET.get('rating'),
        'is_vin_search': is_vin_search,
        'is_plate_search': is_plate_search,
    }

    # Используем нормализованный query для VIN поиска
    service_filters = filters.copy()
    service_filters['search_type'] = search_type
    service_filters['user'] = request.user
    
    # Поиск
    results = SearchService.search_products(query, service_filters)

    # Сортировка
    if sort:
        results = results.order_by(sort)

    paginator = Paginator(results, 20)
    page_obj = paginator.get_page(page_number)

    history_queries = SearchQuery.get_user_history(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key
    )

    return render(request, 'search/results.html', {
        'results': page_obj,
        'query': query,
        'filters': filters,
        'sort': sort,
        'is_vin_search': is_vin_search,
        'is_plate_search': is_plate_search,
        'search_type': search_type,
        'history_queries': history_queries
    })


@require_GET
def autocomplete_view(request):
    query = request.GET.get('q', '').strip()
    print(f"DEBUG: Autocomplete view called with query: '{query}'")
    suggestions = SearchService.autocomplete(query)
    print(f"DEBUG: Found {len(suggestions)} suggestions: {suggestions}")
    return render(request, 'search/autocomplete.html', {'suggestions': suggestions})


@require_POST
def clear_search_history(request):
    deleted_count = SearchQuery.clear_history(
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key
    )
    return JsonResponse({'success': True, 'deleted_count': deleted_count})


@require_POST
def delete_search_query(request, query_id):
    success = SearchQuery.delete_single_query(
        query_id=query_id,
        user=request.user if request.user.is_authenticated else None,
        session_key=request.session.session_key
    )
    return JsonResponse({'success': success})


class SearchHistoryAPIView(APIView):
    def get(self, request):
        print(f"DEBUG API: user={request.user}, authenticated={request.user.is_authenticated}")
        print(f"DEBUG API: session_key={request.session.session_key}")
        print(f"DEBUG API: session data={dict(request.session)}")
        
        history = SearchQuery.get_user_history(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key
        )
        print(f"DEBUG API: history count={history.count()}")
        
        serializer = SearchHistorySerializer(history, many=True)
        print(f"DEBUG API: serialized data={serializer.data}")
        return Response(serializer.data)

    def delete(self, request):
        deleted_count = SearchQuery.clear_history(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key
        )
        return Response(
            {'success': deleted_count > 0, 'deleted_count': deleted_count},
            status=status.HTTP_200_OK
        )


@require_POST
def save_search_selection(request):
    """Сохранить выбранный элемент автоподстановки в историю"""
    try:
        import json
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        selected_text = data.get('text', '').strip()
        selected_type = data.get('type', 'name')
        
        if not selected_text:
            return JsonResponse({'success': False, 'error': 'No text provided'})
        
        # Убеждаемся, что у нас есть session_key
        if not request.session.session_key:
            request.session.create()
        
        # Определяем, является ли это VIN поиском
        is_vin = selected_type == 'vin'
        
        # Создаем запись в истории
        SearchQuery.objects.create(
            query=selected_text,
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key or '',
            ip_address=get_client_ip(request),
            is_vin_search=is_vin,
            is_autocomplete=True,
            results_count=1
        )
        
        # Ограничиваем историю до 10 записей
        limit_history_to_10(
            user=request.user if request.user.is_authenticated else None,
            session_key=request.session.session_key
        )
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        print(f"Error saving search selection: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


def get_client_ip(request):
    """Получить IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


def limit_history_to_10(user=None, session_key=None):
    """Ограничить историю поиска до 10 последних записей"""
    if user and user.is_authenticated:
        # Получаем все записи пользователя, отсортированные по дате
        all_queries = SearchQuery.objects.filter(user=user).order_by('-created_at')
        if all_queries.count() > 10:
            # Удаляем старые записи, оставляя только 10 последних
            queries_to_delete = all_queries[10:]
            SearchQuery.objects.filter(id__in=[q.id for q in queries_to_delete]).delete()
    elif session_key:
        # Получаем все записи сессии, отсортированные по дате
        all_queries = SearchQuery.objects.filter(session_key=session_key, user__isnull=True).order_by('-created_at')
        if all_queries.count() > 10:
            # Удаляем старые записи, оставляя только 10 последних
            queries_to_delete = all_queries[10:]
            SearchQuery.objects.filter(id__in=[q.id for q in queries_to_delete]).delete()
