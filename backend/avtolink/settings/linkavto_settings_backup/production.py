"""
Настройки для production сервера
"""

from .base import *
import ssl
from dotenv import load_dotenv
load_dotenv()

# SECURITY: Отключаем debug в production
DEBUG = False

# Разрешенные хосты для production
ALLOWED_HOSTS = ['linkavto.ru', 'www.linkavto.ru', '.linkavto.ru', '89.23.97.97',]

# НЕ добавляем CaptchaMiddleware в production! Он вызывает проблемы
# Если капча нужна, добавьте условную логику в middleware

# База данных для production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DB_NAME', 'avtolink_django'),
        'USER': os.getenv('DB_USER', 'avtolink_django'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# Настройки email для production (reg.ru)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', '31.31.196.47')
# IP адрес из DNS записей reg.ru
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 25))
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'linkavto@linkavto.ru')

EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('EMAIL_HOST_USER', 'linkavto@linkavto.ru')
SERVER_EMAIL = os.getenv('EMAIL_HOST_USER', 'linkavto@linkavto.ru')
EMAIL_TIMEOUT = 30

# Дополнительные настройки SSL для reg.ru
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None
EMAIL_SSL_CERT_REQS = ssl.CERT_NONE  # Игнорируем проверку SSL сертификата

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
