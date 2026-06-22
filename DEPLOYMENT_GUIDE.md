# 🚀 Руководство по развертыванию LinkAvto на сервере

## ✅ Исправлены следующие проблемы:

### 1. 🚨 DEBUG=False на production сервере
- Создана структура настроек settings/ с разделением для dev/production
- В production автоматически DEBUG=False

### 2. 🔐 Исправлен CaptchaMiddleware
- В production режиме капча автоматически отключается
- На локальном сервере (DEBUG=True) капча работает как прежде

### 3. ⚙️ Добавлена конфигурация Gunicorn
- Создан gunicorn.conf.py с оптимальными настройками
- Добавлен systemd service для автоматического запуска

### 4. 📧 Оптимизированы настройки Email
- Настройки email разделены для dev/production
- В production используется reg.ru SMTP

---

## 📋 Пошаговая инструкция развертывания:

### Шаг 1: Подготовка сервера

```bash
# Подключение к серверу
ssh root@193.227.241.158
# Пароль: N9dllchxieO5sSVx

# Обновление системы
apt update && apt upgrade -y

# Установка необходимых пакетов
apt install -y python3 python3-venv python3-pip nginx postgresql postgresql-contrib redis-server

# Создание пользователя для приложения
useradd -m -s /bin/bash linkavto
usermod -aG www-data linkavto
```

### Шаг 2: Настройка базы данных PostgreSQL

```bash
# Переключение на пользователя postgres
sudo -u postgres psql

# В PostgreSQL консоли:
CREATE DATABASE avtolink_django;
CREATE USER avtolink_django WITH ENCRYPTED PASSWORD '197505';
GRANT ALL PRIVILEGES ON DATABASE avtolink_django TO avtolink_django;
\\q
```

### Шаг 3: Установка проекта

```bash
# Переключение на пользователя linkavto
su - linkavto

# Клонирование проекта (или загрузка)
# Предполагаем, что проект уже находится в /home/linkavto/linkavto

cd /home/linkavto/linkavto

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### Шаг 4: Настройка переменных окружения

```bash
# Создание файла с переменными окружения
cat > /home/linkavto/linkavto/.env << EOF
DJANGO_ENV=production
DJANGO_SETTINGS_MODULE=avtolink.settings
EOF

# Добавление в bashrc для постоянного использования
echo "export DJANGO_ENV=production" >> /home/linkavto/.bashrc
source /home/linkavto/.bashrc
```

### Шаг 5: Миграция базы данных

```bash
# Активация виртуального окружения
source /home/linkavto/linkavto/venv/bin/activate
cd /home/linkavto/linkavto

# Установка переменной окружения
export DJANGO_ENV=production

# Выполнение миграций
python manage.py migrate

# Сбор статических файлов
python manage.py collectstatic --noinput

# Создание суперпользователя
python manage.py createsuperuser
```

### Шаг 6: Создание директорий для логов

```bash
# Возвращение к root пользователю
exit

# Создание директорий для логов
mkdir -p /var/log/linkavto
chown linkavto:www-data /var/log/linkavto
chmod 755 /var/log/linkavto
```

### Шаг 7: Настройка systemd службы

```bash
# Копирование service файла
cp /home/linkavto/linkavto/linkavto.service /etc/systemd/system/

# Обновление прав
chown root:root /etc/systemd/system/linkavto.service
chmod 644 /etc/systemd/system/linkavto.service

# Перезагрузка systemd и запуск службы
systemctl daemon-reload
systemctl enable linkavto
systemctl start linkavto

# Проверка статуса
systemctl status linkavto
```

### Шаг 8: Настройка Nginx

```bash
# Создание конфигурации Nginx
cat > /etc/nginx/sites-available/linkavto << EOF
server {
    listen 80;
    server_name linkavto.ru www.linkavto.ru 193.227.241.158;

    location /static/ {
        alias /home/linkavto/linkavto/staticfiles/;
    }

    location /media/ {
        alias /home/linkavto/linkavto/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \\$host;
        proxy_set_header X-Real-IP \\$remote_addr;
        proxy_set_header X-Forwarded-For \\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\$scheme;
    }
}
EOF

# Активация сайта
ln -s /etc/nginx/sites-available/linkavto /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Проверка конфигурации и перезапуск
nginx -t
systemctl restart nginx
```

---

## 🔍 Диагностика проблем:

### Проверка работы служб:
```bash
# Статус Django приложения
systemctl status linkavto

# Логи Django
tail -f /var/log/linkavto/django.log
tail -f /var/log/linkavto/gunicorn_error.log

# Статус Nginx
systemctl status nginx

# Статус PostgreSQL
systemctl status postgresql
```

### Тестирование email:
```bash
# Переход в Django shell
cd /home/linkavto/linkavto
source venv/bin/activate
export DJANGO_ENV=production
python manage.py shell

# В Django shell:
from django.core.mail import send_mail
send_mail('Test', 'Test message', 'linkavto@linkavto.ru', ['test@example.com'])
```

### Проверка настроек:
```bash
# Проверка текущих настроек
python manage.py diffsettings
```

---

## 🎯 Основные изменения в коде:

1. **Структура настроек**: `settings/` папка с разделением на dev/production
2. **CaptchaMiddleware**: Автоматически отключается в production
3. **Email настройки**: Оптимизированы для reg.ru в production
4. **Gunicorn конфигурация**: Добавлена для production сервера
5. **Systemd service**: Для автоматического запуска и управления

---

## ⚡ Важные команды для администрирования:

```bash
# Перезапуск приложения
systemctl restart linkavto

# Перезапуск Nginx
systemctl restart nginx

# Обновление кода (после git pull)
su - linkavto
cd /home/linkavto/linkavto
source venv/bin/activate
export DJANGO_ENV=production
python manage.py migrate
python manage.py collectstatic --noinput
exit
systemctl restart linkavto

# Просмотр логов в реальном времени
tail -f /var/log/linkavto/django.log
```

## 🔧 Возможные проблемы и решения:

### 1. Gunicorn не запускается:
- Проверьте права доступа к файлам
- Убедитесь что все пути в service файле корректны
- Проверьте логи: `journalctl -u linkavto -f`

### 2. Email не отправляется:
- Проверьте настройки reg.ru
- Убедитесь что сервер может подключаться к 31.31.196.47:25
- Проверьте логи Django: `tail -f /var/log/linkavto/django.log`

### 3. Статические файлы не загружаются:
- Выполните: `python manage.py collectstatic --noinput`
- Проверьте права доступа к папке staticfiles
- Убедитесь что Nginx правильно настроен

---

## ✅ После развертывания проверьте:

1. ✅ Сайт открывается в браузере
2. ✅ Капча НЕ появляется (отключена в production)
3. ✅ Email отправляется при регистрации/заказах
4. ✅ Статические файлы загружаются
5. ✅ Административная панель работает
6. ✅ Все функции сайта работают корректно

Удачного развертывания! 🎉

