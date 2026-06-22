#!/bin/bash
BACKUP_DIR="/opt/linkavto/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Полный дамп базы
sudo -u postgres pg_dump avtolink_django > $BACKUP_DIR/avtolink_django_$DATE.sql
gzip $BACKUP_DIR/avtolink_django_$DATE.sql

# Удаляем старые бэкапы (старше 7 дней)
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete

echo "Backup created: $BACKUP_DIR/avtolink_django_$DATE.sql.gz"

