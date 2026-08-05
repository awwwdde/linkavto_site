from django import template
from shop.models import CarBrand, TruckBrand, MotoBrand, SpecialBrand

register = template.Library()

@register.filter
def is_brand_category(category):
    # Проверяем, есть ли у категории связанные бренды через show_brands
    return category.show_brands