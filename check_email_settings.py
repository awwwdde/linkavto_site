#!/usr/bin/env python
"""
Скрипт для проверки используемых настроек email
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avtolink.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("ТЕКУЩИЕ НАСТРОЙКИ EMAIL")
print("=" * 60)

# Определяем окружение
env = os.environ.get('DJANGO_ENV', 'development')
if env == 'production':
    env_name = "PRODUCTION"
    settings_file = "avtolink/settings/production.py"
else:
    env_name = "DEVELOPMENT"
    settings_file = "avtolink/settings/development.py"

print(f"Okruzhenie: {env_name}")
print(f"DJANGO_ENV: {os.environ.get('DJANGO_ENV', 'NE USTANOVLEN (ispolzuetsya development)')}")
print(f"Fail nastroek: {settings_file}")
print(f"SETTINGS_MODULE: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
print("=" * 60)
print(f"Email Backend: {settings.EMAIL_BACKEND}")
print(f"SMTP Host: {settings.EMAIL_HOST}")
print(f"SMTP Port: {settings.EMAIL_PORT}")
print(f"Use SSL: {settings.EMAIL_USE_SSL}")
print(f"Use TLS: {settings.EMAIL_USE_TLS}")
print(f"Host User: {settings.EMAIL_HOST_USER}")
print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
print(f"Timeout: {settings.EMAIL_TIMEOUT}")
print("=" * 60)

# Рекомендации
print("\nSPRAVKA:")
if 'mail.linkavto.ru' in settings.EMAIL_HOST:
    print("[OK] Ispolzuetsya domennoe imya mail.linkavto.ru")
else:
    print("[!] Ispolzuetsya IP adres vmesto domennogo imeni")

if settings.EMAIL_PORT == 465 and settings.EMAIL_USE_SSL:
    print("[OK] Nastroyki: SSL na portu 465")
elif settings.EMAIL_PORT == 587 and settings.EMAIL_USE_TLS:
    print("[OK] Nastroyki: TLS na portu 587")
elif settings.EMAIL_PORT == 25:
    print("[!] Nastroyki: nezashchishchennoe soedinenie na portu 25")
else:
    print("[X] Nestandartnye nastroyki SSL/TLS")

print("\nDlya izmeneniya okruzheniya:")
print("   Windows: set DJANGO_ENV=production")
print("   Linux:   export DJANGO_ENV=production")
print("=" * 60)

