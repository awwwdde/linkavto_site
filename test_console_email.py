#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест отправки email через Console Backend
Письмо выведется в консоль, а не отправится реально
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avtolink.settings')
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.conf import settings

print("="*60)
print("TEST CONSOLE EMAIL BACKEND")
print("="*60)
print(f"Backend: {settings.EMAIL_BACKEND}")
print("="*60)

# Создаем тестовое письмо
subject = 'Test Email from LinkAvto'
text_content = """
Zdravstvuyte!

Eto testovoe pismo ot LinkAvto.

Vash kod podtverzhdeniya: 123456

S uvazheniem,
Komanda LinkAvto
"""

html_content = """
<html>
<body style="font-family: Arial, sans-serif;">
    <h2 style="color: #0066cc;">LinkAvto</h2>
    <p>Zdravstvuyte!</p>
    <p>Eto testovoe pismo ot LinkAvto.</p>
    <div style="background: #f0f0f0; padding: 20px; text-align: center;">
        <h1 style="font-size: 32px; letter-spacing: 10px;">123456</h1>
    </div>
    <p>S uvazheniem,<br>Komanda LinkAvto</p>
</body>
</html>
"""

from_email = settings.DEFAULT_FROM_EMAIL
to_email = 'test@example.com'

msg = EmailMultiAlternatives(
    subject=subject,
    body=text_content,
    from_email=from_email,
    to=[to_email]
)
msg.attach_alternative(html_content, "text/html")

print("\nOtpravka pisma...")
print(f"Ot: {from_email}")
print(f"Komu: {to_email}")
print("="*60)

try:
    msg.send()
    print("\n[OK] Pismo 'otpravleno' (vyvedeno v konsol vyshe)")
    print("\nPismo dolzhno byt vyvedeno v konsoli!")
except Exception as e:
    print(f"\n[X] Oshibka: {e}")
    import traceback
    traceback.print_exc()

print("="*60)

