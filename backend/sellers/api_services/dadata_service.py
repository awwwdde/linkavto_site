"""
Сервис для работы с DaData API для получения информации об организациях по ИНН
Документация: https://dadata.ru/api/find-party/
"""
import requests
import logging
from typing import Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

DADATA_API_URL = "https://suggestions.dadata.ru/suggestions/api/4_1/rs"
DADATA_TOKEN = getattr(settings, 'DADATA_TOKEN', '')


class DaDataService:
    """Сервис для работы с DaData API для поиска организаций"""
    
    def __init__(self):
        """Инициализация сервиса с токеном из настроек Django"""
        self.token = DADATA_TOKEN
        if not self.token:
            logger.warning("DADATA_TOKEN не настроен в settings")
    
    def _get_headers(self) -> Dict[str, str]:
        """
        Получение заголовков для запросов к DaData API
        
        Returns:
            Словарь с заголовками авторизации
        """
        return {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Authorization': f'Token {self.token}'
        }
    
    def get_company_by_inn(self, inn: str) -> Optional[Dict]:
        """
        Получение информации об организации по ИНН через DaData API
        
        Args:
            inn: ИНН организации (10 или 12 цифр)
            
        Returns:
            Словарь с нормализованными данными компании или None при ошибке
            Формат:
            {
                'company_name': str,
                'legal_form': str,  # 'ip', 'ooo', 'ao'
                'inn': str,
                'ogrn': str,
                'legal_address': str,
                'actual_address': str | None
            }
        """
        if not inn or not inn.strip():
            logger.error("ИНН не указан")
            return None
        
        inn = inn.strip()
        
        # Проверка формата ИНН
        if not inn.isdigit() or (len(inn) != 10 and len(inn) != 12):
            logger.error(f"Некорректный формат ИНН: {inn}")
            return None
        
        if not self.token:
            logger.error("DADATA_TOKEN не настроен")
            return None
        
        url = f"{DADATA_API_URL}/findById/party"
        payload = {
            'query': inn
        }
        
        logger.info(f"DaData: запрос информации об организации по ИНН {inn}")
        
        try:
            response = requests.post(
                url,
                json=payload,
                headers=self._get_headers(),
                timeout=15
            )
            response.raise_for_status()
            data = response.json()
            
            # DaData возвращает массив suggestions
            suggestions = data.get('suggestions', [])
            
            if not suggestions:
                logger.warning(f"DaData: организация с ИНН {inn} не найдена")
                return None
            
            # Берем первый результат (наиболее релевантный)
            suggestion = suggestions[0]
            company_data = suggestion.get('data', {})
            
            # Нормализуем данные
            normalized = self._normalize_company_data(company_data, inn)
            
            if normalized:
                logger.info(f"DaData: успешно получены данные для ИНН {inn}")
                # Добавляем полные исходные данные из API для сохранения
                normalized['raw_api_data'] = company_data
                normalized['full_response'] = suggestion
            
            return normalized
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"DaData API HTTP ошибка: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_data = e.response.json()
                    logger.error(f"Детали ошибки: {error_data}")
                except:
                    logger.error(f"Текст ошибки: {e.response.text[:500]}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"DaData API ошибка запроса: {e}")
            return None
    
    def _normalize_company_data(self, data: Dict, inn: str) -> Optional[Dict]:
        """
        Нормализация данных компании из DaData в формат для формы регистрации
        
        Args:
            data: Данные компании из DaData API
            inn: ИНН компании
            
        Returns:
            Нормализованный словарь с данными или None
        """
        try:
            # Полное наименование компании
            company_name = data.get('name', {}).get('full_with_opf', '') or \
                          data.get('name', {}).get('full', '') or \
                          data.get('name', {}).get('short_with_opf', '') or \
                          data.get('name', {}).get('short', '')
            
            if not company_name:
                logger.warning("Не найдено наименование компании")
                return None
            
            # Определяем форму собственности
            legal_form = self._map_legal_form(data)
            
            # ОГРН/ОГРНИП
            ogrn = data.get('ogrn', '') or data.get('ogrn_date', '')
            
            # Юридический адрес
            legal_address = self._extract_address(data.get('address', {}))
            
            # Фактический адрес (если отличается от юридического)
            actual_address = None
            # Проверяем наличие фактического адреса в отдельном поле
            if data.get('address_actual'):
                actual_address = self._extract_address(data.get('address_actual', {}))
            # Если фактический адрес совпадает с юридическим или не указан, не заполняем его
            if actual_address == legal_address or not actual_address:
                actual_address = None
            
            return {
                'company_name': company_name,
                'legal_form': legal_form,
                'inn': inn,
                'ogrn': ogrn,
                'legal_address': legal_address or '',
                'actual_address': actual_address
            }
            
        except Exception as e:
            logger.error(f"Ошибка нормализации данных компании: {e}")
            return None
    
    def _map_legal_form(self, data: Dict) -> str:
        """
        Маппинг типа организации из DaData на значения формы
        
        Args:
            data: Данные компании из DaData
            
        Returns:
            'ip', 'ooo' или 'ao'
        """
        # Тип организации из DaData
        org_type = data.get('type', '')
        company_name = data.get('name', {}).get('full_with_opf', '') or \
                      data.get('name', {}).get('full', '') or \
                      data.get('name', {}).get('short_with_opf', '') or \
                      data.get('name', {}).get('short', '')
        
        # INDIVIDUAL означает ИП
        if org_type == 'INDIVIDUAL':
            return 'ip'
        
        # LEGAL означает юридическое лицо
        if org_type == 'LEGAL':
            # Проверяем название на наличие АО
            company_name_upper = company_name.upper()
            if 'АО' in company_name_upper or 'АКЦИОНЕРНОЕ' in company_name_upper or \
               'ПАО' in company_name_upper or 'ПУБЛИЧНОЕ АКЦИОНЕРНОЕ' in company_name_upper:
                return 'ao'
            # Остальные юридические лица считаем ООО
            return 'ooo'
        
        # По умолчанию ООО, если тип не определен
        logger.warning(f"Неизвестный тип организации: {org_type}, используется 'ooo'")
        return 'ooo'
    
    def _extract_address(self, address_data: Dict) -> str:
        """
        Извлечение полного адреса из структуры DaData
        
        Args:
            address_data: Данные адреса из DaData
            
        Returns:
            Полный адрес в виде строки
        """
        # Если есть готовое значение адреса
        if isinstance(address_data, str):
            return address_data
        
        # Извлекаем значение из объекта
        address_value = address_data.get('value', '') or address_data.get('unrestricted_value', '')
        
        if address_value:
            return address_value
        
        # Если нет готового значения, собираем из частей
        address_parts = []
        
        # Структура адреса в DaData
        if address_data.get('data'):
            addr_data = address_data.get('data', {})
            
            # Регион
            if addr_data.get('region_with_type'):
                address_parts.append(addr_data['region_with_type'])
            elif addr_data.get('region'):
                address_parts.append(addr_data['region'])
            
            # Город/Населенный пункт
            if addr_data.get('city_with_type'):
                address_parts.append(addr_data['city_with_type'])
            elif addr_data.get('city'):
                address_parts.append(addr_data['city'])
            elif addr_data.get('settlement_with_type'):
                address_parts.append(addr_data['settlement_with_type'])
            elif addr_data.get('settlement'):
                address_parts.append(addr_data['settlement'])
            
            # Улица
            if addr_data.get('street_with_type'):
                street = addr_data['street_with_type']
                if addr_data.get('house'):
                    street += f", д. {addr_data['house']}"
                if addr_data.get('block'):
                    street += f", корп. {addr_data['block']}"
                if addr_data.get('flat'):
                    street += f", кв. {addr_data['flat']}"
                address_parts.append(street)
            elif addr_data.get('street'):
                street = addr_data['street']
                if addr_data.get('house'):
                    street += f", д. {addr_data['house']}"
                address_parts.append(street)
        
        # Собираем адрес
        full_address = ', '.join(filter(None, address_parts))
        
        return full_address if full_address else ''
