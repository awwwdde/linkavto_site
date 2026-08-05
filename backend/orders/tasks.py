# orders/tasks.py
from django.conf import settings


def send_order_notifications_sync(order_id):
    """Синхронная версия задачи"""
    from django.core.mail import send_mail
    from .models import Order

    order = Order.objects.get(id=order_id)

    # Отправка клиенту
    send_mail(
        f'Заказ #{order.id} принят',
        f'Статус: {order.get_status_display()}',
        'noreply@example.com',
        [order.email],
        fail_silently=True,
    )


# Для production используем Celery, для разработки - синхронный вызов
if settings.CELERY_TASK_ALWAYS_EAGER:
    send_order_notifications = send_order_notifications_sync
else:
    from celery import shared_task


    @shared_task
    def send_order_notifications(order_id):
        send_order_notifications_sync(order_id)