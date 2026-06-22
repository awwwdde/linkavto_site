#!/usr/bin/env python
"""
Финальный скрипт для заполнения базы данных тестовыми данными
Исправлены все ошибки и добавлена проверка уникальности
"""
import os
import sys
import django
from decimal import Decimal
import random

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'avtolink.settings.development')
django.setup()

from shop.models import (
    Category, Product, Manufacturer, CarBrand, 
    OilAndChemistryCategory, OilAndChemistryBrand,
    MaintenanceCategory, MaintenanceBrand
)

def create_final_test_data():
    print("🚀 Создание финальных тестовых данных...")
    
    # 1. Создаем производителей
    print("\n📦 Создание производителей...")
    manufacturers = {}
    manufacturer_data = [
        ("Bosch", "Германия"),
        ("VAG", "Германия"), 
        ("Toyota Motor", "Япония"),
        ("Hyundai Motor", "Корея"),
        ("Castrol", "Великобритания"),
        ("Mobil", "США"),
        ("Liqui Moly", "Германия"),
        ("Shell", "Нидерланды")
    ]
    
    for name, country in manufacturer_data:
        manufacturer, created = Manufacturer.objects.get_or_create(
            name=name,
            defaults={'country': country}
        )
        manufacturers[name] = manufacturer
        print(f"  ✓ {name} ({'создан' if created else 'уже существует'})")
    
    # 2. Создаем бренды автомобилей
    print("\n🚗 Создание брендов автомобилей...")
    car_brands = {}
    car_brand_data = [
        ("Audi", "Германия"),
        ("BMW", "Германия"),
        ("Mercedes-Benz", "Германия"),
        ("Toyota", "Япония"),
        ("Volkswagen", "Германия"),
        ("Honda", "Япония"),
        ("Ford", "США"),
        ("Hyundai", "Корея")
    ]
    
    for name, country in car_brand_data:
        brand, created = CarBrand.objects.get_or_create(
            name=name,
            defaults={'country': country}
        )
        car_brands[name] = brand
        print(f"  ✓ {name} ({'создан' if created else 'уже существует'})")
    
    # 3. Создаем основные категории (корневые)
    print("\n📂 Создание основных категорий...")
    root_categories = {}
    root_category_data = [
        ("Двигатель", "engine", "cars"),
        ("Тормозная система", "brake-system", "cars"),
        ("Подвеска", "suspension", "cars"),
        ("Электрика", "electrical", "cars"),
        ("Система питания", "fuel-system", "cars"),
        ("Автохимия и масла", "chemistry", "chemistry"),
        ("Техническое обслуживание", "maintenance", "dlya-to"),
    ]
    
    for name, slug, show_in in root_category_data:
        category, created = Category.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'show_in': show_in,
                'is_active': True,
                'order': len(root_categories) + 1
            }
        )
        root_categories[slug] = category
        print(f"  ✓ {name} ({'создан' if created else 'уже существует'})")
    
    # 4. Создаем подкатегории
    print("\n📁 Создание подкатегорий...")
    subcategories = {}
    subcategory_data = [
        # Двигатель
        ("ГРМ", "timing-system", "engine"),
        ("Блок цилиндров", "cylinder-block", "engine"),
        ("Система смазки", "lubrication-system", "engine"),
        
        # Тормозная система
        ("Тормозные диски", "brake-discs", "brake-system"),
        ("Тормозные колодки", "brake-pads", "brake-system"),
        
        # Подвеска
        ("Амортизаторы", "shock-absorbers", "suspension"),
        ("Пружины", "springs", "suspension"),
        
        # Электрика
        ("Аккумуляторы", "batteries", "electrical"),
        ("Генераторы", "alternators", "electrical"),
        
        # Система питания
        ("Топливные насосы", "fuel-pumps", "fuel-system"),
        ("Форсунки", "fuel-injectors", "fuel-system"),
    ]
    
    for name, slug, parent_slug in subcategory_data:
        subcategory, created = Category.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'parent': root_categories[parent_slug],
                'is_active': True,
                'order': len(subcategories) + 1
            }
        )
        subcategories[slug] = subcategory
        print(f"  ✓ {name} → {root_categories[parent_slug].name}")
    
    # 5. Создаем специализированные категории для масел
    print("\n🛢️ Создание категорий автохимии...")
    oil_categories = {}
    oil_category_data = [
        ("Моторные масла", "engine-oils"),
        ("Трансмиссионные масла", "transmission-oils"),
        ("Тормозные жидкости", "brake-fluids"),
    ]
    
    for name, slug in oil_category_data:
        category, created = OilAndChemistryCategory.objects.get_or_create(
            slug=slug,
            defaults={
                'name': name,
                'is_active': True
            }
        )
        oil_categories[slug] = category
        print(f"  ✓ {name} ({'создан' if created else 'уже существует'})")
    
    # 6. Создаем бренды автохимии
    print("\n🏷️ Создание брендов автохимии...")
    oil_brands = {}
    oil_brand_data = [
        ("Castrol", "Великобритания"),
        ("Mobil", "США"),
        ("Shell", "Нидерланды"),
        ("Liqui Moly", "Германия"),
    ]
    
    for name, country in oil_brand_data:
        brand, created = OilAndChemistryBrand.objects.get_or_create(
            name=name,
            defaults={'country': country}
        )
        oil_brands[name] = brand
        print(f"  ✓ {name} ({'создан' if created else 'уже существует'})")
    
    # 7. Создаем простые товары с проверкой уникальности
    print("\n🛍️ Создание товаров...")
    
    def generate_unique_part_number(base, existing_numbers):
        """Генерирует уникальный артикул"""
        counter = 1
        part_number = f"{base}-{counter:03d}"
        while part_number in existing_numbers:
            counter += 1
            part_number = f"{base}-{counter:03d}"
        existing_numbers.add(part_number)
        return part_number
    
    # Получаем существующие артикулы
    existing_part_numbers = set(Product.objects.values_list('part_number', flat=True))
    
    products_data = [
        # Запчасти для двигателя
        {
            'name': 'Ремень ГРМ Audi A4 1.8T',
            'description': 'Оригинальный ремень ГРМ для Audi A4 с двигателем 1.8T',
            'price': Decimal('8500.00'),
            'category': subcategories['timing-system'],
            'car_brand': car_brands['Audi'],
            'manufacturer': manufacturers['Bosch'],
            'part_number': generate_unique_part_number('AUD-GRM', existing_part_numbers),
            'vin': 'WAUZZZ8E8DA123456',
            'product_type': 'spare_part',
            'vehicle_type': 'car'
        },
        {
            'name': 'Тормозные диски BMW X5',
            'description': 'Комплект тормозных дисков для BMW X5',
            'price': Decimal('25000.00'),
            'category': subcategories['brake-discs'],
            'car_brand': car_brands['BMW'],
            'manufacturer': manufacturers['Bosch'],
            'part_number': generate_unique_part_number('BMW-BRK', existing_part_numbers),
            'vin': 'WBAFR7C50LC123456',
            'product_type': 'spare_part',
            'vehicle_type': 'car'
        },
        {
            'name': 'Амортизаторы Toyota RAV4',
            'description': 'Комплект амортизаторов для Toyota RAV4',
            'price': Decimal('22000.00'),
            'category': subcategories['shock-absorbers'],
            'car_brand': car_brands['Toyota'],
            'manufacturer': manufacturers['Toyota Motor'],
            'part_number': generate_unique_part_number('TOY-SHK', existing_part_numbers),
            'vin': 'JT2BF28K123456789',
            'product_type': 'spare_part',
            'vehicle_type': 'car'
        },
        {
            'name': 'Тормозные колодки Mercedes E-Class',
            'description': 'Комплект тормозных колодок для Mercedes E-Class',
            'price': Decimal('12000.00'),
            'category': subcategories['brake-pads'],
            'car_brand': car_brands['Mercedes-Benz'],
            'manufacturer': manufacturers['Bosch'],
            'part_number': generate_unique_part_number('MER-PAD', existing_part_numbers),
            'vin': 'WDD2120011A123456',
            'product_type': 'spare_part',
            'vehicle_type': 'car'
        },
        {
            'name': 'Пружины подвески VW Golf',
            'description': 'Комплект пружин подвески для VW Golf',
            'price': Decimal('15000.00'),
            'category': subcategories['springs'],
            'car_brand': car_brands['Volkswagen'],
            'manufacturer': manufacturers['VAG'],
            'part_number': generate_unique_part_number('VW-SPR', existing_part_numbers),
            'vin': 'WVWZZZ1KZBW123456',
            'product_type': 'spare_part',
            'vehicle_type': 'car'
        },
        
        # Автохимия
        {
            'name': 'Моторное масло Castrol 5W-30 4л',
            'description': 'Синтетическое моторное масло Castrol GTX 5W-30',
            'price': Decimal('2500.00'),
            'category': root_categories['chemistry'],
            'oil_chem_category': oil_categories['engine-oils'],
            'oil_chem_brand': oil_brands['Castrol'],
            'manufacturer': manufacturers['Castrol'],
            'part_number': generate_unique_part_number('CAST-5W30', existing_part_numbers),
            'product_type': 'oil_chem',
            'vehicle_type': 'universal',
            'viscosity': '5W-30',
            'volume': Decimal('4.0')
        },
        {
            'name': 'Тормозная жидкость DOT 4 1л',
            'description': 'Тормозная жидкость DOT 4 для всех типов автомобилей',
            'price': Decimal('800.00'),
            'category': root_categories['chemistry'],
            'oil_chem_category': oil_categories['brake-fluids'],
            'oil_chem_brand': oil_brands['Liqui Moly'],
            'manufacturer': manufacturers['Liqui Moly'],
            'part_number': generate_unique_part_number('LM-DOT4', existing_part_numbers),
            'product_type': 'oil_chem',
            'vehicle_type': 'universal',
            'volume': Decimal('1.0')
        },
        {
            'name': 'Моторное масло Mobil 5W-40 5л',
            'description': 'Синтетическое моторное масло Mobil 1 5W-40',
            'price': Decimal('3200.00'),
            'category': root_categories['chemistry'],
            'oil_chem_category': oil_categories['engine-oils'],
            'oil_chem_brand': oil_brands['Mobil'],
            'manufacturer': manufacturers['Mobil'],
            'part_number': generate_unique_part_number('MOB-5W40', existing_part_numbers),
            'product_type': 'oil_chem',
            'vehicle_type': 'universal',
            'viscosity': '5W-40',
            'volume': Decimal('5.0')
        },
        
        # Универсальные товары
        {
            'name': 'Аккумулятор 60Ah 12V',
            'description': 'Свинцово-кислотный аккумулятор 60Ah 12V',
            'price': Decimal('8000.00'),
            'category': subcategories['batteries'],
            'manufacturer': manufacturers['Bosch'],
            'part_number': generate_unique_part_number('BOSCH-60AH', existing_part_numbers),
            'product_type': 'spare_part',
            'vehicle_type': 'universal'
        },
        {
            'name': 'Генератор 120A',
            'description': 'Автомобильный генератор 120A',
            'price': Decimal('25000.00'),
            'category': subcategories['alternators'],
            'manufacturer': manufacturers['Bosch'],
            'part_number': generate_unique_part_number('BOSCH-GEN', existing_part_numbers),
            'product_type': 'spare_part',
            'vehicle_type': 'universal'
        },
        {
            'name': 'Топливный насос электрический',
            'description': 'Электрический топливный насос для инжекторных двигателей',
            'price': Decimal('15000.00'),
            'category': subcategories['fuel-pumps'],
            'manufacturer': manufacturers['Bosch'],
            'part_number': generate_unique_part_number('BOSCH-FP', existing_part_numbers),
            'product_type': 'spare_part',
            'vehicle_type': 'universal'
        },
    ]
    
    created_products = []
    for product_data in products_data:
        try:
            product = Product.objects.create(**product_data)
            created_products.append(product)
            print(f"  ✓ {product.name} - {product.price} руб. (артикул: {product.part_number})")
        except Exception as e:
            print(f"  ❌ Ошибка при создании {product_data['name']}: {e}")
    
    # 8. Статистика
    print(f"\n📊 Статистика:")
    print(f"  Производителей: {Manufacturer.objects.count()}")
    print(f"  Брендов авто: {CarBrand.objects.count()}")
    print(f"  Категорий: {Category.objects.count()}")
    print(f"  Товаров: {Product.objects.count()}")
    
    print(f"\n🎉 Готово! Создано {len(created_products)} новых товаров")
    
    # Показываем структуру
    print(f"\n📋 Структура категорий:")
    for root in Category.objects.filter(parent__isnull=True).order_by('order'):
        print(f"  {root.name}")
        for sub in root.children.all().order_by('order'):
            count = Product.objects.filter(category=sub).count()
            if count > 0:
                print(f"    └── {sub.name} ({count} товаров)")

if __name__ == "__main__":
    create_final_test_data()
