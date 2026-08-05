from rest_framework import serializers

from shop.models import Product, Category, CarouselSlide


def abs_media_url(request, field):
    """Безопасно возвращает абсолютный URL для ImageField (или None)."""
    try:
        if field and getattr(field, 'name', None):
            url = field.url
            if request is not None:
                return request.build_absolute_uri(url)
            return url
    except Exception:
        pass
    return None


class ProductCardSerializer(serializers.ModelSerializer):
    """Данные, необходимые для карточки товара (как в shop/product_card.html)."""
    image = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    has_active_sale = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'part_number',
            'price', 'old_price', 'discount',
            'image', 'url', 'stock', 'is_active',
            'is_original', 'is_new', 'is_featured',
            'average_rating', 'review_count', 'has_active_sale',
        ]

    def _request(self):
        return self.context.get('request')

    def get_image(self, obj):
        return abs_media_url(self._request(), getattr(obj, 'image', None))

    def get_url(self, obj):
        try:
            return obj.get_absolute_url()
        except Exception:
            return f'/product/{obj.slug}/'

    def get_discount(self, obj):
        try:
            return obj.get_discount()
        except Exception:
            return 0

    def get_average_rating(self, obj):
        try:
            return round(float(obj.average_rating or 0), 1)
        except Exception:
            return 0

    def get_review_count(self, obj):
        try:
            return int(obj.review_count or 0)
        except Exception:
            return 0

    def get_has_active_sale(self, obj):
        try:
            return bool(obj.has_active_sale)
        except Exception:
            return False


class CategorySerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'icon', 'image', 'url', 'parent', 'order']

    def get_image(self, obj):
        return abs_media_url(self.context.get('request'), getattr(obj, 'image', None))

    def get_url(self, obj):
        try:
            return obj.get_absolute_url()
        except Exception:
            return f'/category/{obj.slug}/'


class CarouselSlideSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = CarouselSlide
        fields = ['id', 'title', 'image', 'url', 'order']

    def get_image(self, obj):
        return abs_media_url(self.context.get('request'), getattr(obj, 'image', None))
