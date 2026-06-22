#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Простой тест SMTP подключения без эмодзи для Windows консоли
Запуск: python test_smtp_simple.py
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
    print(f"Test podklyucheniya k {host}:{port}")
    print(f"{'='*60}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"[OK] Port {port} dostupen")
            return True
        else:
            print(f"[X] Port {port} nedostupen (kod: {result})")
            return False
    except Exception as e:
        print(f"[X] Oshibka podklyucheniya: {e}")
        return False

def test_smtp_ssl(host, port, user, password, recipient):
    """Тест отправки через SSL (порт 465)"""
    print(f"\n{'='*60}")
    print(f"Test SMTP SSL - {host}:{port}")
    print(f"{'='*60}")
    
    try:
        context = ssl.create_default_context()
        
        print(f"Podklyuchenie k {host}:{port} cherez SSL...")
        
        with smtplib.SMTP_SSL(host, port, timeout=30, context=context) as server:
            print("[OK] SSL podklyuchenie ustanovleno")
            
            print(f"Autentifikatsiya kak {user}...")
            server.login(user, password)
            print("[OK] Autentifikatsiya uspeshna")
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'Test SMTP SSL (port {port})'
            msg['From'] = FROM_EMAIL
            msg['To'] = recipient
            
            text = f"Testovoe pismo cherez SMTP SSL na portu {port}"
            html = f"""
            <html>
            <body>
                <h2>Test uspeshen!</h2>
                <p>Pismo otpravleno cherez SMTP SSL na portu {port}</p>
                <p>Server: {host}</p>
                <p>Ot: {FROM_EMAIL}</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(text, 'plain', 'utf-8'))
            msg.attach(MIMEText(html, 'html', 'utf-8'))
            
            print(f"Otpravka pisma na {recipient}...")
            server.send_message(msg)
            print("[OK] Pismo otpravleno uspeshno!")
            
            return True
            
    except smtplib.SMTPAuthenticationError as e:
        print(f"[X] Oshibka autentifikatsii: {e}")
        print("   Proverte login i parol")
        return False
    except smtplib.SMTPException as e:
        print(f"[X] SMTP oshibka: {e}")
        return False
    except ssl.SSLError as e:
        print(f"[X] SSL oshibka: {e}")
        return False
    except Exception as e:
        print(f"[X] Oshibka: {type(e).__name__}: {e}")
        return False

def test_smtp_tls(host, port, user, password, recipient):
    """Тест отправки через TLS (порт 587)"""
    print(f"\n{'='*60}")
    print(f"Test SMTP TLS - {host}:{port}")
    print(f"{'='*60}")
    
    try:
        print(f"Podklyuchenie k {host}:{port}...")
        
        with smtplib.SMTP(host, port, timeout=30) as server:
            print("[OK] Podklyuchenie ustanovleno")
            
            print("Nachalo TLS...")
            server.starttls()
            print("[OK] TLS aktivirovan")
            
            print(f"Autentifikatsiya kak {user}...")
            server.login(user, password)
            print("[OK] Autentifikatsiya uspeshna")
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f'Test SMTP TLS (port {port})'
            msg['From'] = FROM_EMAIL
            msg['To'] = recipient
            
            text = f"Testovoe pismo cherez SMTP TLS na portu {port}"
            html = f"""
            <html>
            <body>
                <h2>Test uspeshen!</h2>
                <p>Pismo otpravleno cherez SMTP TLS na portu {port}</p>
                <p>Server: {host}</p>
                <p>Ot: {FROM_EMAIL}</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(text, 'plain', 'utf-8'))
            msg.attach(MIMEText(html, 'html', 'utf-8'))
            
            print(f"Otpravka pisma na {recipient}...")
            server.send_message(msg)
            print("[OK] Pismo otpravleno uspeshno!")
            
            return True
            
    except smtplib.SMTPAuthenticationError as e:
        print(f"[X] Oshibka autentifikatsii: {e}")
        return False
    except smtplib.SMTPException as e:
        print(f"[X] SMTP oshibka: {e}")
        return False
    except Exception as e:
        print(f"[X] Oshibka: {type(e).__name__}: {e}")
        return False

def main():
    print("\n" + "="*60)
    print("TESTIROVANIE SMTP PODKLYUCHENIYA")
    print("="*60)
    print(f"Server: {EMAIL_HOST}")
    print(f"Polzovatel: {EMAIL_USER}")
    print(f"Ot kogo: {FROM_EMAIL}")
    print("="*60)
    
    recipient = input("\nVvedite email poluchatelya dlya testa: ").strip()
    
    if not recipient or '@' not in recipient:
        print("[X] Nekorrektnyy email!")
        return
    
    # Тест DNS
    print(f"\n{'='*60}")
    print(f"Proverka DNS dlya {EMAIL_HOST}")
    print(f"{'='*60}")
    try:
        ip = socket.gethostbyname(EMAIL_HOST)
        print(f"[OK] {EMAIL_HOST} -> {ip}")
    except Exception as e:
        print(f"[X] Oshibka DNS: {e}")
        return
    
    # Тест подключения к портам
    port_465_available = test_connection(EMAIL_HOST, 465)
    port_587_available = test_connection(EMAIL_HOST, 587)
    
    if not port_465_available and not port_587_available:
        print("\n[X] Oba porta nedostupny. Proverte:")
        print("   1. Firewall na servere")
        print("   2. Nastroyki hostinga")
        print("   3. DNS nastroyki")
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
    print("ITOGI TESTIROVANIYA")
    print(f"{'='*60}")
    
    for method, success in results.items():
        status = "[OK] Rabotaet" if success else "[X] Ne rabotaet"
        print(f"{method}: {status}")
    
    # Рекомендации
    print(f"\n{'='*60}")
    print("REKOMENDATSII")
    print(f"{'='*60}")
    
    if results.get('SSL (465)'):
        print("[OK] Ispolzuyte nastroyki SSL (port 465) v Django:")
        print("   EMAIL_HOST = 'mail.linkavto.ru'")
        print("   EMAIL_PORT = 465")
        print("   EMAIL_USE_SSL = True")
        print("   EMAIL_USE_TLS = False")
    elif results.get('TLS (587)'):
        print("[OK] Ispolzuyte nastroyki TLS (port 587) v Django:")
        print("   EMAIL_HOST = 'mail.linkavto.ru'")
        print("   EMAIL_PORT = 587")
        print("   EMAIL_USE_TLS = True")
        print("   EMAIL_USE_SSL = False")
    else:
        print("[X] Ni odin metod ne rabotaet. Obratites v podderzhku hostinga.")
    
    print(f"\nProverte pochtu {recipient}")

if __name__ == '__main__':
    main()

