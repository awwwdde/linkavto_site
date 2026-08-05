from django.contrib import admin
from django.urls import path
from django.shortcuts import render
from django.db.models import Count, Sum
from django.utils.translation import gettext_lazy as _  # Импорт для локализации
from .models import Order


class OrderAdminDashboard(admin.ModelAdmin):
    # Метаданные для админ-панели
    verbose_name = _('Статистика заказов')
    verbose_name_plural = _('Статистика заказов')

    def get_urls(self):
        """Добавляем кастомный URL для статистики"""
        urls = super().get_urls()
        custom_urls = [
            path('stats/', self.admin_site.admin_view(self.stats_view), name='orders_stats')
        ]
        return custom_urls + urls

    def stats_view(self, request):
        """Представление для отображения статистики"""
        # Статистика по статусам заказов
        status_stats = Order.objects.values('status').annotate(
            count=Count('id'),
            total=Sum('items__price')
        ).order_by('status')

        # Перевод статусов на русский
        status_map = {
            'processing': _('В обработке'),
            'shipped': _('Отправлен'),
            'delivered': _('Доставлен'),
            'canceled': _('Отменен')
        }

        # Применяем перевод к статусам
        translated_status_stats = []
        for stat in status_stats:
            stat['status_name'] = status_map.get(stat['status'], stat['status'])
            translated_status_stats.append(stat)

        # Ежемесячная статистика
        monthly_stats = Order.objects.extra(
            select={'month': "date_trunc('month', created_at)"}
        ).values('month').annotate(
            orders=Count('id'),
            revenue=Sum('items__price')
        ).order_by('month')

        context = {
            'title': _('Статистика заказов'),
            'status_stats': translated_status_stats,
            'monthly_stats': monthly_stats,
            'opts': self.model._meta,
            **self.admin_site.each_context(request)
        }
        return render(request, 'admin/orders/stats.html', context)

    def get_model_perms(self, request):
        """Ограничиваем видимость в основном меню"""
        return {
            'add': False,
            'change': False,
            'delete': False,
            'view': request.user.is_staff
        }