#!/usr/bin/env python
"""
Детальный тест отправки email с обработкой ошибок
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avtolink.settings')
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
import socket
import sys

def test_smtp_connection():
    """Проверка соединения с SMTP сервером"""
    print("\n" + "=" * 60)
    print("ПРОВЕРКА СОЕДИНЕНИЯ С SMTP")
    print("=" * 60)
    
    try:
        import smtplib
        
        print(f"Подключение к {settings.EMAIL_HOST}:{settings.EMAIL_PORT}...")
        
        if settings.EMAIL_USE_TLS:
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=30)
            server.ehlo()
            print("✓ EHLO команда выполнена")
            
            server.starttls()
            print("✓ TLS соединение установлено")
            
            server.ehlo()
            print("✓ EHLO после TLS выполнена")
        else:
            server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT, timeout=30)
            print("✓ Соединение установлено")
        
        print(f"Авторизация как {settings.EMAIL_HOST_USER}...")
        server.login(settings.EMAIL_HOST_USER, settings.EMAIL_HOST_PASSWORD)
        print("✓ Авторизация успешна")
        
        server.quit()
        print("✓ Соединение закрыто\n")
        return True
        
    except socket.gaierror as e:
        print(f"❌ Ошибка DNS: {e}")
        return False
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Ошибка авторизации: {e}")
        print("Проверьте логин и пароль в настройках")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP ошибка: {e}")
        return False
    except Exception as e:
        print(f"❌ Неизвестная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_email_send():
    """Тест отправки email через Django"""
    print("=" * 60)
    print("ОТПРАВКА ТЕСТОВОГО EMAIL")
    print("=" * 60)
    
    recipient = "seregaboj619@gmail.com"  # Используем email из лога
    test_code = "123456"
    
    try:
        subject = 'Тестовое письмо от LinkAvto'
        
        text_content = f'''Здравствуйте!

Ваш код подтверждения для входа в LinkAvto: {test_code}

Код действителен в течение 15 минут.

С уважением,
Команда LinkAvto
https://linkavto.ru'''
        
        html_content = f'''
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #0066cc;">Код подтверждения LinkAvto</h2>
                <p>Здравствуйте!</p>
                <p>Ваш код подтверждения для входа в LinkAvto:</p>
                <div style="background-color: #f4f4f4; padding: 15px; text-align: center; font-size: 24px; font-weight: bold; letter-spacing: 5px; margin: 20px 0;">
                    {test_code}
                </div>
                <p style="color: #666;">Код действителен в течение 15 минут.</p>
                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 12px;">
                    С уважением,<br>
                    Команда <a href="https://linkavto.ru" style="color: #0066cc;">LinkAvto</a>
                </p>
            </div>
        </body>
        </html>
        '''
        
        print(f"Отправка письма на {recipient}...")
        
        msg = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [recipient]
        )
        msg.attach_alternative(html_content, "text/html")
        
        # Отправляем с детальным логированием
        result = msg.send(fail_silently=False)
        
        print(f"✅ Письмо отправлено! Результат: {result}")
        print(f"\n📬 Проверьте почту: {recipient}")
        print("⚠️  Проверьте папку 'Спам' и 'Промоакции' в Gmail")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        print(f"Тип ошибки: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("\n🔍 ДЕТАЛЬНАЯ ДИАГНОСТИКА EMAIL")
    print("=" * 60)
    print(f"Host: {settings.EMAIL_HOST}")
    print(f"Port: {settings.EMAIL_PORT}")
    print(f"TLS: {settings.EMAIL_USE_TLS}")
    print(f"User: {settings.EMAIL_HOST_USER}")
    print(f"From: {settings.DEFAULT_FROM_EMAIL}")
    
    # Шаг 1: Проверка соединения
    if test_smtp_connection():
        # Шаг 2: Отправка письма
        test_email_send()
    else:
        print("\n❌ Не удалось подключиться к SMTP серверу")
        print("Возможные причины:")
        print("1. Порт 587 заблокирован файрволом")
        print("2. Неверные учетные данные SMTP")
        print("3. Проблемы с интернет-соединением сервера")
        sys.exit(1)

