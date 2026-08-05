# shop/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.template.loader import render_to_string
from orders.models import Payment
from django.db.models.signals import post_save, post_delete
from .models import Product
from django.core.cache import cache



@receiver(post_save, sender=Payment)
def send_payment_notification(sender, instance, created, **kwargs):
    if instance.status == 'succeeded':
        subject = 'Ваш заказ оплачен'
        message = render_to_string('shop/emails/payment_success.html', {
            'order': instance.order,
            'payment': instance
        })
        recipient = instance.order.email
        send_mail(
            subject,
            message,
            'noreply@yourstore.com',
            [recipient],
            html_message=message
        )



@receiver([post_save, post_delete], sender=Product)
def clear_home_cache(sender, **kwargs):
    """Очистка кэша главной страницы при изменении товаров"""
    cache_keys = ['home_new_products', 'home_sale_products',
                  'home_popular_products', 'home_featured_products',
                  'home_bestsellers']
    for key in cache_keys:
        cache.delete(key)