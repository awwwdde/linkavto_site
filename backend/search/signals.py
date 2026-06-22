from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from shop.models import Product
from .services import update_search_index


@receiver(post_save, sender=Product)
def update_product_on_save(sender, instance, **kwargs):
    update_search_index(instance)


@receiver(post_delete, sender=Product)
def delete_product_from_index(sender, instance, **kwargs):
    remove_from_search_index(instance)
