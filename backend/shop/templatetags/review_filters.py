from django import template

register = template.Library()

@register.filter
def replace(value, arg):
    """
    Заменяет подстроку в значении
    Использование: {{ value|replace:"old,new" }}
    """
    old, new = arg.split(',')
    return value.replace(old, new)

@register.filter
def format_rating(value):
    """Форматирует рейтинг в русский формат с запятой"""
    if value is None:
        return "0,0"
    return f"{float(value):.1f}".replace('.', ',')