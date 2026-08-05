"""Context processors for garage app"""


def garage_count(request):
    """Добавляет количество пользовательских транспортных средств в контекст"""
    if request.user.is_authenticated:
        from .models import Vehicle
        vehicles_count = Vehicle.objects.filter(
            user=request.user,
            is_active=True
        ).count()
        return {'garage_vehicles_count': vehicles_count}
    return {'garage_vehicles_count': 0}
