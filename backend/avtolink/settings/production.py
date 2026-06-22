"""
Настройки для production сервера
"""

from .base import *
import ssl

# SECURITY: Отключаем debug в production
# DEBUG = False
DEBUG = True

# НЕ добавляем CaptchaMiddleware в production! Он вызывает проблемы
# Если капча нужна, добавьте условную логику в middleware

# База данных для production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
    }
}

# Настройка для отключения проверки SSL в Django
ssl._create_default_https_context = ssl._create_unverified_context

# Security настройки для production
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Логирование для production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/linkavto/django.log',  # Путь для production логов
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'django.db.backends': {
            'level': 'WARNING',
            'handlers': ['console'],
        },
        'orders': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
        },
        'django.server': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'django.core.mail': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
        'accounts': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
        'accounts.views': {
            'level': 'INFO',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'WARNING',
    },
}

# Настройки Celery для production
CELERY_TASK_ALWAYS_EAGER = False
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_CACHE_BACKEND = 'django-cache'

# Увеличение лимитов для загрузки файлов
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000
