"""
Базовые настройки Django для avtolink проекта
"""

from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-fallback-key-only-for-dev')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'rest_framework',  # Временно отключен
    'shop',
    'orders',
    'cart',
    'checkout',
    'import_export',
    'simple_history',
    'django_celery_results',
    'accounts',
    'favorites',
    'search.apps.SearchConfig',
    'django.forms',
    'sellers.apps.SellersConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'search.middleware.SearchHistoryMiddleware',
    # CaptchaMiddleware будет добавлен в development настройках
]

ROOT_URLCONF = 'avtolink.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'shop.context_processors.categories',
                'shop.context_processors.favorites_count',
                'shop.context_processors.api_keys',
                'cart.context_processors.cart',
                'search.context_processors.search_history'
            ],
        },
    },
]

WSGI_APPLICATION = 'avtolink.wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'shop/static'),
    os.path.join(BASE_DIR, 'accounts/static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles/')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Authentication
LOGIN_URL = '/account/'  # URL для редиректа при необходимости авторизации
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'index'
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

# Cart configuration
CART_SESSION_ID = 'cart'

# Favorites configuration
FAVORITES_CONFIG = {
    'MAX_ITEMS': 100,
    'SESSION_SAVE': True,
}

# SMS настройки
SMSC_LOGIN = os.getenv('SMSC_LOGIN', 'linkavto.ru')
SMSC_PASSWORD = os.getenv('SMSC_PASSWORD', '')
SMSC_SENDER = 'LinkAvto'

# Т-Банк настройки
TBANK_TERMINAL = os.getenv('TBANK_TERMINAL', '')
TBANK_PASSWORD = os.getenv('TBANK_PASSWORD', '')
TBANK_API_URL = 'https://securepay.tinkoff.ru'

# Настройки платежной системы
PAYMENT_SYSTEM = {
    'MERCHANT_ID': 'your_merchant_id',
    'SECRET_KEY': 'your_secret_key',
    'SBP_MERCHANT_ACCOUNT': 'your_sbp_account',
    'TEST_MODE': True,
}

# Кеширование
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

CACHE_TIMEOUT = {
    'home_page': 3600,  # 1 час
    'product_blocks': 1800,  # 30 минут
}

# Celery configuration (базовые настройки)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_BROKER_URL = 'memory://'
CELERY_RESULT_BACKEND = 'django-cache'
CELERY_CACHE_BACKEND = 'django-cache'

# =============================================================================
# API Ключи внешних сервисов
# =============================================================================

# Яндекс Карты
YANDEX_MAPS_API_KEY = os.getenv('YANDEX_MAPS_API_KEY', '')


# DaData (поиск ПВЗ по геолокации)
DADATA_TOKEN = os.getenv('DADATA_TOKEN', '')


# СДЭК
CDEK_CLIENT_ID = os.getenv('CDEK_CLIENT_ID', '')
CDEK_CLIENT_SECRET = os.getenv('CDEK_CLIENT_SECRET', '')

# Почта России
RUSSIAN_POST_TOKEN = os.getenv('RUSSIAN_POST_TOKEN', '')
RUSSIAN_POST_USER_AUTH = os.getenv('RUSSIAN_POST_USER_AUTH', '')