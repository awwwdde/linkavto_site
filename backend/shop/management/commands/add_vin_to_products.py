from django.core.management.base import BaseCommand
from shop.models import Product
import random
import string


class Command(BaseCommand):
    help = 'Добавляет VIN-номера к оригинальным товарам'

    def generate_vin(self):
        """Генерирует реалистичный VIN-номер (17 символов)"""
        # VIN состоит из букв (кроме I, O, Q) и цифр
        allowed_letters = 'ABCDEFGHJKLMNPRSTUVWXYZ'
        allowed_chars = allowed_letters + '0123456789'
        
        # WMI (World Manufacturer Identifier) - первые 3 символа
        wmi_codes = {
            'audi': ['WAU', 'TRU'],
            'bmw': ['WBA', 'WBS', 'WBX'],
            'mercedes': ['WDB', 'WDD', 'WDF'],
            'volkswagen': ['WVW', 'WVG', '3VW'],
            'toyota': ['JTD', 'JTE', '5TE'],
            'honda': ['JHM', '1HG', '2HG'],
            'ford': ['1FA', '1FB', '1FT'],
            'hyundai': ['KMH', '5NP'],
        }
        
        # Случайный WMI
        wmi = random.choice(list(wmi_codes.values()))
        if isinstance(wmi, list):
            wmi = random.choice(wmi)
        else:
            wmi = random.choice(['WVW', 'JTD', '1FA'])
        
        # VDS (Vehicle Descriptor Section) - символы 4-9
        vds = ''.join(random.choices(allowed_chars, k=6))
        
        # VIS (Vehicle Identifier Section) - символы 10-17
        # 10-й символ - год (используем буквы для годов 2010+)
        year_codes = 'ABCDEFGHJKLMNPR'  # A=2010, B=2011, и т.д.
        year = random.choice(year_codes)
        
        # 11-й символ - завод
        plant = random.choice(allowed_letters)
        
        # 12-17 - серийный номер
        serial = ''.join(random.choices('0123456789', k=6))
        
        return wmi + vds + year + plant + serial

    def handle(self, *args, **options):
        # Получаем все оригинальные товары
        original_products = Product.objects.filter(
            is_original=True,
            vin__isnull=True
        )

        total_count = original_products.count()
        updated_count = 0

        self.stdout.write(
            self.style.HTTP_INFO(f'\n🔍 Найдено оригинальных товаров без VIN: {total_count}')
        )

        for product in original_products:
            # Генерируем VIN
            vin = self.generate_vin()
            
            # Обновляем товар
            product.vin = vin
            product.save(update_fields=['vin'])
            
            updated_count += 1
            
            if updated_count % 20 == 0:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Обработано {updated_count} из {total_count}...')
                )

        # Также добавим VIN к некоторым неоригинальным товарам (10-15%)
        non_original_products = Product.objects.filter(
            is_original=False,
            vin__isnull=True
        )

        # Выбираем случайные 15% товаров
        sample_count = int(non_original_products.count() * 0.15)
        sample_products = random.sample(list(non_original_products), min(sample_count, non_original_products.count()))

        added_to_non_original = 0
        for product in sample_products:
            vin = self.generate_vin()
            product.vin = vin
            product.save(update_fields=['vin'])
            added_to_non_original += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                f'Готово!\n'
                f'VIN добавлены к оригинальным товарам: {updated_count}\n'
                f'VIN добавлены к неоригинальным товарам: {added_to_non_original}\n'
                f'Всего товаров с VIN: {updated_count + added_to_non_original}\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
            )
        )
        
        # Проверка: выводим несколько примеров
        self.stdout.write(self.style.HTTP_INFO('\n📋 Примеры сгенерированных VIN:'))
        sample_vins = Product.objects.filter(vin__isnull=False).order_by('?')[:5]
        for product in sample_vins:
            original_mark = '🟢 [ОРИГИНАЛ]' if product.is_original else '⚪ [АНАЛОГ]'
            self.stdout.write(
                self.style.SUCCESS(f'  {original_mark} {product.name[:50]}... → {product.vin}')
            )

