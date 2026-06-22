"""
Сервис интеграции с API СДЭК
Документация: https://apidoc.cdek.ru
"""
import requests
from typing import List, Dict, Optional
import os
import logging
import time
from django.conf import settings

logger = logging.getLogger(__name__)


class CDEKService:
    """Сервис для работы с API СДЭК"""
    
    BASE_URL = "https://api.cdek.ru/v2"  # Продакшн API
    
    def __init__(self, client_id: str = None, client_secret: str = None):
        """
        Инициализация сервиса СДЭК
        
        Args:
            client_id: ID клиента СДЭК
            client_secret: Секретный ключ клиента СДЭК
        """
        # Получаем токены из Django settings
        self.client_id = client_id or getattr(settings, 'CDEK_CLIENT_ID', '')
        self.client_secret = client_secret or getattr(settings, 'CDEK_CLIENT_SECRET', '')
        self.token = None
        self.token_expires_at = 0
        
        if not self.client_id or not self.client_secret:
            logger.warning("CDEK_CLIENT_ID or CDEK_CLIENT_SECRET not set. CDEK API may not work.")
    
    def _get_token(self) -> Optional[str]:
        """
        Получение OAuth токена с кэшированием
        
        Returns:
            Токен доступа или None при ошибке
        """
        # Проверяем, не истек ли токен (обновляем за 60 секунд до истечения)
        if self.token and self.token_expires_at > time.time() + 60:
            return self.token
        
        url = f"{self.BASE_URL}/oauth/token"
        params = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret
        }
        
        try:
            response = requests.post(url, data=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            self.token = data.get('access_token')
            expires_in = data.get('expires_in', 3600)  # По умолчанию 1 час
            self.token_expires_at = time.time() + expires_in
            logger.info("CDEK token obtained successfully.")
            return self.token
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error getting CDEK token: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"CDEK token error response: {error_data}")
                except:
                    logger.error(f"CDEK token error text: {e.response.text[:500]}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error getting CDEK token: {e}")
            return None
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Получение заголовков для запросов к API
        
        Returns:
            Словарь с заголовками авторизации
        """
        token = self._get_token()
        if not token:
            return {}
        
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    
    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Dict = None,
        data: Dict = None
    ) -> Optional[Dict]:
        """
        Выполнение HTTP запроса к API
        
        Args:
            method: HTTP метод (GET, POST, etc.)
            endpoint: Endpoint API (без BASE_URL)
            params: GET параметры
            data: POST данные
            
        Returns:
            Ответ API в виде словаря или None при ошибке
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_headers()
        
        if not headers:
            logger.error("Failed to get CDEK authorization token.")
            return None
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=15)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, params=params, headers=headers, timeout=15)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error CDEK API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"CDEK API error details: {error_data}")
                except:
                    logger.error(f"CDEK API error text: {e.response.text[:500]}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error CDEK API: {e}")
            return None
    
    def get_pickup_points(
        self, 
        city: str = "Москва", 
        latitude: float = None, 
        longitude: float = None
    ) -> List[Dict]:
        """
        Получение списка пунктов выдачи СДЭК
        
        Args:
            city: Название города
            latitude: Широта для поиска ближайших ПВЗ
            longitude: Долгота для поиска ближайших ПВЗ
            
        Returns:
            Список пунктов выдачи в унифицированном формате
        """
        endpoint = "/deliverypoints"
        params = {
            'type': 'PVZ',  # Только пункты выдачи
        }
        
        # Если указан город, добавляем его в параметры
        if city:
            params['city'] = city
        
        # Если указаны координаты, добавляем их
        if latitude and longitude:
            params['latitude'] = latitude
            params['longitude'] = longitude
        
        data = self._make_request('GET', endpoint, params=params)
        
        if not data:
            logger.warning(f"API СДЭК не вернул данных для города: {city}")
            return []
        
        # API может возвращать массив или объект с массивом
        points = []
        if isinstance(data, list):
            points = data
        elif isinstance(data, dict):
            if 'items' in data:
                points = data['items']
            elif 'deliverypoints' in data:
                points = data['deliverypoints']
            else:
                # Может быть один объект
                points = [data] if data else []
        
        if not points:
            logger.warning(f"No pickup points found for city: {city}")
            return []
        
        # Нормализуем данные в унифицированный формат
        pickup_points = []
        for point in points:
            normalized_point = self._normalize_point(point)
            if normalized_point:
                pickup_points.append(normalized_point)
        
        logger.info(f"Fetched {len(pickup_points)} CDEK pickup points.")
        return pickup_points
    
    def _normalize_point(self, point: Dict) -> Optional[Dict]:
        """
        Нормализация данных точки в унифицированный формат
        
        Args:
            point: Данные точки из API
            
        Returns:
            Словарь в унифицированном формате или None
        """
        try:
            # Извлекаем координаты
            location = point.get('location', {})
            lat = location.get('latitude')
            lon = location.get('longitude')
            
            # Пробуем разные варианты получения координат
            if not lat:
                lat = point.get('latitude')
            if not lon:
                lon = point.get('longitude')
            
            if lat and lon:
                try:
                    latitude = float(lat)
                    longitude = float(lon)
                except (ValueError, TypeError):
                    logger.warning(f"Skipping CDEK point {point.get('code')} due to invalid coordinates.")
                    return None
            else:
                logger.warning(f"Skipping CDEK point {point.get('code')} due to missing coordinates.")
                return None
            
            # Извлекаем адрес
            address = location.get('address_full') or location.get('address') or point.get('address', '')
            
            # Извлекаем название
            name = point.get('name', '')
            
            # Извлекаем режим работы
            work_time = point.get('work_time', '') or point.get('workTime', '')
            
            # Извлекаем телефоны (обрабатываем формат {number: "+78001000000"})
            phones = []
            phone = ''
            
            # Проверяем массив phones
            phones_raw = point.get('phones', [])
            if phones_raw and isinstance(phones_raw, list):
                for phone_item in phones_raw:
                    if isinstance(phone_item, dict):
                        # Если это объект с полем number
                        phone_number = phone_item.get('number', '')
                        if phone_number:
                            phones.append(phone_number)
                            if not phone:  # Первый телефон как основной
                                phone = phone_number
                    elif isinstance(phone_item, str):
                        # Если это уже строка
                        phones.append(phone_item)
                        if not phone:
                            phone = phone_item
            
            # Если phones пуст, проверяем поле phone
            if not phones:
                phone_raw = point.get('phone', '')
                if phone_raw:
                    if isinstance(phone_raw, dict):
                        # Если phone - это объект с полем number
                        phone = phone_raw.get('number', '')
                        if phone:
                            phones = [phone]
                    elif isinstance(phone_raw, str):
                        # Если phone - это строка
                        phone = phone_raw
                        phones = [phone]
            
            return {
                'code': point.get('code', ''),
                'name': name or 'Пункт выдачи СДЭК',
                'address': address or 'Адрес не указан',
                'full_address': address or 'Адрес не указан',
                'latitude': latitude,
                'longitude': longitude,
                'work_time': work_time or 'Уточняйте режим работы',
                'phone': phone,
                'phones': phones,
                'provider': 'cdek',
                'provider_name': 'СДЭК'
            }
        except Exception as e:
            logger.warning(f"Error normalizing CDEK point: {e}")
            return None
    
    def get_pickup_point_by_code(self, code: str) -> Optional[Dict]:
        """
        Получение детальной информации о пункте выдачи по коду
        
        Args:
            code: Код пункта выдачи
            
        Returns:
            Словарь с информацией о пункте выдачи или None
        """
        endpoint = "/deliverypoints"
        params = {'code': code}
        
        data = self._make_request('GET', endpoint, params=params)
        
        if not data:
            return None
        
        # API может возвращать массив или один объект
        if isinstance(data, list):
            if not data:
                return None
            point = data[0]
        elif isinstance(data, dict):
            point = data
        else:
            return None
        
        return self._normalize_point(point)

