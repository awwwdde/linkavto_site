# ===== EMAIL CONFIGURATION =====
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.reg.ru'  # Правильный хост reg.ru!
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_USE_SSL = False
EMAIL_HOST_USER = 'linkavto@linkavto.ru'  # Ваш реальный email!
EMAIL_HOST_PASSWORD = 'qK4gF2vX3btF4jS3'  # Пароль от почты!
DEFAULT_FROM_EMAIL = 'linkavto@linkavto.ru'
SERVER_EMAIL = 'linkavto@linkavto.ru'
EMAIL_TIMEOUT = 30


