import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def send_sms_smsru(phone, message):
    """
    Отправка SMS через сервис SMS.RU
    Документация: https://sms.ru/api
    """
    try:
        # Конфигурация из settings.py
        api_id = getattr(settings, 'SMSRU_API_ID', '')
        sender = getattr(settings, 'SMSRU_SENDER', 'LinkAvto')

        if not api_id:
            logger.error("SMSRU_API_ID not configured")
            return False

        # Подготовка параметров
        params = {
            'api_id': api_id,
            'to': phone,
            'msg': message,
            'from': sender,
            'json': 1  # JSON формат ответа
        }

        # Отправка запроса
        response = requests.get('https://sms.ru/sms/send', params=params, timeout=10)
        response_data = response.json()

        # Проверка ответа
        if response_data.get('status') == 'OK':
            logger.info(
                f"SMS sent to {phone} via SMS.RU, ID: {response_data.get('sms', {}).get(phone, {}).get('sms_id', 'unknown')}")
            return True
        else:
            logger.error(f"SMS.RU error: {response_data.get('status_text', 'Unknown error')}")
            return False

    except Exception as e:
        logger.error(f"SMS.RU sending error: {e}")
        return False


def send_sms(phone, message):
    """
    Универсальная функция отправки SMS
    Пробует SMS.RU, если не настроен - выводит в консоль
    """
    # Проверяем, настроен ли SMS.RU
    api_id = getattr(settings, 'SMSRU_API_ID', '')

    if api_id:
        # Отправляем через SMS.RU
        return send_sms_smsru(phone, message)
    else:
        # Если не настроен - выводим в консоль
        logger.info(f"SMS to {phone}: {message}")
        logger.warning("SMS отправлен в режиме DEBUG (SMS.RU не настроен)")
        return True

