#!/usr/bin/env python
"""
Скрипт для тестирования двух вариантов SMTP подключения:
1. mail.linkavto.ru:465 (SSL)
2. mail.linkavto.ru:587 (TLS)

Запуск: python test_email_smtp_both.py
"""

import socket
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Настройки
EMAIL_HOST = 'mail.linkavto.ru'
EMAIL_USER = 'linkavto@linkavto.ru'
EMAIL_PASSWORD = 'qK4gF2vX3btF4jS3'
FROM_EMAIL = 'linkavto@linkavto.ru'

def test_connection(host, port):
    """Тест TCP подключения к серверу"""
    print(f"\n{'='*60}")
    print(f"🔌 Тест подключения к {host}:{port}")
    print(f"{'='*60}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Порт {port} доступен")
            return True
        else:
            print(f"❌ Порт {port} недоступен (код: {result})")
            return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_smtp_ssl(host, port, user, password, recipient):
    """Тест отправки через SSL (порт 465)"""
    print(f"\n{'='*60}")
    print(f"📧 Тест SMTP SSL - {host}:{port}")
    print(f"{'='*60}")
    
    try:
        # Создаем SSL контекст
        context = ssl.create_default_context()
        # Для тестирования можно отключить проверку сертификата
        # context.check_hostname = False
        # context.verify_mode = ssl.CERT_NONE
        
        print(f"🔐 Подключение к {host}:{port} через SSL...")
        
        # Подключаемся через SSL сразу
        with smtplib.SMTP_SSL(host, port, timeout=30, context=context) as server:
            print("✅ SSL подключение установлено")
            
            print(f"👤 Аутентификация как {user}...")
            server.login(user, password)
            print("✅ Аутентификация успешна")
            
            # Создаем письмо
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'Тест SMTP SSL (порт {port})'
            msg['From'] = FROM_EMAIL
            msg['To'] = recipient
            
            text = f"Тестовое письмо через SMTP SSL на порту {port}"
            html = f"""
            <html>
            <body>
                <h2>✅ Тест успешен!</h2>
                <p>Письмо отправлено через SMTP SSL на порту {port}</p>
                <p>Сервер: {host}</p>
                <p>От: {FROM_EMAIL}</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(text, 'plain'))
            msg.attach(MIMEText(html, 'html'))
            
            print(f"📤 Отправка письма на {recipient}...")
            server.send_message(msg)
            print("✅ Письмо отправлено успешно!")
            
            return True
            
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Ошибка аутентификации: {e}")
        print("   Проверьте логин и пароль")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP ошибка: {e}")
        return False
    except ssl.SSLError as e:
        print(f"❌ SSL ошибка: {e}")
        print("   Попробуйте отключить проверку сертификата")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_smtp_tls(host, port, user, password, recipient):
    """Тест отправки через TLS (порт 587)"""
    print(f"\n{'='*60}")
    print(f"📧 Тест SMTP TLS - {host}:{port}")
    print(f"{'='*60}")
    
    try:
        print(f"🔌 Подключение к {host}:{port}...")
        
        with smtplib.SMTP(host, port, timeout=30) as server:
            print("✅ Подключение установлено")
            
            # Включаем debug для диагностики
            # server.set_debuglevel(1)
            
            print("🔐 Начало TLS...")
            server.starttls()
            print("✅ TLS активирован")
            
            print(f"👤 Аутентификация как {user}...")
            server.login(user, password)
            print("✅ Аутентификация успешна")
            
            # Создаем письмо
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'Тест SMTP TLS (порт {port})'
            msg['From'] = FROM_EMAIL
            msg['To'] = recipient
            
            text = f"Тестовое письмо через SMTP TLS на порту {port}"
            html = f"""
            <html>
            <body>
                <h2>✅ Тест успешен!</h2>
                <p>Письмо отправлено через SMTP TLS на порту {port}</p>
                <p>Сервер: {host}</p>
                <p>От: {FROM_EMAIL}</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(text, 'plain'))
            msg.attach(MIMEText(html, 'html'))
            
            print(f"📤 Отправка письма на {recipient}...")
            server.send_message(msg)
            print("✅ Письмо отправлено успешно!")
            
            return True
            
    except smtplib.SMTPAuthenticationError as e:
        print(f"❌ Ошибка аутентификации: {e}")
        print("   Проверьте логин и пароль")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP ошибка: {e}")
        return False
    except Exception as e:
        print(f"❌ Ошибка: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*60)
    print("🚀 ТЕСТИРОВАНИЕ SMTP ПОДКЛЮЧЕНИЯ")
    print("="*60)
    print(f"Сервер: {EMAIL_HOST}")
    print(f"Пользователь: {EMAIL_USER}")
    print(f"От кого: {FROM_EMAIL}")
    print("="*60)
    
    # Получаем email получателя
    recipient = input("\n📧 Введите email получателя для теста: ").strip()
    
    if not recipient or '@' not in recipient:
        print("❌ Некорректный email!")
        return
    
    # Тест DNS резолвинга
    print(f"\n{'='*60}")
    print(f"🌐 Проверка DNS для {EMAIL_HOST}")
    print(f"{'='*60}")
    try:
        ip = socket.gethostbyname(EMAIL_HOST)
        print(f"✅ {EMAIL_HOST} → {ip}")
    except Exception as e:
        print(f"❌ Ошибка DNS: {e}")
        return
    
    # Тест подключения к портам
    port_465_available = test_connection(EMAIL_HOST, 465)
    port_587_available = test_connection(EMAIL_HOST, 587)
    
    # Если оба порта недоступны
    if not port_465_available and not port_587_available:
        print("\n❌ Оба порта недоступны. Проверьте:")
        print("   1. Firewall на сервере")
        print("   2. Настройки хостинга")
        print("   3. DNS настройки")
        return
    
    results = {}
    
    # Тест SSL (порт 465)
    if port_465_available:
        results['SSL (465)'] = test_smtp_ssl(EMAIL_HOST, 465, EMAIL_USER, EMAIL_PASSWORD, recipient)
    
    # Тест TLS (порт 587)
    if port_587_available:
        results['TLS (587)'] = test_smtp_tls(EMAIL_HOST, 587, EMAIL_USER, EMAIL_PASSWORD, recipient)
    
    # Итоги
    print(f"\n{'='*60}")
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print(f"{'='*60}")
    
    for method, success in results.items():
        status = "✅ Работает" if success else "❌ Не работает"
        print(f"{method}: {status}")
    
    # Рекомендации
    print(f"\n{'='*60}")
    print("💡 РЕКОМЕНДАЦИИ")
    print(f"{'='*60}")
    
    if results.get('SSL (465)'):
        print("✅ Используйте настройки SSL (порт 465) в Django:")
        print("   EMAIL_HOST = 'mail.linkavto.ru'")
        print("   EMAIL_PORT = 465")
        print("   EMAIL_USE_SSL = True")
        print("   EMAIL_USE_TLS = False")
    elif results.get('TLS (587)'):
        print("✅ Используйте настройки TLS (порт 587) в Django:")
        print("   EMAIL_HOST = 'mail.linkavto.ru'")
        print("   EMAIL_PORT = 587")
        print("   EMAIL_USE_TLS = True")
        print("   EMAIL_USE_SSL = False")
    else:
        print("❌ Ни один метод не работает. Обратитесь в поддержку хостинга.")
    
    print(f"\n📬 Проверьте почту {recipient}")
    print("⚠️  Также проверьте папку 'Спам'")

if __name__ == '__main__':
    main()

