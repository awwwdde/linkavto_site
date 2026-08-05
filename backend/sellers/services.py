# services.py
from django.utils import timezone
from django.db import transaction
from .models import ProductReview, SellerReviewSummary

class ReviewService:
    @staticmethod
    def create_review(order, product, user, rating, comment, **kwargs):
        """Создание нового отзыва"""
        with transaction.atomic():
            review = ProductReview.objects.create(
                order=order,
                product=product,
                user=user,
                rating=rating,
                comment=comment,
                advantages=kwargs.get('advantages', ''),
                disadvantages=kwargs.get('disadvantages', ''),
                title=kwargs.get('title', ''),
                ip_address=kwargs.get('ip_address'),
                is_verified_purchase=True  # Так как отзыв из заказа
            )

            # Обновляем статистику продавца
            summary, created = SellerReviewSummary.objects.get_or_create(seller=product.seller)
            summary.update_statistics()

            return review

    @staticmethod
    def calculate_product_rating(product):
        """Пересчет рейтинга товара"""
        reviews = ProductReview.objects.filter(
            product=product,
            status='approved'
        )

        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        review_count = reviews.count()

        product.rating = avg_rating
        product.review_count = review_count
        product.save()

        return avg_rating, review_count

    @staticmethod
    def get_review_recommendations(seller):
        """Получение рекомендаций по улучшению отзывов"""
        summary = SellerReviewSummary.objects.get(seller=seller)
        recommendations = []

        if summary.response_rate < 80:
            recommendations.append({
                'type': 'response_rate',
                'title': 'Увеличьте процент ответов на отзывы',
                'description': f'Текущий процент ответов: {summary.response_rate}%',
                'priority': 'high'
            })

        if summary.average_rating < 4.0:
            recommendations.append({
                'type': 'low_rating',
                'title': 'Улучшите средний рейтинг',
                'description': f'Текущий средний рейтинг: {summary.average_rating}',
                'priority': 'high'
            })

        # Анализ негативных отзывов
        negative_reviews = ProductReview.objects.filter(
            product__seller=seller,
            rating__lte=2,
            status='approved'
        ).count()

        if negative_reviews > 5:
            recommendations.append({
                'type': 'negative_reviews',
                'title': 'Обратите внимание на негативные отзывы',
                'description': f'Количество негативных отзывов: {negative_reviews}',
                'priority': 'medium'
            })

        return recommendations