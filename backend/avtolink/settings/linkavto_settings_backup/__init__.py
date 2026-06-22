# Автоматический выбор настроек на основе окружения
import os

# По умолчанию используем development настройки
environment = os.environ.get('DJANGO_ENV', 'development')

if environment == 'production':
    from .production import *
elif environment == 'development':
    from .development import *
else:
    from .development import *
