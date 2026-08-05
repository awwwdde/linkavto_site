"""
Базовые настройки Django для avtolink проекта
"""

from pathlib import Path
import os

from pathlib import Path
import environ

# /opt/linkavto/avtolink/settings/production.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # => /opt/linkavto

env = environ.Env(
    DEBUG=(bool, False),
)

# читаем .env (важно: путь абсолютный или через BASE_DIR)
env.read_env(BASE_DIR / ".env")

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")  # без default
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["linkavto.ru", "www.linkavto.ru"])

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
SMSC_LOGIN = env('SMSC_LOGIN'),
SMSC_PASSWORD = env('SMSC_PASSWORD'),
SMSC_SENDER = env('SMSC_SENDER'),

# Т-Банк настройки
TBANK_TERMINAL = env('TBANK_TERMINAL'),
TBANK_PASSWORD = env('TBANK_PASSWORD'),
TBANK_API_URL = env('TBANK_API_URL'),

# Настройки платежной системы
PAYMENT_SYSTEM = {
    'MERCHANT_ID':env('PAYMENT_MERCHANT_ID'),
    'SECRET_KEY': env('PAYMENT_SECRET_KEY'),
    'SBP_MERCHANT_ACCOUNT': env('PAYMENT_SBP_ACCOUNT'),
    'TEST_MODE': env('PAYMENT_TEST_MODE'),
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
YANDEX_MAPS_API_KEY = env('YANDEX_MAPS_API_KEY')

# DaData (поиск ПВЗ по геолокации)
DADATA_TOKEN = env('DADATA_TOKEN')

# СДЭК
CDEK_CLIENT_ID = env('CDEK_CLIENT_ID')
CDEK_CLIENT_SECRET = env('CDEK_CLIENT_SECRET')

# Почта России
RUSSIAN_POST_TOKEN = env('RUSSIAN_POST_TOKEN')
RUSSIAN_POST_USER_AUTH = env('RUSSIAN_POST_USER_AUTH')

# Дополнительные настройки SSL для reg.ru
import ssl
EMAIL_SSL_CERTFILE = None
EMAIL_SSL_KEYFILE = None
EMAIL_SSL_CERT_REQS = ssl.CERT_NONE  # Игнорируем проверку SSL сертификата

# Email settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)

EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_USE_SSL = env.bool("EMAIL_USE_SSL", default=False)

EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = env("SERVER_EMAIL")
EMAIL_TIMEOUT = env.int("EMAIL_TIMEOUT", default=30)
