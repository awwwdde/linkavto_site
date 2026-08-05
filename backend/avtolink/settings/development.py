"""
Настройки для локальной разработки
"""

from .base import *
import os

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Разрешенные хосты для разработки
ALLOWED_HOSTS = ['linkavto.ru', 'www.linkavto.ru', '127.0.0.1', 'localhost', '5.129.249.185', '.linkavto.ru']

# CaptchaMiddleware: по умолчанию отключаем в локальной разработке,
# чтобы не блокировать разработку/тестирование фильтров. При необходимости
# можно включить, задав ENABLE_CAPTCHA=1.
if os.environ.get('ENABLE_CAPTCHA') == '1':
    MIDDLEWARE.append('shop.middleware.CaptchaMiddleware')

# База данных для разработки
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ВРЕМЕННО: Тестируем SMTP reg.ru локально
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = '31.31.196.47'
EMAIL_PORT = 25
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'linkavto@linkavto.ru'
EMAIL_HOST_PASSWORD = 'qK4gF2vX3btF4jS3'
DEFAULT_FROM_EMAIL = 'linkavto@linkavto.ru'
SERVER_EMAIL = 'linkavto@linkavto.ru'
EMAIL_TIMEOUT = 30

# Дополнительные настройки SSL для reg.ru
import ssl
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None
EMAIL_SSL_CERT_REQS = ssl.CERT_NONE

# Логирование для разработки
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'level': 'INFO',
            'handlers': ['console'],
        },
        'orders': {
            'level': 'INFO',
            'handlers': ['console'],
        },
        'django.server': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'django.core.mail': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
        'accounts': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
        'accounts.views': {
            'level': 'DEBUG',
            'handlers': ['console', 'file'],
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}


# ============================================================================
# REST API + CORS (только локальная разработка, для React-фронтенда)
# ============================================================================
INSTALLED_APPS += [
    'rest_framework',
    'corsheaders',
    'api',
]

# corsheaders middleware должен стоять как можно выше
MIDDLEWARE.insert(0, 'corsheaders.middleware.CorsMiddleware')

CORS_ALLOWED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 24,
}
