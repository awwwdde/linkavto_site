from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import ProductReview, SellerReviewSummary


@receiver(post_save, sender=ProductReview)
@receiver(post_delete, sender=ProductReview)
def update_review_statistics(sender, instance, **kwargs):
    """Обновление статистики при изменении отзывов"""
    try:
        seller = instance.product.seller
        summary = SellerReviewSummary.objects.get(seller=seller)
        summary.update_statistics()
    except SellerReviewSummary.DoesNotExist:
        pass
    except Exception as e:
        # Логируем ошибку, но не прерываем выполнение
        print(f"Error updating review statistics: {e}")


@receiver(post_save, sender=ProductReview)
def update_product_rating(sender, instance, **kwargs):
    """Обновление рейтинга товара при изменении отзывов"""
    if instance.status == 'approved':
        from .services import ReviewService
        ReviewService.calculate_product_rating(instance.product)
