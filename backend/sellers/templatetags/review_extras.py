from django import template

register = template.Library()

@register.filter
def get_attribute(obj, attr):
    """Получить атрибут объекта по имени"""
    return getattr(obj, attr, None)

@register.filter
def get_item(dictionary, key):
    """Получить элемент из словаря"""
    return dictionary.get(key, 0)