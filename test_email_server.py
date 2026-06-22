#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Быстрый тест email на production сервере
Использует настройки production (localhost:25)
"""

import os
import sys
import django

# Устанавливаем окружение production
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avtolink.settings')
os.environ['DJANGO_ENV'] = 'production'

django.setup()

from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def test_email():
    """Тест отправки email на сервере"""
    print("="*60)
    print("TEST EMAIL NA SERVERE")
    print("="*60)
    print(f"Backend: {settings.EMAIL_BACKEND}")
    print(f"Host: {settings.EMAIL_HOST}")
    print(f"Port: {settings.EMAIL_PORT}")
    print(f"From: {settings.DEFAULT_FROM_EMAIL}")
    print("="*60)
    
    # Получаем email получателя
    if len(sys.argv) > 1:
        recipient = sys.argv[1]
    else:
        recipient = input("\nVvedite email poluchatelya: ").strip()
    
    if not recipient or '@' not in recipient:
        print("[X] Nekorrektnyy email!")
        return False
    
    try:
        # Создаем письмо
        subject = 'Test Email LinkAvto (Production Server)'
        
        text = f"""
Zdravstvuyte!

Eto testovoe pismo ot LinkAvto s production servera.

Vash testovyy kod: 123456

Server: {settings.EMAIL_HOST}
Port: {settings.EMAIL_PORT}

Esli vy poluchili eto pismo, znachit email nastroyen pravilno!

S uvazheniem,
Komanda LinkAvto
https://linkavto.ru
"""
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <div style="background: #667eea; padding: 30px; text-align: center; color: white;">
        <h1>LinkAvto</h1>
        <p>Test Email Production Server</p>
    </div>
    
    <div style="padding: 30px; border: 1px solid #e0e0e0;">
        <h2 style="color: #667eea;">Email rabotaet!</h2>
        <p>Zdravstvuyte!</p>
        <p>Eto testovoe pismo ot LinkAvto s production servera.</p>
        
        <div style="background: #f0f0f0; padding: 20px; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 0; color: #666;">Server: <strong>{settings.EMAIL_HOST}</strong></p>
            <p style="margin: 5px 0; color: #666;">Port: <strong>{settings.EMAIL_PORT}</strong></p>
        </div>
        
        <div style="background: #667eea; color: white; padding: 20px; text-align: center; border-radius: 5px;">
            <p style="margin: 0;">Vash testovyy kod:</p>
            <h1 style="margin: 10px 0; letter-spacing: 10px;">123456</h1>
        </div>
        
        <p style="color: #28a745; font-weight: bold; margin-top: 20px;">
            Esli vy poluchili eto pismo, znachit email nastroyen pravilno!
        </p>
    </div>
    
    <div style="text-align: center; padding: 20px; color: #999; font-size: 12px;">
        <p>S uvazheniem, Komanda <a href="https://linkavto.ru">LinkAvto</a></p>
    </div>
</body>
</html>
"""
        
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient]
        )
        msg.attach_alternative(html, "text/html")
        
        print(f"\nOtpravka pisma na {recipient}...")
        msg.send(fail_silently=False)
        
        print("\n" + "="*60)
        print("[OK] PISMO OTPRAVLENO USPESHNO!")
        print("="*60)
        print(f"\nProverte pochtu: {recipient}")
        print("Takzhe proverte papku 'Spam'")
        
        return True
        
    except Exception as e:
        print("\n" + "="*60)
        print("[X] OSHIBKA PRI OTPRAVKE")
        print("="*60)
        print(f"Oshibka: {type(e).__name__}")
        print(f"Soobshchenie: {e}")
        
        # Диагностика
        print("\n" + "="*60)
        print("DIAGNOSTIKA:")
        print("="*60)
        
        error_str = str(e)
        
        if "Connection" in error_str or "refused" in error_str:
            print("[!] Oshibka podklyucheniya k SMTP serveru")
            print("\nPoprobuite:")
            print("1. Proverte dostupnost SMTP:")
            print("   telnet localhost 25")
            print("\n2. Ili vernte starye nastroyki v production.py:")
            print("   EMAIL_HOST = '31.31.196.47'")
            print("   EMAIL_PORT = 25")
            
        elif "Authentication" in error_str:
            print("[!] Oshibka autentifikatsii")
            print("\nProverte:")
            print("- Pravilnost parolya")
            print("- Aktivna li uchetnaya zapis na hostinge")
            
        else:
            print("[!] Obshchaya oshibka")
            print("\nPosmotrite polnyy traceback:")
            import traceback
            traceback.print_exc()
        
        return False

if __name__ == '__main__':
    print("\n" + "="*60)
    print("LINKAVTO EMAIL TEST (PRODUCTION SERVER)")
    print("="*60)
    
    success = test_email()
    
    sys.exit(0 if success else 1)

