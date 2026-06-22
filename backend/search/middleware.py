# для автоматического логирования поиска

from django.utils.deprecation import MiddlewareMixin
from .models import SearchQuery
from django.utils import timezone
from .services import SearchService


class SearchHistoryMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Убрали автоматическое сохранение из middleware
        # Теперь история сохраняется только при клике на элемент автоподстановки
        pass

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

    def is_vin_query(self, query):
        return len(query) in (17, 20) and query.isalnum()
