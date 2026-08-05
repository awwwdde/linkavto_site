import re
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)


VIN_CYRILLIC_TO_LATIN = str.maketrans({
    'А': 'A',
    'В': 'B',
    'Е': 'E',
    'К': 'K',
    'М': 'M',
    'Н': 'H',
    'О': 'O',
    'Р': 'P',
    'С': 'C',
    'Т': 'T',
    'У': 'Y',
    'Х': 'X',
})


class VINService:
    """Сервис для работы с VIN номерами"""
    
    @staticmethod
    def normalize_vin(vin):
        """Normalize VIN before validation and storing."""
        if not vin:
            return ''

        vin = str(vin).upper().translate(VIN_CYRILLIC_TO_LATIN)
        return ''.join(char for char in vin if char.isalnum())

    @staticmethod
    def validate_vin(vin):
        """
        Валидация VIN номера
        
        Args:
            vin: VIN номер для проверки
            
        Returns:
            dict: {'valid': bool, 'error': str or None}
        """
        if not vin:
            return {'valid': False, 'error': 'VIN номер не может быть пустым'}
        
        # Убираем пробелы и приводим к верхнему регистру
        vin = VINService.normalize_vin(vin)
        
        # Проверяем длину
        if len(vin) != 17:
            return {
                'valid': False,
                'error': 'VIN номер должен содержать ровно 17 символов',
                'normalized_vin': vin,
            }
            return {'valid': False, 'error': 'VIN номер должен содержать ровно 17 символов'}
        
        # Проверяем допустимые символы (только цифры и латинские буквы, кроме I, O, Q)
        if not re.match(r'^[A-HJ-NPR-Z0-9]{17}$', vin):
            return {
                'valid': False,
                'error': 'VIN содержит недопустимые символы: разрешены цифры и латинские буквы, кроме I, O, Q',
                'normalized_vin': vin,
            }
            return {'valid': False, 'error': 'VIN номер содержит недопустимые символы (не допускаются I, O, Q)'}
        
        # Контрольная сумма (9-й символ) проверяется только у североамериканских VIN (WMI 1–5).
        # У европейских и других VIN на 9-й позиции может быть произвольный символ — не отклоняем.
        wmi_first = vin[0]
        if wmi_first in '12345' and not VINService._check_vin_checksum(vin):
            return {
                'valid': False,
                'error': 'Неверная контрольная сумма VIN номера',
                'normalized_vin': vin,
            }
            return {'valid': False, 'error': 'Неверная контрольная сумма VIN номера'}
        
        return {'valid': True, 'error': None, 'normalized_vin': vin}
    
    @staticmethod
    def _check_vin_checksum(vin):
        """
        Проверка контрольной суммы VIN номера
        
        Args:
            vin: VIN номер (17 символов)
            
        Returns:
            bool: True если контрольная сумма верна
        """
        # Таблица весов позиций
        weights = [8, 7, 6, 5, 4, 3, 2, 10, 0, 9, 8, 7, 6, 5, 4, 3, 2]
        
        # Таблица значений символов
        transliteration = {
            'A': 1, 'B': 2, 'C': 3, 'D': 4, 'E': 5, 'F': 6, 'G': 7, 'H': 8,
            'J': 1, 'K': 2, 'L': 3, 'M': 4, 'N': 5, 'P': 7, 'R': 9,
            'S': 2, 'T': 3, 'U': 4, 'V': 5, 'W': 6, 'X': 7, 'Y': 8, 'Z': 9
        }
        
        try:
            total = 0
            for i, char in enumerate(vin):
                if char.isdigit():
                    value = int(char)
                else:
                    value = transliteration.get(char, 0)
                total += value * weights[i]
            
            # Вычисляем контрольную цифру
            checksum = total % 11
            check_digit = str(checksum) if checksum < 10 else 'X'
            
            # 9-й символ (индекс 8) должен совпадать с контрольной цифрой
            return vin[8] == check_digit
        except Exception as e:
            logger.error(f"Error checking VIN checksum: {e}")
            # Если не удалось проверить контрольную сумму, считаем VIN валидным
            # (многие производители не используют контрольную сумму)
            return True
    
    @staticmethod
    def decode_vin(vin):
        """
        Декодирование VIN номера
        
        Args:
            vin: VIN номер
            
        Returns:
            dict: Информация о транспортном средстве
        """
        vin = VINService.normalize_vin(vin)
        validation = VINService.validate_vin(vin)
        if not validation['valid']:
            return {'success': False, 'error': validation['error']}
        
        
        # Базовая информация из VIN
        info = {
            'success': True,
            'valid': True,
            'vin': vin,
            'normalized_vin': vin,
            'wmi': vin[:3],  # World Manufacturer Identifier
            'vds': vin[3:9],  # Vehicle Descriptor Section
            'vis': vin[9:],   # Vehicle Identifier Section
        }
        
        # Определяем регион производителя по WMI
        wmi_first = vin[0]
        if wmi_first in 'ABCDEFGH':
            info['region'] = 'Африка'
        elif wmi_first in 'JKL':
            info['region'] = 'Азия (Япония, Корея)'
        elif wmi_first in 'MNP':
            info['region'] = 'Азия (Китай, Индия и др.)'
        elif wmi_first in 'R':
            info['region'] = 'Азия (Тайвань)'
        elif wmi_first in 'STU':
            info['region'] = 'Европа'
        elif wmi_first in 'VW':
            info['region'] = 'Европа (Франция, Испания)'
        elif wmi_first in 'X':
            info['region'] = 'Россия, СНГ'
        elif wmi_first in 'YZ':
            info['region'] = 'Европа (Скандинавия, Италия)'
        elif wmi_first in '12345':
            info['region'] = 'Северная Америка'
        elif wmi_first in '6789':
            info['region'] = 'Океания'
        else:
            info['region'] = 'Неизвестно'
        
        # Год выпуска (10-й символ)
        year_code = vin[9]
        info['year'] = VINService._decode_year(year_code)
        
        return info
    
    @staticmethod
    def _decode_year(code):
        """Декодирование года выпуска из VIN"""
        # Таблица соответствия кода году
        year_codes = {
            'A': 1980, 'B': 1981, 'C': 1982, 'D': 1983, 'E': 1984,
            'F': 1985, 'G': 1986, 'H': 1987, 'J': 1988, 'K': 1989,
            'L': 1990, 'M': 1991, 'N': 1992, 'P': 1993, 'R': 1994,
            'S': 1995, 'T': 1996, 'V': 1997, 'W': 1998, 'X': 1999,
            'Y': 2000, '1': 2001, '2': 2002, '3': 2003, '4': 2004,
            '5': 2005, '6': 2006, '7': 2007, '8': 2008, '9': 2009,
        }
        
        # Коды повторяются каждые 30 лет
        base_year = year_codes.get(code)
        if base_year:
            # Определяем, какой период более вероятен
            from datetime import datetime
            current_year = datetime.now().year
            
            # Проверяем периоды: base_year, base_year+30, base_year+60
            possible_years = [base_year, base_year + 30]
            if base_year + 60 <= current_year + 1:
                possible_years.append(base_year + 60)
            
            # Выбираем ближайший год, не превышающий текущий+1
            valid_years = [y for y in possible_years if y <= current_year + 1]
            if valid_years:
                return max(valid_years)
        
        return None


