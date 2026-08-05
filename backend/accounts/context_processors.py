"""
Context processors для accounts app
"""
from django.conf import settings


def pochta_widget_settings(request):
    """
    Добавляет настройки виджетов доставки в контекст всех шаблонов
    """
    return {
        'POCHTA_WIDGET_ID': settings.POCHTA_WIDGET_ID,
        'YANDEX_DELIVERY_TOKEN': settings.YANDEX_DELIVERY_TOKEN,
    }

