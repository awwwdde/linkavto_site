import requests
import json
import logging
import hashlib
from django.conf import settings
from decimal import Decimal

logger = logging.getLogger(__name__)


class TBankPaymentService:
    """
    Сервис для работы с Т-Банк API
    """
    
    def __init__(self):
        self.terminal = settings.TBANK_TERMINAL
        self.password = settings.TBANK_PASSWORD
        self.api_url = settings.TBANK_API_URL
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _generate_token(self, params):
        """
        Генерация токена для подписи запроса согласно документации T-Bank
        """
        # Исключаем Token, Password и вложенные объекты из параметров для генерации токена
        token_params = {}
        for key, value in params.items():
            if key not in ['Token', 'Password', 'Receipt', 'DATA', 'Shops']:
                token_params[key] = value
        
        # Добавляем пароль
        token_params['Password'] = self.password
        
        # Сортируем параметры по алфавиту
        sorted_params = sorted(token_params.items())
        
        # Создаем строку для подписи (только значения)
        values = []
        for key, value in sorted_params:
            if value is not None:
                values.append(str(value))
        
        # Создаем строку для хеширования
        token_string = ''.join(values)
        
        # Генерируем SHA-256 хеш
        token = hashlib.sha256(token_string.encode('utf-8')).hexdigest()
        
        return token
    
    def create_payment(self, order_id, amount, description="Оплата заказа", order_items=None, customer_email=None, customer_phone=None):
        """
        Создание платежа в Т-Банк согласно API v2
        
        Args:
            order_id (int): ID заказа (может быть None для временного ID)
            amount (Decimal): Сумма платежа
            description (str): Описание платежа
            order_items (list): Список товаров заказа для чека
            customer_email (str): Email покупателя
            customer_phone (str): Телефон покупателя
            
        Returns:
            dict: Ответ от API или None в случае ошибки
        """
        try:
            # Конвертируем сумму в копейки
            amount_kopecks = int(amount * 100)
            
            # Генерируем уникальный OrderId с временной меткой для избежания конфликтов
            import time
            unique_order_id = f"{order_id}_{int(time.time())}"
            
            # Подготавливаем параметры для API
            params = {
                "TerminalKey": self.terminal,
                "Amount": amount_kopecks,
                "OrderId": unique_order_id,
                "Description": description,
                "Language": "ru",
                "NotificationURL": f"https://linkavto.ru/orders/api/payment/tbank/notify/",
                "SuccessURL": f"https://linkavto.ru/orders/success/{order_id}/",
                "FailURL": f"https://linkavto.ru/orders/fail/{order_id}/",
                "PayType": "O",  # Одностадийная оплата
                "CustomerKey": f"customer_{order_id}",
                "Recurrent": "Y"  # Для сохранения карт
            }
            
            # Добавляем данные чека если есть товары
            if order_items:
                receipt_items = []
                for item in order_items:
                    receipt_items.append({
                        "Name": item.product.name[:64],  # Ограничение по длине
                        "Price": int(item.price * 100),  # В копейках
                        "Quantity": item.quantity,
                        "Amount": int(item.price * item.quantity * 100),  # В копейках
                        "PaymentMethod": "full_payment",
                        "PaymentObject": "commodity",
                        "Tax": "vat20"  # НДС 20%
                    })
                
                receipt_data = {
                    "FfdVersion": "1.05",
                    "Taxation": "osn",  # Общая система налогообложения
                    "Items": receipt_items,
                    "Payments": {
                        "Electronic": amount_kopecks
                    }
                }
                
                # Добавляем Email или Phone (обязательно для чека)
                if customer_email:
                    receipt_data["Email"] = customer_email
                    params["Receipt"] = receipt_data
                elif customer_phone:
                    receipt_data["Phone"] = customer_phone
                    params["Receipt"] = receipt_data
                else:
                    # Если нет ни email, ни телефона, не передаем чек
                    logger.warning("No email or phone provided, skipping receipt")
            
            # Генерируем токен
            token = self._generate_token(params)
            params["Token"] = token
            
            logger.info(f"Creating TBank payment for order {order_id}, amount: {amount}")
            logger.info(f"Unique OrderId: {unique_order_id}")
            logger.info(f"API URL: {self.api_url}/v2/Init")
            logger.info(f"Params: {params}")
            
            # Отправляем запрос к API
            response = self.session.post(
                f"{self.api_url}/v2/Init",
                json=params,
                timeout=30
            )
            
            logger.info(f"TBank API response status: {response.status_code}")
            logger.info(f"TBank API response: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"TBank payment created successfully: {data}")
                return data
            else:
                logger.error(f"TBank API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"TBank payment creation error: {e}")
            return None
    
    def get_payment_status(self, payment_id):
        """
        Получение статуса платежа
        
        Args:
            payment_id (str): ID платежа в Т-Банк
            
        Returns:
            dict: Статус платежа или None в случае ошибки
        """
        try:
            payload = {
                "terminal": self.terminal,
                "password": self.password,
                "payment_id": payment_id
            }
            
            response = self.session.post(
                f"{self.api_url}/payments/status",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"TBank payment status: {data}")
                return data
            else:
                logger.error(f"TBank status check error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"TBank status check error: {e}")
            return None
    
    def refund_payment(self, payment_id, amount=None):
        """
        Возврат платежа
        
        Args:
            payment_id (str): ID платежа в Т-Банк
            amount (Decimal, optional): Сумма возврата (если None - полный возврат)
            
        Returns:
            dict: Результат возврата или None в случае ошибки
        """
        try:
            payload = {
                "terminal": self.terminal,
                "password": self.password,
                "payment_id": payment_id
            }
            
            if amount:
                payload["amount"] = int(amount * 100)
            
            response = self.session.post(
                f"{self.api_url}/payments/refund",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"TBank refund successful: {data}")
                return data
            else:
                logger.error(f"TBank refund error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"TBank refund error: {e}")
            return None


def create_tbank_payment(order_id, amount, description="Оплата заказа", order_items=None, customer_email=None, customer_phone=None):
    """
    Удобная функция для создания платежа
    """
    service = TBankPaymentService()
    return service.create_payment(order_id, amount, description, order_items, customer_email, customer_phone)


def get_tbank_payment_status(payment_id):
    """
    Удобная функция для проверки статуса платежа
    """
    service = TBankPaymentService()
    return service.get_payment_status(payment_id)