class LicensePlateService:
    """Сервис для работы с госномерами"""
    
    # Регулярные выражения для различных типов номеров РФ
    PATTERNS = {
        'standard': r'^[АВЕКМНОРСТУХ]\d{3}[АВЕКМНОРСТУХ]{2}\d{2,3}$',  # А123ВС77
        'trailer': r'^\d{4}[АВЕКМНОРСТУХ]{2}\d{2,3}$',  # 1234АВ77
        'transit': r'^[АВЕКМНОРСТУХ]{2}\d{4}\d{2,3}$',  # АВ123477
    }
    
    @staticmethod
    def validate_license_plate(plate):
        """
        Валидация госномера
        
        Args:
            plate: Госномер для проверки
            
        Returns:
            dict: {'valid': bool, 'error': str or None, 'type': str}
        """
        if not plate:
            return {'valid': False, 'error': 'Госномер не может быть пустым', 'type': None}
        
        # Убираем пробелы и приводим к верхнему регистру
        plate = plate.replace(' ', '').upper()
        
        # Проверяем по паттернам
        for plate_type, pattern in LicensePlateService.PATTERNS.items():
            if re.match(pattern, plate):
                return {'valid': True, 'error': None, 'type': plate_type}
        
        # Если не подошел ни один паттерн, возможно это нестандартный номер
        # Принимаем его, но отмечаем как неизвестный тип
        if 5 <= len(plate) <= 15:
            return {'valid': True, 'error': None, 'type': 'other'}
        
        return {'valid': False, 'error': 'Неверный формат госномера', 'type': None}


@require_http_methods(['POST'])
def validate_vin_view(request):
    """API endpoint для валидации VIN"""
    import json
    
    try:
        data = json.loads(request.body)
        vin = data.get('vin', '')
        
        result = VINService.validate_vin(vin)
        
        if result['valid']:
            # Пытаемся декодировать VIN
            decoded = VINService.decode_vin(vin)
            return JsonResponse(decoded)
        else:
            return JsonResponse(result, status=400)
            
    except Exception as e:
        logger.error(f"Error validating VIN: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_http_methods(['POST'])
def validate_license_plate_view(request):
    """API endpoint для валидации госномера"""
    import json
    
    try:
        data = json.loads(request.body)
        plate = data.get('license_plate', '')
        
        result = LicensePlateService.validate_license_plate(plate)
        return JsonResponse(result)
            
    except Exception as e:
        logger.error(f"Error validating license plate: {e}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
