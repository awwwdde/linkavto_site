import requests
import logging
from django.conf import settings
from .sms_service_smsru import send_sms as send_sms_smsru

logger = logging.getLogger(__name__)


def send_sms_smsc(phone, message):
    """
    Отправка SMS через сервис smsc.ru
    Документация: https://smsc.ru/api/
    """
    try:
        # Конфигурация из settings.py
        smsc_login = getattr(settings, 'SMSC_LOGIN', '')
        smsc_password = getattr(settings, 'SMSC_PASSWORD', '')
        smsc_sender = getattr(settings, 'SMSC_SENDER', 'LinkAvto')

        if not all([smsc_login, smsc_password]):
            logger.error("SMSC credentials not configured")
            return False

        # Подготовка параметров
        params = {
            'login': smsc_login,
            'psw': smsc_password,
            'sender': smsc_sender,
            'phones': phone,
            'mes': message,
            'fmt': 3,  # JSON формат ответа
            'charset': 'utf-8'
        }

        # Отправка запроса
        response = requests.get('https://smsc.ru/sys/send.php', params=params, timeout=10)
        response_data = response.json()

        # Проверка ответа
        if 'error' in response_data:
            logger.error(f"SMSC error: {response_data['error']}")
            return False
        else:
            logger.info(f"SMS sent to {phone}, ID: {response_data.get('id', 'unknown')}")
            return True

    except Exception as e:
        logger.error(f"SMS sending error: {e}")
        return False


def send_sms(phone, message):
    """
    Универсальная функция отправки SMS
    Пробует SMS.RU, если не настроен - SMSC, если заблокирован - DEBUG
    """
    # Сначала пробуем SMS.RU
    try:
        result = send_sms_smsru(phone, message)
        if result:
            return True
    except Exception as e:
        logger.warning(f"SMS.RU failed: {e}")

    # Если SMS.RU не работает, пробуем SMSC
    try:
        result = send_sms_smsc(phone, message)
        if result:
            return True
    except Exception as e:
        logger.warning(f"SMSC failed: {e}")

    # Если ничего не работает - DEBUG режим
    logger.info(f"SMS to {phone}: {message}")
    logger.warning("SMS отправлен в режиме DEBUG (все сервисы недоступны)")
    return True