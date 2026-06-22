#!/usr/bin/env python
"""
Скрипт для тестирования отправки email через Django settings
Запуск: python test_email.py
"""

import os
import django

# Настройка Django окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avtolink.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

def test_email():
    """Тест отправки email"""
    print("=" * 60)
    print("ТЕСТИРОВАНИЕ ОТПРАВКИ EMAIL")
    print("=" * 60)
    print(f"Email Backend: {settings.EMAIL_BACKEND}")
    print(f"SMTP Host: {settings.EMAIL_HOST}")
    print(f"SMTP Port: {settings.EMAIL_PORT}")
    print(f"Use TLS: {settings.EMAIL_USE_TLS}")
    print(f"From Email: {settings.DEFAULT_FROM_EMAIL}")
    print("=" * 60)
    
    # Тестовые данные
    test_recipient = input("Введите email получателя для теста: ").strip()
    
    if not test_recipient:
        print("❌ Email не указан!")
        return
    
    try:
        print(f"\n📧 Отправка тестового письма на {test_recipient}...")
        
        # Код для теста
        test_code = "123456"
        
        subject = 'Тестовое письмо от LinkAvto'
        message = f'''Здравствуйте!

Это тестовое письмо для проверки работы email.

Ваш тестовый код: {test_code}

С уважением,
Команда LinkAvto
https://linkavto.ru'''
        
        html_message = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #0066cc;">Тестовое письмо LinkAvto</h2>
                <p>Здравствуйте!</p>
                <p>Это тестовое письмо для проверки работы email.</p>
                <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                    {test_code}
                </div>
                <p style="color: #666;">Если вы получили это письмо, значит email работает корректно.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    С уважением,<br>
                    Команда <a href="https://linkavto.ru" style="color: #0066cc;">LinkAvto</a>
                </p>
            </div>
        </body>
        </html>
        '''
        
        from django.core.mail import EmailMultiAlternatives
        
        msg = EmailMultiAlternatives(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [test_recipient]
        )
        msg.attach_alternative(html_message, "text/html")
        msg.send()
        
        print("✅ Письмо отправлено успешно!")
        print(f"\n📬 Проверьте почтовый ящик: {test_recipient}")
        print("⚠️  Также проверьте папку 'Спам' если письмо не пришло в течение 1-2 минут")
        
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        print(f"\nТип ошибки: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_email()

