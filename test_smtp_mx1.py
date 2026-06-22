#!/usr/bin/env python
"""
Тест SMTP через mx1.hosting.reg.ru
"""
import smtplib
import sys

hosts = [
    ('31.31.194.240', 587, True),   # mx1 с TLS
    ('31.31.194.240', 465, False),  # mx1 с SSL
    ('31.31.194.240', 25, False),   # mx1 без шифрования
]

for host, port, use_tls in hosts:
    print(f"\n{'='*60}")
    print(f"Тест: {host}:{port} (TLS={use_tls})")
    print('='*60)
    
    try:
        if use_tls:
            server = smtplib.SMTP(host, port, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
        elif port == 465:
            server = smtplib.SMTP_SSL(host, port, timeout=10)
        else:
            server = smtplib.SMTP(host, port, timeout=10)
        
        print("✓ Соединение установлено")
        
        # Пробуем авторизацию
        try:
            server.login('linkavto@linkavto.ru', 'qK4gF2vX3btF4jS3')
            print("✓ Авторизация успешна!")
            server.quit()
            print(f"\n🎉 РАБОТАЕТ: {host}:{port} TLS={use_tls}")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Авторизация не удалась: {e}")
            server.quit()
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

print("\n❌ Ни один вариант не сработал")

