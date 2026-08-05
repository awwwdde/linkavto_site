from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """
    Заменяет подстроку в значении
    Использование: {{ value|replace:"old,new" }}
    """
    if not value:
        return value
    try:
        old, new = arg.split(',')
        return str(value).replace(old, new)
    except (ValueError, AttributeError):
        return value

@register.filter
def format_rating(value):
    """Форматирует рейтинг в русский формат с запятой"""
    if value is None:
        return "0,0"
    try:
        return f"{float(value):.1f}".replace('.', ',')
    except (ValueError, TypeError):
        return "0,0"

@register.filter
def get_item(dictionary, key):
    """Получает значение из словаря по ключу"""
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None


@register.filter
def split_csv(value):
    """
    Разбивает строку по запятым и возвращает список.
    Полезно для GET-параметров вида: "a,b,c".
    """
    if not value:
        return []
    try:
        return [v.strip() for v in str(value).split(',') if v.strip()]
    except Exception:
        return []