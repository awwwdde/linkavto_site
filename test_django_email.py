#!/usr/bin/env python
"""
Скрипт для тестирования отправки email через Django с текущими настройками
Запуск: python test_django_email.py
"""

import os
import sys
import django

# Настройка Django окружения
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avtolink.settings')
django.setup()

from django.core.mail import EmailMultiAlternatives
from django.conf import settings

def show_current_settings():
    """Показать текущие настройки email"""
    print("\n" + "="*60)
    print("⚙️  ТЕКУЩИЕ НАСТРОЙКИ EMAIL")
    print("="*60)
    print(f"Backend:        {settings.EMAIL_BACKEND}")
    print(f"Host:           {settings.EMAIL_HOST}")
    print(f"Port:           {settings.EMAIL_PORT}")
    print(f"Use SSL:        {settings.EMAIL_USE_SSL}")
    print(f"Use TLS:        {settings.EMAIL_USE_TLS}")
    print(f"User:           {settings.EMAIL_HOST_USER}")
    print(f"From:           {settings.DEFAULT_FROM_EMAIL}")
    print(f"Timeout:        {settings.EMAIL_TIMEOUT}")
    print("="*60)

def test_send_email(recipient):
    """Тест отправки email через Django"""
    print("\n" + "="*60)
    print("📧 ОТПРАВКА ТЕСТОВОГО ПИСЬМА")
    print("="*60)
    
    try:
        # Создаем письмо
        subject = f'Тест Django Email ({settings.EMAIL_HOST}:{settings.EMAIL_PORT})'
        
        text_content = f"""
Здравствуйте!

Это тестовое письмо от LinkAvto для проверки работы email через Django.

Настройки:
- Сервер: {settings.EMAIL_HOST}
- Порт: {settings.EMAIL_PORT}
- SSL: {settings.EMAIL_USE_SSL}
- TLS: {settings.EMAIL_USE_TLS}

Тестовый код: 123456

Если вы видите это письмо, значит email настроен правильно! ✅

С уважением,
Команда LinkAvto
https://linkavto.ru
"""
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0;">LinkAvto</h1>
        <p style="color: #f0f0f0; margin: 10px 0 0 0;">Тестовое письмо</p>
    </div>
    
    <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <h2 style="color: #667eea; margin-top: 0;">✅ Email работает!</h2>
        
        <p>Здравствуйте!</p>
        
        <p>Это тестовое письмо для проверки работы email через Django.</p>
        
        <div style="background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
            <h3 style="margin: 0 0 10px 0; color: #333;">Настройки подключения:</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 5px;"><strong>Сервер:</strong></td>
                    <td style="padding: 5px;">{settings.EMAIL_HOST}</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><strong>Порт:</strong></td>
                    <td style="padding: 5px;">{settings.EMAIL_PORT}</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><strong>SSL:</strong></td>
                    <td style="padding: 5px;">{settings.EMAIL_USE_SSL}</td>
                </tr>
                <tr>
                    <td style="padding: 5px;"><strong>TLS:</strong></td>
                    <td style="padding: 5px;">{settings.EMAIL_USE_TLS}</td>
                </tr>
            </table>
        </div>
        
        <div style="background: #667eea; color: white; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0;">
            <p style="margin: 0; font-size: 14px;">Ваш тестовый код:</p>
            <h1 style="margin: 10px 0; font-size: 36px; letter-spacing: 10px;">123456</h1>
        </div>
        
        <p style="color: #28a745; font-weight: bold;">
            🎉 Если вы видите это письмо, значит email настроен правильно!
        </p>
        
        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
        
        <p style="color: #666; font-size: 14px; text-align: center; margin: 0;">
            С уважением,<br>
            Команда <a href="https://linkavto.ru" style="color: #667eea; text-decoration: none;">LinkAvto</a>
        </p>
    </div>
    
    <div style="text-align: center; margin-top: 20px; color: #999; font-size: 12px;">
        <p>Это автоматическое письмо, не отвечайте на него.</p>
    </div>
</body>
</html>
"""
        
        # Создаем сообщение
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient]
        )
        msg.attach_alternative(html_content, "text/html")
        
        print(f"📤 Отправка письма на {recipient}...")
        print(f"   От: {settings.DEFAULT_FROM_EMAIL}")
        print(f"   Через: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}")
        
        # Отправляем
        msg.send(fail_silently=False)
        
        print("\n✅ Письмо успешно отправлено!")
        print(f"\n📬 Проверьте почтовый ящик: {recipient}")
        print("⚠️  Также проверьте папку 'Спам' если письмо не пришло в течение 1-2 минут")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при отправке: {type(e).__name__}")
        print(f"   {e}")
        
        # Подробная диагностика
        print("\n🔍 ДИАГНОСТИКА:")
        
        if "Authentication" in str(e):
            print("   ❌ Ошибка аутентификации")
            print("   Проверьте:")
            print("   - Правильность логина и пароля")
            print("   - Активна ли учетная запись на хостинге")
            
        elif "Connection" in str(e) or "timeout" in str(e).lower():
            print("   ❌ Ошибка подключения")
            print("   Проверьте:")
            print("   - Доступен ли сервер (ping mail.linkavto.ru)")
            print("   - Открыт ли порт на firewall")
            print("   - Правильность хоста и порта")
            
        elif "SSL" in str(e) or "TLS" in str(e):
            print("   ❌ Ошибка SSL/TLS")
            print("   Проверьте:")
            print("   - Правильность настроек USE_SSL/USE_TLS")
            print("   - Попробуйте другой порт (465 или 587)")
            
        else:
            print("   ℹ️  Общая ошибка")
        
        print("\n💡 РЕКОМЕНДАЦИИ:")
        print("   1. Запустите: python test_email_smtp_both.py")
        print("   2. Проверьте какой порт работает (465 или 587)")
        print("   3. Обновите настройки в avtolink/settings.py")
        
        import traceback
        print("\n📋 Полный traceback:")
        traceback.print_exc()
        
        return False

def main():
    print("\n" + "="*60)
    print("🚀 ТЕСТИРОВАНИЕ DJANGO EMAIL")
    print("="*60)
    
    # Показываем текущие настройки
    show_current_settings()
    
    # Получаем email получателя
    print("\n" + "="*60)
    recipient = input("📧 Введите email получателя для теста: ").strip()
    
    if not recipient or '@' not in recipient:
        print("❌ Некорректный email!")
        sys.exit(1)
    
    # Отправляем тестовое письмо
    success = test_send_email(recipient)
    
    # Итоги
    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТ")
    print("="*60)
    
    if success:
        print("✅ Тест пройден успешно!")
        print("\nВаши настройки работают правильно:")
        print(f"   EMAIL_HOST = '{settings.EMAIL_HOST}'")
        print(f"   EMAIL_PORT = {settings.EMAIL_PORT}")
        print(f"   EMAIL_USE_SSL = {settings.EMAIL_USE_SSL}")
        print(f"   EMAIL_USE_TLS = {settings.EMAIL_USE_TLS}")
    else:
        print("❌ Тест не пройден")
        print("\nИспользуйте скрипт для диагностики:")
        print("   python test_email_smtp_both.py")
    
    print("="*60)

if __name__ == '__main__':
    main()

