"""
Настройки для локальной разработки
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Разрешенные хосты для разработки
ALLOWED_HOSTS = ['linkavto.ru', 'www.linkavto.ru', '127.0.0.1', 'localhost', '5.129.249.185', '.linkavto.ru']

# Добавляем CaptchaMiddleware для тестирования
MIDDLEWARE.append('shop.middleware.CaptchaMiddleware')

# База данных для разработки
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Настройки email для разработки (консольный backend)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

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
