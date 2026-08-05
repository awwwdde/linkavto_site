#!/bin/bash

# Скрипт для запуска LinkAvto с gunicorn в production режиме

# Установка переменных окружения
export DJANGO_ENV=production

# Путь к проекту (измените на свой)
PROJECT_DIR="/path/to/linkavto"
VENV_DIR="$PROJECT_DIR/venv"

# Активация виртуального окружения
source "$VENV_DIR/bin/activate"

# Переход в директорию проекта
cd "$PROJECT_DIR"

# Создание директории для логов (если не существует)
sudo mkdir -p /var/log/linkavto
sudo chown www-data:www-data /var/log/linkavto

# Выполнение миграций
python manage.py migrate --noinput

# Сбор статических файлов
python manage.py collectstatic --noinput

# Запуск gunicorn
exec gunicorn \
    --config gunicorn.conf.py \
    avtolink.wsgi:application
