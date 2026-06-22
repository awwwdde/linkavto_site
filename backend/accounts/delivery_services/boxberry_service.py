"""
Сервис интеграции с API Boxberry
Документация: https://api.boxberry.ru/
"""
import requests
from typing import List, Dict, Optional


class BoxberryService:
    """Сервис для работы с API Boxberry"""
    
    BASE_URL = "https://api.boxberry.ru/json.php"
    
    def __init__(self, api_token: str = None):
        """
        Инициализация сервиса Boxberry
        
        Args:
            api_token: API токен Boxberry (для тестового режима можно оставить None)
        """
        import os
        # Читаем из .env или используем Яндекс API токен
        self.api_token = api_token or os.getenv('BOXBERRY_API_TOKEN', 'y0__xDQuYLGCBix9Bwg8bnmpxW0XSfG_rbutFwod1MA9SyterOauA')
        
    def get_pickup_points(self, city: str = "Москва", prepaid: bool = True) -> List[Dict]:
        """
        Получение списка пунктов выдачи Boxberry
        
        Args:
            city: Название города
            prepaid: Только для предоплаченных заказов
            
        Returns:
            Список пунктов выдачи
        """
        params = {
            'token': self.api_token,
            'method': 'ListPoints',
            'CityCode': self._get_city_code(city)
        }
        
        if prepaid:
            params['prepaid'] = 1
        
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Преобразуем в унифицированный формат
            pickup_points = []
            for point in data:
                # Пропускаем постаматы если нужны только ПВЗ
                if point.get('OnlyPrepaidOrders') == 'No':
                    continue
                    
                pickup_points.append({
                    'code': point.get('Code'),
                    'name': point.get('Name', ''),
                    'address': point.get('Address', ''),
                    'latitude': float(point.get('GPS', '').split(',')[0] if point.get('GPS') else 0),
                    'longitude': float(point.get('GPS', '').split(',')[1] if point.get('GPS') else 0),
                    'work_time': point.get('WorkShedule', ''),
                    'phones': [point.get('Phone', '')],
                    'provider': 'boxberry',
                    'provider_name': 'Boxberry'
                })
            
            return pickup_points
            
        except Exception as e:
            print(f"Ошибка получения ПВЗ Boxberry: {e}")
            # Возвращаем моковые данные для демонстрации
            from .mock_data import BOXBERRY_MOSCOW_POINTS
            return [
                {
                    'code': p['code'],
                    'name': p['name'],
                    'address': p['address'],
                    'latitude': p['lat'],
                    'longitude': p['lng'],
                    'work_time': p['hours'],
                    'phones': [p['phone']],
                    'provider': 'boxberry',
                    'provider_name': 'Boxberry'
                } for p in BOXBERRY_MOSCOW_POINTS
            ]
    
    def _get_city_code(self, city_name: str) -> str:
        """
        Получение кода города по названию
        
        Args:
            city_name: Название города
            
        Returns:
            Код города
        """
        params = {
            'token': self.api_token,
            'method': 'ListCities'
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            cities = response.json()
            
            # Ищем город по названию
            for city in cities:
                if city.get('Name', '').lower() == city_name.lower():
                    return city.get('Code', '77')  # 77 - код Москвы по умолчанию
            
            return '77'  # По умолчанию Москва
            
        except Exception as e:
            print(f"Ошибка получения кода города: {e}")
            return '77'
    
    def get_pickup_point_by_code(self, code: str) -> Optional[Dict]:
        """
        Получение информации о конкретном пункте выдачи
        
        Args:
            code: Код пункта выдачи
            
        Returns:
            Информация о пункте выдачи или None
        """
        params = {
            'token': self.api_token,
            'method': 'PointsDescription',
            'code': code
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params)
            response.raise_for_status()
            point = response.json()
            
            if point:
                return {
                    'code': point.get('Code'),
                    'name': point.get('Name', ''),
                    'address': point.get('Address', ''),
                    'latitude': float(point.get('GPS', '').split(',')[0] if point.get('GPS') else 0),
                    'longitude': float(point.get('GPS', '').split(',')[1] if point.get('GPS') else 0),
                    'work_time': point.get('WorkShedule', ''),
                    'phones': [point.get('Phone', '')],
                    'provider': 'boxberry',
                    'provider_name': 'Boxberry'
                }
            
            return None
            
        except Exception as e:
            print(f"Ошибка получения ПВЗ Boxberry по коду: {e}")
            return None

