from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.functional import cached_property
from django.db.models import Q

User = get_user_model()


class SearchQuery(models.Model):
    query = models.CharField(max_length=255, verbose_name="Поисковый запрос")
    results_count = models.PositiveIntegerField(default=0, verbose_name="Количество результатов")
    user = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.CASCADE,  # Меняем на CASCADE для корректного удаления
        verbose_name="Пользователь",
        related_name='search_queries'
    )
    session_key = models.CharField(max_length=40, blank=True, verbose_name="Ключ сессии")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата и время запроса")
    is_autocomplete = models.BooleanField(default=False, verbose_name="Автодополнение")
    is_vin_search = models.BooleanField(default=False, verbose_name="Поиск по VIN")
    filters = models.JSONField(default=dict, blank=True, verbose_name="Фильтры поиска")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP-адрес")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Поисковый запрос'
        verbose_name_plural = 'Поисковые запросы'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['session_key', 'created_at']),
        ]

    def __str__(self):
        return f"{self.query} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"

    @classmethod
    def get_user_history(cls, user=None, session_key=None, limit=10):
        """Получить историю поиска для пользователя или сессии"""
        queryset = cls.objects.all()

        if user and user.is_authenticated:
            queryset = queryset.filter(user=user)
        elif session_key:
            queryset = queryset.filter(session_key=session_key, user__isnull=True)
        else:
            return cls.objects.none()

        return queryset.order_by('-created_at')[:limit]

    @classmethod
    def clear_history(cls, user=None, session_key=None):
        """Очистить историю поиска"""
        if user and user.is_authenticated:
            deleted_count, _ = cls.objects.filter(user=user).delete()
            return deleted_count
        elif session_key:
            deleted_count, _ = cls.objects.filter(session_key=session_key, user__isnull=True).delete()
            return deleted_count
        return 0

    @classmethod
    def delete_single_query(cls, query_id, user=None, session_key=None):
        """Удалить один поисковый запрос"""
        try:
            if user and user.is_authenticated:
                query = cls.objects.get(id=query_id, user=user)
            elif session_key:
                query = cls.objects.get(id=query_id, session_key=session_key, user__isnull=True)
            else:
                return False

            query.delete()
            return True
        except cls.DoesNotExist:
            return False

    @classmethod
    def merge_session_history_to_user(cls, user, session_key):
        """Перенести историю из сессии в пользователя при логине"""
        if user.is_authenticated and session_key:
            cls.objects.filter(
                session_key=session_key,
                user__isnull=True
            ).update(user=user)
            return True
        return False

    @cached_property
    def display_query(self):
        if self.is_vin_search:
            return f"VIN: {self.query[:4]}...{self.query[-4:]}"
        return self.query

    def save(self, *args, **kwargs):
        # Предотвращаем дублирование последних запросов
        recent_queries = SearchQuery.objects.filter(
            Q(user=self.user) if self.user else Q(session_key=self.session_key),
            query=self.query
        ).order_by('-created_at')[:1]

        if not recent_queries or (timezone.now() - recent_queries[0].created_at).total_seconds() > 300:
            super().save(*args, **kwargs)
            
            # Ограничиваем историю до 10 записей после сохранения
            self.limit_history_to_10()

    def limit_history_to_10(self):
        """Ограничить историю поиска до 10 последних записей"""
        if self.user and self.user.is_authenticated:
            # Получаем все записи пользователя, отсортированные по дате
            all_queries = SearchQuery.objects.filter(user=self.user).order_by('-created_at')
            if all_queries.count() > 10:
                # Удаляем старые записи, оставляя только 10 последних
                queries_to_delete = all_queries[10:]
                SearchQuery.objects.filter(id__in=[q.id for q in queries_to_delete]).delete()
        elif self.session_key:
            # Получаем все записи сессии, отсортированные по дате
            all_queries = SearchQuery.objects.filter(session_key=self.session_key, user__isnull=True).order_by('-created_at')
            if all_queries.count() > 10:
                # Удаляем старые записи, оставляя только 10 последних
                queries_to_delete = all_queries[10:]
                SearchQuery.objects.filter(id__in=[q.id for q in queries_to_delete]).delete()