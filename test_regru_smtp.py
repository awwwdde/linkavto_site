#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Тест SMTP подключения к серверам Reg.ru
"""

import socket
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

EMAIL_HOST = 'mx1.hosting.reg.ru'
EMAIL_USER = 'linkavto@linkavto.ru'
EMAIL_PASSWORD = 'qK4gF2vX3btF4jS3'

def test_ports():
    """Проверка доступности портов"""
    print("="*60)
    print("Proverka portov na", EMAIL_HOST)
    print("="*60)
    
    ports = [25, 465, 587]
    available = []
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((EMAIL_HOST, port))
            sock.close()
            
            if result == 0:
                print(f"[OK] Port {port} - DOSTUPEN")
                available.append(port)
            else:
                print(f"[X] Port {port} - nedostupen")
        except Exception as e:
            print(f"[X] Port {port} - oshibka: {e}")
    
    return available

def test_smtp_587(recipient):
    """Тест TLS на порту 587"""
    print("\n" + "="*60)
    print(f"Test SMTP TLS (port 587)")
    print("="*60)
    
    try:
        print(f"Podklyuchenie k {EMAIL_HOST}:587...")
        server = smtplib.SMTP(EMAIL_HOST, 587, timeout=15)
        print("[OK] Podklyucheno")
        
        server.set_debuglevel(0)  # Включите 1 для отладки
        
        print("Zapusk STARTTLS...")
        server.starttls()
        print("[OK] TLS aktivirovan")
        
        print(f"Login kak {EMAIL_USER}...")
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        print("[OK] Autentifikatsiya uspeshna!")
        
        # Создаем письмо
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = recipient
        msg['Subject'] = 'Test Reg.ru SMTP TLS'
        
        body = "Testovoe pismo s Reg.ru cherez TLS (port 587)"
        msg.attach(MIMEText(body, 'plain'))
        
        print(f"Otpravka pisma na {recipient}...")
        server.send_message(msg)
        server.quit()
        
        print("[OK] PISMO OTPRAVLENO USPESHNO!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"[X] Oshibka avtorizatsii: {e}")
        return False
    except Exception as e:
        print(f"[X] Oshibka: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_smtp_465(recipient):
    """Тест SSL на порту 465"""
    print("\n" + "="*60)
    print(f"Test SMTP SSL (port 465)")
    print("="*60)
    
    try:
        context = ssl.create_default_context()
        
        print(f"Podklyuchenie k {EMAIL_HOST}:465...")
        server = smtplib.SMTP_SSL(EMAIL_HOST, 465, timeout=15, context=context)
        print("[OK] SSL podklyuchenie ustanovleno")
        
        print(f"Login kak {EMAIL_USER}...")
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        print("[OK] Autentifikatsiya uspeshna!")
        
        # Создаем письмо
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = recipient
        msg['Subject'] = 'Test Reg.ru SMTP SSL'
        
        body = "Testovoe pismo s Reg.ru cherez SSL (port 465)"
        msg.attach(MIMEText(body, 'plain'))
        
        print(f"Otpravka pisma na {recipient}...")
        server.send_message(msg)
        server.quit()
        
        print("[OK] PISMO OTPRAVLENO USPESHNO!")
        return True
        
    except Exception as e:
        print(f"[X] Oshibka: {type(e).__name__}: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("TEST SMTP REG.RU")
    print("="*60)
    print(f"Host: {EMAIL_HOST}")
    print(f"User: {EMAIL_USER}")
    print("="*60)
    
    recipient = input("\nVvedite email poluchatelya: ").strip()
    if not recipient or '@' not in recipient:
        print("[X] Nekorrektnyy email!")
        return
    
    # Проверка портов
    available_ports = test_ports()
    
    if not available_ports:
        print("\n[X] Ni odin port ne dostupen!")
        print("Vozmozhno, nuzhno testirovato na servere, a ne lokalono.")
        return
    
    results = {}
    
    # Тестируем доступные порты
    if 587 in available_ports:
        results['TLS (587)'] = test_smtp_587(recipient)
    
    if 465 in available_ports:
        results['SSL (465)'] = test_smtp_465(recipient)
    
    # Итоги
    print("\n" + "="*60)
    print("ITOGI")
    print("="*60)
    for method, success in results.items():
        status = "[OK] RABOTAET" if success else "[X] NE RABOTAET"
        print(f"{method}: {status}")
    
    if any(results.values()):
        print("\n[OK] Email rabotaet! Proverte pochtu:", recipient)
    else:
        print("\n[X] Ne udalos otpravit pismo")

if __name__ == '__main__':
    main()

