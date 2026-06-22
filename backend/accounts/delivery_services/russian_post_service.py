"""
Сервис интеграции с API Почты России
Документация: https://otpravka.pochta.ru/new/specification#/main

Также использует DaData API для получения списка ПВЗ с координатами:
https://dadata.ru/api/suggest/postal_unit/
"""
import requests
from typing import List, Dict, Optional
import os
import logging
import base64
from django.conf import settings

logger = logging.getLogger(__name__)

# DaData API для получения списка ПВЗ Почты России
DADATA_API_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs"
DADATA_TOKEN = getattr(settings, 'DADATA_TOKEN', '')


class RussianPostService:
    """Сервис для работы с API Почты России"""
    
    BASE_URL = "https://otpravka-api.pochta.ru"
    
    def __init__(
        self, 
        access_token: str = None, 
        user_auth_key: str = None,
        login: str = None,
        password: str = None
    ):
        """
        Инициализация сервиса Почты России
        
        Args:
            access_token: Токен доступа к API
            user_auth_key: Base64 ключ авторизации пользователя (login:password)
            login: Логин (email) - используется если user_auth_key не указан
            password: Пароль - используется если user_auth_key не указан
        """
        # Получаем токены из Django settings
        self.access_token = access_token or getattr(settings, 'RUSSIAN_POST_TOKEN', '')
        
        # Сохраняем login и password для использования в X-User-Auth (для passport endpoint)
        self.login = login or os.getenv('RUSSIAN_POST_LOGIN', '')
        self.password = password or os.getenv('RUSSIAN_POST_PASSWORD', '')
        
        # Если указан готовый ключ, используем его
        if user_auth_key:
            self.user_auth_key = user_auth_key
        else:
            # Берём из Django settings
            self.user_auth_key = getattr(settings, 'RUSSIAN_POST_USER_AUTH', '')
            
            # Если ключ не найден, генерируем из login:password
            if not self.user_auth_key and self.login and self.password:
                credentials = f"{self.login}:{self.password}"
                self.user_auth_key = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
                logger.info(f"Сгенерирован Base64 ключ авторизации для {self.login}")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Получение заголовков для запросов к API
        
        Returns:
            Словарь с заголовками авторизации
        """
        headers = {
            'Authorization': f'AccessToken {self.access_token}',
            'X-User-Authorization': f'Basic {self.user_auth_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        logger.debug(f"Заголовки авторизации: Authorization=AccessToken {self.access_token[:10]}..., X-User-Authorization=Basic {self.user_auth_key[:20]}...")
        
        return headers
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Optional[Dict]:
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
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=params, headers=headers, timeout=15)
            elif method.upper() == 'POST':
                response = requests.post(url, json=data, params=params, headers=headers, timeout=15)
            else:
                logger.error(f"Неподдерживаемый HTTP метод: {method}")
                return None
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP ошибка API Почты России: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Статус код: {e.response.status_code}")
                logger.error(f"URL: {url}")
                logger.error(f"Параметры: {params}")
                
                try:
                    error_data = e.response.json()
                    logger.error(f"Детали ошибки: {error_data}")
                    
                    # Если ошибка авторизации, даем подсказку
                    if e.response.status_code == 401:
                        error_code = error_data.get('code', '')
                        error_desc = error_data.get('desc', '')
                        logger.error(f"Ошибка авторизации (401): {error_code} - {error_desc}")
                        logger.error("Проверьте правильность токена доступа и ключа авторизации пользователя")
                        
                except:
                    logger.error(f"Текст ошибки: {e.response.text[:500]}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка запроса к API Почты России: {e}")
            return None
    
    def get_pickup_points(
        self, 
        address: str = "Москва", 
        latitude: float = None, 
        longitude: float = None
    ) -> List[Dict]:
        """
        Получение списка почтовых отделений (устаревший метод)
        Используйте get_nearby_post_offices() или get_post_offices_by_city()
        """
        # Делегируем в новый метод
        if latitude and longitude:
            return self.get_nearby_post_offices(latitude, longitude)
        return self.get_post_offices_by_city(address)
    
    def get_post_offices_by_city(
        self,
        city: str = "Москва",
        top: int = 200,
        filter_mode: str = 'ALL'
    ) -> List[Dict]:
        """
        Получение всех почтовых отделений по названию города/населённого пункта
        через API Почты России /postoffice/1.0/by-address
        
        Args:
            city: Название города или населённого пункта
            top: Максимальное количество результатов
            filter_mode: Режим фильтрации (ALL, WORK_NOW, etc.)
            
        Returns:
            Список почтовых отделений в унифицированном формате
        """
        endpoint = "/postoffice/1.0/by-address"
        params = {
            'address': city,
            'top': top,
            'filter': filter_mode
        }
        
        logger.info(f"API Почты России by-address: city={city}, top={top}")
        data = self._make_request('GET', endpoint, params=params)
        
        if not data:
            logger.warning(f"API /postoffice/1.0/by-address не вернул данных для города: {city}")
            return []
        
        # API возвращает массив объектов отделений
        pickup_points = []
        
        if isinstance(data, list):
            for item in data:
                point = self._normalize_nearby_point(item)
                if point:
                    pickup_points.append(point)
        elif isinstance(data, dict):
            # Если ответ в виде объекта с массивом
            items = data.get('postoffices') or data.get('items') or []
            for item in items:
                point = self._normalize_nearby_point(item)
                if point:
                    pickup_points.append(point)
        
        logger.info(f"API by-address: получено {len(pickup_points)} ПВЗ для города {city}")
        return pickup_points
    
    def _extract_postal_codes(self, data: Dict) -> List[str]:
        """
        Извлечение почтовых индексов из ответа API
        
        Args:
            data: Ответ API
            
        Returns:
            Список почтовых индексов
        """
        postal_codes = []
        
        # API может возвращать данные в разных форматах
        if isinstance(data, list):
            # Если ответ - это массив индексов
            postal_codes = [str(item) for item in data if item]
        elif isinstance(data, dict):
            # Если ответ - это объект с полями
            if 'postoffices' in data:
                # Массив объектов с полем postal-code
                for item in data['postoffices']:
                    if isinstance(item, dict) and 'postal-code' in item:
                        postal_codes.append(str(item['postal-code']))
                    elif isinstance(item, str):
                        postal_codes.append(str(item))
            elif 'postalCodes' in data:
                postal_codes = [str(code) for code in data['postalCodes']]
            elif 'items' in data:
                for item in data['items']:
                    if isinstance(item, dict) and 'postal-code' in item:
                        postal_codes.append(str(item['postal-code']))
                    elif isinstance(item, str):
                        postal_codes.append(str(item))
            elif 'postal-code' in data:
                # Один индекс
                postal_codes.append(str(data['postal-code']))
        
        return postal_codes
    
    def _get_post_office_details(self, postal_code: str) -> Optional[Dict]:
        """
        Получение детальной информации о почтовом отделении по индексу
        Использует endpoint /postoffice/1.0/{postal-code}
        
        Args:
            postal_code: Почтовый индекс
            
        Returns:
            Словарь с информацией о пункте выдачи или None
        """
        # Endpoint с индексом в URL, без параметров
        endpoint = f"/postoffice/1.0/{postal_code}"
        
        logger.info(f"Запрос деталей через /postoffice/1.0/{postal_code} для индекса: {postal_code}")
        data = self._make_request('GET', endpoint, params=None)
        
        if not data:
            logger.warning(f"API /postoffice/1.0/{postal_code} не вернул данных для индекса: {postal_code}")
            return None
        
        logger.info(f"Получены данные от /postoffice/1.0/{postal_code} для индекса: {postal_code}")
        normalized = self._normalize_point_from_v1(data, postal_code)
        
        if not normalized:
            logger.warning(f"Не удалось нормализовать данные для индекса: {postal_code}")
        
        return normalized
    
    def _normalize_point_from_v1(self, data: Dict, postal_code: str) -> Optional[Dict]:
        """
        Нормализация данных из /postoffice/1.0/{postal-code} в унифицированный формат
        
        Args:
            data: Данные из API /postoffice/1.0/{postal-code}
            postal_code: Почтовый индекс
            
        Returns:
            Словарь в унифицированном формате или None
        """
        # Извлекаем координаты
        latitude = None
        longitude = None
        if data.get('latitude'):
            try:
                latitude = float(data['latitude'])
            except (ValueError, TypeError):
                pass
        if data.get('longitude'):
            try:
                longitude = float(data['longitude'])
            except (ValueError, TypeError):
                pass
        
        if not latitude or not longitude:
            logger.warning(f"Skipping Russian Post point {postal_code} due to missing coordinates.")
            return None
        
        # Формируем полный адрес из address-source, settlement, region
        address_parts = []
        if data.get('settlement'):
            address_parts.append(data['settlement'])
        if data.get('region'):
            address_parts.append(data['region'])
        if data.get('address-source'):
            address_parts.append(data['address-source'])
        
        full_address = ", ".join(filter(None, address_parts)) or f"Почтовое отделение {postal_code}"
        
        # Извлекаем телефоны из массива phones
        phones = []
        phone = ''
        if data.get('phones') and isinstance(data['phones'], list):
            for phone_obj in data['phones']:
                if isinstance(phone_obj, dict):
                    town_code = phone_obj.get('phone-town-code', '')
                    number = phone_obj.get('phone-number', '')
                    if town_code and number:
                        full_phone = f"{town_code}{number}"
                        phones.append(full_phone)
                        if not phone:  # Первый телефон как основной
                            phone = full_phone
        
        # Формируем время работы из массива working-hours
        work_time = 'Уточняйте режим работы'
        if data.get('working-hours') and isinstance(data['working-hours'], list):
            schedule_parts = []
            weekday_names = {
                1: 'Пн', 2: 'Вт', 3: 'Ср', 4: 'Чт', 
                5: 'Пт', 6: 'Сб', 7: 'Вс'
            }
            
            for wh in data['working-hours']:
                weekday_id = wh.get('weekday-id')
                begin = wh.get('begin-worktime', '')
                end = wh.get('end-worktime', '')
                
                if weekday_id and begin and end:
                    day_name = weekday_names.get(weekday_id, f"День {weekday_id}")
                    # Берем только время без миллисекунд
                    begin_time = begin[:5] if len(begin) >= 5 else begin
                    end_time = end[:5] if len(end) >= 5 else end
                    
                    time_str = f"{begin_time}-{end_time}"
                    
                    # Проверяем наличие обеда
                    if 'lunches' in wh and isinstance(wh['lunches'], list) and len(wh['lunches']) > 0:
                        lunch = wh['lunches'][0]
                        lunch_begin = lunch.get('begin-lunchtime', '')[:5]
                        lunch_end = lunch.get('end-lunchtime', '')[:5]
                        if lunch_begin and lunch_end:
                            time_str += f" (обед {lunch_begin}-{lunch_end})"
                    
                    schedule_parts.append(f"{day_name}: {time_str}")
            
            if schedule_parts:
                work_time = "; ".join(schedule_parts)
        
        return {
            'code': f"post_{postal_code}",
            'name': f"Почта России {postal_code}",
            'address': full_address,
            'full_address': full_address,
            'latitude': latitude,
            'longitude': longitude,
            'work_time': work_time,
            'phone': phone,
            'phones': phones,
            'provider': 'russian_post',
            'provider_name': 'Почта России',
            'postal_code': postal_code,
            'type_code': data.get('type-code', ''),
            'working_hours': data.get('working-hours', []),  # Сохраняем полное расписание
            'works_on_saturdays': data.get('works-on-saturdays', False),
            'works_on_sundays': data.get('works-on-sundays', False)
        }
    
    def _normalize_point(self, data: Dict, postal_code: str) -> Optional[Dict]:
        """
        Нормализация данных точки в унифицированный формат
        
        Args:
            data: Данные из API
            postal_code: Почтовый индекс
            
        Returns:
            Словарь в унифицированном формате или None
        """
        # Извлекаем адрес
        address_parts = []
        if data.get('settlement-name'):
            address_parts.append(data['settlement-name'])
        if data.get('region-name'):
            address_parts.append(data['region-name'])
        if data.get('street-name'):
            street = data['street-name']
            if data.get('house-number'):
                street += f", д. {data['house-number']}"
            address_parts.append(street)
        
        full_address = ", ".join(filter(None, address_parts))
        
        # Извлекаем координаты
        latitude = None
        longitude = None
        if data.get('latitude'):
            try:
                latitude = float(data['latitude'])
            except (ValueError, TypeError):
                pass
        if data.get('longitude'):
            try:
                longitude = float(data['longitude'])
            except (ValueError, TypeError):
                pass
        
        if not latitude or not longitude:
            logger.warning(f"Skipping Russian Post point {postal_code} due to missing coordinates.")
            return None
        
        return {
            'code': f"post_{postal_code}",
            'name': f"Почтовое отделение {postal_code}",
            'address': full_address or data.get('address', 'Адрес не указан'),
            'full_address': full_address or data.get('address', 'Адрес не указан'),
            'latitude': latitude,
            'longitude': longitude,
            'work_time': data.get('work-time', 'Уточняйте режим работы'),
            'phone': data.get('phone-number', ''),
            'phones': [data.get('phone-number', '')] if data.get('phone-number') else [],
            'provider': 'russian_post',
            'provider_name': 'Почта России',
            'postal_code': postal_code
        }
    
    def get_pickup_point_by_code(self, code: str) -> Optional[Dict]:
        """
        Получение детальной информации о пункте выдачи по коду
        
        Args:
            code: Код пункта выдачи (формат: post_{postal_code})
            
        Returns:
            Словарь с информацией о пункте выдачи или None
        """
        # Извлекаем почтовый индекс из кода
        postal_code = code.replace('post_', '')
        return self._get_post_office_details(postal_code)

    # ==================== DaData API методы ====================
    
    def _get_dadata_headers(self) -> Dict[str, str]:
        """
        Получение заголовков для запросов к DaData API
        
        Returns:
            Словарь с заголовками авторизации
        """
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Token {DADATA_TOKEN}'
        }
    
    def get_pickup_points_dadata(
        self, 
        city: str = "Москва",
        count: int = 50,
        type_code: str = None
    ) -> List[Dict]:
        """
        Получение списка ПВЗ Почты России через DaData API по названию города
        
        Args:
            city: Название города для поиска
            count: Максимальное количество результатов (до 100)
            type_code: Фильтр по типу отделения (ОПС, ГОПС, ПОЧТАМТ, ППС)
            
        Returns:
            Список ПВЗ в унифицированном формате для размещения на карте
        """
        url = f"{DADATA_API_URL}/suggest/postal_unit"
        
        payload = {
            'query': city,
            'count': min(count, 100)  # DaData ограничивает до 100
        }
        
        logger.info(f"DaData: запрос ПВЗ для города '{city}', count={count}")
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                headers=self._get_dadata_headers(),
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            suggestions = data.get('suggestions', [])
            logger.info(f"DaData: получено {len(suggestions)} ПВЗ")
            
            # Нормализуем и фильтруем результаты
            pickup_points = []
            for suggestion in suggestions:
                point = self._normalize_dadata_point(suggestion)
                if point:
                    # Фильтруем по типу, если указан
                    if type_code and point.get('type_code') != type_code:
                        continue
                    pickup_points.append(point)
            
            logger.info(f"DaData: нормализовано {len(pickup_points)} ПВЗ с координатами")
            return pickup_points
            
        except requests.exceptions.RequestException as e:
            logger.error(f"DaData API ошибка: {e}")
            return []
    
    def get_pickup_points_by_location_dadata(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 5000,
        count: int = 20
    ) -> List[Dict]:
        """
        Получение ближайших ПВЗ Почты России по координатам через DaData API
        
        Args:
            latitude: Широта центра поиска
            longitude: Долгота центра поиска
            radius_meters: Радиус поиска в метрах (по умолчанию 5 км)
            count: Максимальное количество результатов
            
        Returns:
            Список ближайших ПВЗ в унифицированном формате
        """
        url = f"{DADATA_API_URL}/geolocate/postal_unit"
        
        payload = {
            'lat': latitude,
            'lon': longitude,
            'radius_meters': radius_meters,
            'count': min(count, 100)
        }
        
        logger.info(f"DaData: поиск ПВЗ по координатам ({latitude}, {longitude}), радиус {radius_meters}м")
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_dadata_headers(),
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            suggestions = data.get('suggestions', [])
            logger.info(f"DaData: найдено {len(suggestions)} ПВЗ в радиусе {radius_meters}м")
            
            # Нормализуем результаты
            pickup_points = []
            for suggestion in suggestions:
                point = self._normalize_dadata_point(suggestion)
                if point:
                    pickup_points.append(point)
            
            return pickup_points
            
        except requests.exceptions.RequestException as e:
            logger.error(f"DaData API ошибка (geolocate): {e}")
            return []
    
    def get_pickup_points_by_kladr_dadata(
        self,
        kladr_id: str,
        count: int = 50
    ) -> List[Dict]:
        """
        Получение ПВЗ Почты России по КЛАДР коду города через DaData API
        
        Args:
            kladr_id: КЛАДР код города (например, '7700000000000' для Москвы)
            count: Максимальное количество результатов
            
        Returns:
            Список ПВЗ в унифицированном формате
        """
        url = f"{DADATA_API_URL}/suggest/postal_unit"
        
        payload = {
            'query': '',
            'count': min(count, 100),
            'filters': [
                {'address_kladr_id': kladr_id}
            ]
        }
        
        logger.info(f"DaData: запрос ПВЗ по КЛАДР '{kladr_id}'")
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_dadata_headers(),
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            suggestions = data.get('suggestions', [])
            logger.info(f"DaData: получено {len(suggestions)} ПВЗ по КЛАДР {kladr_id}")
            
            # Нормализуем результаты
            pickup_points = []
            for suggestion in suggestions:
                point = self._normalize_dadata_point(suggestion)
                if point:
                    pickup_points.append(point)
            
            return pickup_points
            
        except requests.exceptions.RequestException as e:
            logger.error(f"DaData API ошибка (КЛАДР): {e}")
            return []
    
    def _normalize_dadata_point(self, suggestion: Dict) -> Optional[Dict]:
        """
        Нормализация данных ПВЗ из DaData в унифицированный формат
        
        Args:
            suggestion: Объект suggestion из ответа DaData API
            
        Returns:
            Словарь в унифицированном формате для карты или None если нет координат
        """
        data = suggestion.get('data', {})
        
        # Проверяем наличие координат
        geo_lat = data.get('geo_lat')
        geo_lon = data.get('geo_lon')
        
        if not geo_lat or not geo_lon:
            logger.debug(f"DaData: пропуск ПВЗ {data.get('postal_code')} - нет координат")
            return None
        
        try:
            latitude = float(geo_lat)
            longitude = float(geo_lon)
        except (ValueError, TypeError):
            logger.debug(f"DaData: пропуск ПВЗ {data.get('postal_code')} - невалидные координаты")
            return None
        
        postal_code = data.get('postal_code', '')
        address = data.get('address_str', suggestion.get('value', ''))
        
        # Формируем расписание работы
        schedule_parts = []
        schedule_map = {
            'Пн': data.get('schedule_mon'),
            'Вт': data.get('schedule_tue'),
            'Ср': data.get('schedule_wed'),
            'Чт': data.get('schedule_thu'),
            'Пт': data.get('schedule_fri'),
            'Сб': data.get('schedule_sat'),
            'Вс': data.get('schedule_sun')
        }
        
        for day, time in schedule_map.items():
            if time:
                schedule_parts.append(f"{day}: {time}")
        
        work_time = '; '.join(schedule_parts) if schedule_parts else 'Уточняйте режим работы'
        
        # Тип отделения
        type_code = data.get('type_code', 'ОПС')
        
        return {
            'code': f"post_{postal_code}",
            'name': f"Почта России {postal_code}",
            'address': address,
            'full_address': suggestion.get('value', address),
            'latitude': latitude,
            'longitude': longitude,
            'work_time': work_time,
            'schedule': schedule_map,  # Детальное расписание для UI
            'phone': '',
            'phones': [],
            'provider': 'russian_post',
            'provider_name': 'Почта России',
            'postal_code': postal_code,
            'type_code': type_code,
            # Дополнительные данные из DaData
            'region': data.get('region'),
            'city': data.get('city'),
            'settlement': data.get('settlement'),
            'kladr_id': data.get('address_kladr_id')
        }

    # ==================== API Почты России - поиск по координатам ====================
    
    def get_nearby_post_offices(
        self,
        latitude: float,
        longitude: float,
        top: int = 50,
        current_date_time: str = None,
        filter_mode: str = 'ALL'
    ) -> List[Dict]:
        """
        Получение ближайших почтовых отделений по координатам
        через официальный API Почты России
        
        Документация: https://otpravka.pochta.ru/new/specification#/services-postoffice-nearby
        
        Args:
            latitude: Широта
            longitude: Долгота
            top: Максимальное количество результатов (до 100)
            current_date_time: Текущая дата/время в формате ISO (опционально)
            filter_mode: Режим фильтрации (ALL, WORK_NOW, etc.)
            
        Returns:
            Список почтовых отделений в унифицированном формате
        """
        endpoint = "/postoffice/1.0/nearby"
        params = {
            'latitude': latitude,
            'longitude': longitude,
            'top': min(top, 1000),  # API поддерживает до 1000+ точек
            'filter': filter_mode  # Обязательный параметр API
        }
        
        if current_date_time:
            params['current-date-time'] = current_date_time
        
        logger.info(f"API Почты России nearby: lat={latitude}, lon={longitude}, top={top}, filter={filter_mode}")
        data = self._make_request('GET', endpoint, params=params)
        
        if not data:
            logger.warning("API /postoffice/1.0/nearby не вернул данных")
            return []
        
        # Нормализуем ответ - API возвращает массив объектов
        pickup_points = []
        
        if isinstance(data, list):
            for item in data:
                point = self._normalize_nearby_point(item)
                if point:
                    pickup_points.append(point)
        elif isinstance(data, dict) and 'postoffices' in data:
            # Альтернативный формат ответа
            for item in data['postoffices']:
                point = self._normalize_nearby_point(item)
                if point:
                    pickup_points.append(point)
        
        logger.info(f"API nearby: получено {len(pickup_points)} ПВЗ")
        return pickup_points

    def _normalize_nearby_point(self, data: Dict) -> Optional[Dict]:
        """
        Нормализация данных из /postoffice/1.0/nearby в унифицированный формат
        
        Args:
            data: Объект отделения из ответа API
            
        Returns:
            Словарь в унифицированном формате для карты или None
        """
        postal_code = str(data.get('postal-code', data.get('postalCode', '')))
        
        # Проверяем наличие координат
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not latitude or not longitude:
            logger.debug(f"Nearby: пропуск ПВЗ {postal_code} - нет координат")
            return None
        
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (ValueError, TypeError):
            logger.debug(f"Nearby: пропуск ПВЗ {postal_code} - невалидные координаты")
            return None
        
        # Собираем адрес из доступных полей
        address = data.get('address', '')
        if not address:
            address_parts = []
            # Разные варианты полей адреса в API
            settlement = data.get('settlement') or data.get('settlement-name') or data.get('city-name')
            if settlement:
                address_parts.append(settlement)
            
            street = data.get('street') or data.get('street-name')
            if street:
                house = data.get('house') or data.get('house-number') or data.get('building')
                if house:
                    street = f"{street}, д. {house}"
                address_parts.append(street)
            
            address = ", ".join(filter(None, address_parts)) or f"Почтовое отделение {postal_code}"
        
        # Время работы
        work_time = data.get('work-time') or data.get('workTime') or 'Уточняйте режим работы'
        
        # Телефон
        phone = data.get('phone') or data.get('phone-number') or data.get('phoneNumber') or ''
        
        return {
            'code': f"post_{postal_code}",
            'name': f"Почта России {postal_code}",
            'address': address,
            'full_address': address,
            'latitude': latitude,
            'longitude': longitude,
            'work_time': work_time,
            'phone': phone,
            'phones': [phone] if phone else [],
            'provider': 'russian_post',
            'provider_name': 'Почта России',
            'postal_code': postal_code,
            'type_code': data.get('type-office') or data.get('typeOffice') or '',
            'distance': data.get('distance')  # API может вернуть расстояние до точки
        }

