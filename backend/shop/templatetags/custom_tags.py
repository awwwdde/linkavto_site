from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(str(key), 0)

@register.filter
def has_image(image_field):
    """Безопасная проверка наличия изображения"""
    if not image_field:
        return False
    try:
        return bool(image_field.name)
    except (ValueError, AttributeError):
        return False

@register.filter
def safe_image_url(image_field):
    """Безопасное получение URL изображения"""
    if not image_field:
        return None
    try:
        return image_field.url
    except (ValueError, AttributeError):
        return None