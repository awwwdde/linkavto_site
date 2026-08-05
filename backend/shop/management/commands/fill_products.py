"""
Команда для создания товаров с привязкой к категориям и модификациям
"""
from django.core.management.base import BaseCommand
from shop.models import Product, Category, CarModification
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Создает товары с привязкой к категориям и модификациям'

    def handle(self, *args, **options):
        self.stdout.write('Создание товаров...')
        
        # Получаем категории
        categories_map = {}
        for cat in Category.objects.filter(parent__isnull=False):
            categories_map[cat.name] = cat
        
        if not categories_map:
            self.stdout.write(self.style.ERROR('Сначала создайте категории командой: python manage.py fill_catalog'))
            return
        
        # Получаем модификации
        modifications = list(CarModification.objects.all())
        if not modifications:
            self.stdout.write(self.style.ERROR('Сначала создайте автомобили командой: python manage.py fill_vehicles'))
            return
        
        # Структура: категория -> список товаров
        products_data = {
            'Двигатель': [
                {'name': 'Поршень двигателя STD', 'article': 'PST-001', 'price': 1500},
                {'name': 'Кольца поршневые STD', 'article': 'RNG-001', 'price': 800},
                {'name': 'Вкладыши коленвала STD', 'article': 'BRG-001', 'price': 2500},
                {'name': 'Прокладка ГБЦ', 'article': 'GSK-001', 'price': 1200},
                {'name': 'Цепь ГРМ', 'article': 'CHN-001', 'price': 3500},
                {'name': 'Натяжитель цепи ГРМ', 'article': 'TNS-001', 'price': 1800},
                {'name': 'Успокоитель цепи ГРМ', 'article': 'DMR-001', 'price': 900},
                {'name': 'Помпа охлаждения', 'article': 'PMP-001', 'price': 2800},
                {'name': 'Термостат', 'article': 'THM-001', 'price': 1100},
                {'name': 'Клапан впускной', 'article': 'VLV-IN-001', 'price': 650},
                {'name': 'Клапан выпускной', 'article': 'VLV-EX-001', 'price': 700},
                {'name': 'Сальник коленвала передний', 'article': 'SL-CRK-F', 'price': 450},
                {'name': 'Сальник коленвала задний', 'article': 'SL-CRK-R', 'price': 550},
            ],
            'Крепеж': [
                {'name': 'Болт М8х30 (10 шт)', 'article': 'BLT-M8-30', 'price': 150},
                {'name': 'Болт М10х40 (10 шт)', 'article': 'BLT-M10-40', 'price': 200},
                {'name': 'Гайка М8 (20 шт)', 'article': 'NT-M8', 'price': 100},
                {'name': 'Шайба 8 мм (50 шт)', 'article': 'WSH-8', 'price': 80},
                {'name': 'Хомут 40-60 мм (5 шт)', 'article': 'CLP-40-60', 'price': 120},
            ],
            'Кузовные детали': [
                {'name': 'Крыло переднее левое', 'article': 'FND-L', 'price': 8500},
                {'name': 'Крыло переднее правое', 'article': 'FND-R', 'price': 8500},
                {'name': 'Капот', 'article': 'HDD-001', 'price': 15000},
                {'name': 'Бампер передний', 'article': 'BMP-F', 'price': 12000},
                {'name': 'Бампер задний', 'article': 'BMP-R', 'price': 11000},
                {'name': 'Дверь передняя левая', 'article': 'DR-FL', 'price': 18000},
                {'name': 'Дверь передняя правая', 'article': 'DR-FR', 'price': 18000},
                {'name': 'Решетка радиатора', 'article': 'GRL-001', 'price': 3500},
            ],
            'Подвеска': [
                {'name': 'Амортизатор передний левый', 'article': 'SHK-FL', 'price': 3200},
                {'name': 'Амортизатор передний правый', 'article': 'SHK-FR', 'price': 3200},
                {'name': 'Амортизатор задний левый', 'article': 'SHK-RL', 'price': 2800},
                {'name': 'Амортизатор задний правый', 'article': 'SHK-RR', 'price': 2800},
                {'name': 'Пружина передняя', 'article': 'SPR-F', 'price': 1800},
                {'name': 'Пружина задняя', 'article': 'SPR-R', 'price': 1600},
                {'name': 'Рычаг передний нижний левый', 'article': 'ARM-FL', 'price': 4500},
                {'name': 'Рычаг передний нижний правый', 'article': 'ARM-FR', 'price': 4500},
                {'name': 'Стойка стабилизатора передняя', 'article': 'SLK-F', 'price': 450},
                {'name': 'Втулка стабилизатора', 'article': 'BSH-STB', 'price': 250},
            ],
            'Приводные ремни': [
                {'name': 'Ремень ГРМ', 'article': 'BLT-TM', 'price': 1200},
                {'name': 'Ремень генератора', 'article': 'BLT-ALT', 'price': 650},
                {'name': 'Ремень ГУР', 'article': 'BLT-PS', 'price': 550},
                {'name': 'Ремень кондиционера', 'article': 'BLT-AC', 'price': 700},
                {'name': 'Комплект ГРМ (ремень + ролики)', 'article': 'KIT-TM', 'price': 4500},
            ],
            'Рулевое управление': [
                {'name': 'Рулевая рейка', 'article': 'RCK-001', 'price': 18000},
                {'name': 'Наконечник рулевой тяги левый', 'article': 'TRE-L', 'price': 850},
                {'name': 'Наконечник рулевой тяги правый', 'article': 'TRE-R', 'price': 850},
                {'name': 'Рулевая тяга левая', 'article': 'TRD-L', 'price': 1500},
                {'name': 'Рулевая тяга правая', 'article': 'TRD-R', 'price': 1500},
                {'name': 'Пыльник рулевой рейки', 'article': 'BT-RCK', 'price': 450},
            ],
            'Тормозная система': [
                {'name': 'Колодки тормозные передние', 'article': 'PAD-F', 'price': 2200},
                {'name': 'Колодки тормозные задние', 'article': 'PAD-R', 'price': 1800},
                {'name': 'Диск тормозной передний', 'article': 'DSC-F', 'price': 1500},
                {'name': 'Диск тормозной задний', 'article': 'DSC-R', 'price': 1300},
                {'name': 'Суппорт передний левый', 'article': 'CLP-FL', 'price': 6500},
                {'name': 'Суппорт передний правый', 'article': 'CLP-FR', 'price': 6500},
                {'name': 'Тормозной цилиндр задний', 'article': 'CYL-R', 'price': 1200},
                {'name': 'Главный тормозной цилиндр', 'article': 'CYL-MST', 'price': 4500},
                {'name': 'Тормозная жидкость DOT4 1л', 'article': 'FLD-BRK', 'price': 450},
            ],
            'Трансмиссия': [
                {'name': 'ШРУС наружный', 'article': 'CVJ-OUT', 'price': 3500},
                {'name': 'ШРУС внутренний', 'article': 'CVJ-IN', 'price': 2800},
                {'name': 'Пыльник ШРУСа наружный', 'article': 'BT-CVJ-O', 'price': 350},
                {'name': 'Пыльник ШРУСа внутренний', 'article': 'BT-CVJ-I', 'price': 350},
                {'name': 'Сцепление комплект', 'article': 'CLT-KIT', 'price': 8500},
                {'name': 'Диск сцепления', 'article': 'CLT-DSC', 'price': 4500},
                {'name': 'Корзина сцепления', 'article': 'CLT-CVR', 'price': 5500},
                {'name': 'Выжимной подшипник', 'article': 'BRG-REL', 'price': 950},
            ],
            'Фильтры': [
                {'name': 'Фильтр воздушный', 'article': 'FLT-AIR', 'price': 450},
                {'name': 'Фильтр масляный', 'article': 'FLT-OIL', 'price': 350},
                {'name': 'Фильтр топливный', 'article': 'FLT-FUEL', 'price': 650},
                {'name': 'Фильтр салона', 'article': 'FLT-CAB', 'price': 550},
                {'name': 'Фильтр салона угольный', 'article': 'FLT-CAB-C', 'price': 750},
            ],
            'Электрооборудование': [
                {'name': 'Генератор', 'article': 'ALT-001', 'price': 8500},
                {'name': 'Стартер', 'article': 'STR-001', 'price': 7500},
                {'name': 'Аккумулятор 60Ah', 'article': 'BTR-60', 'price': 4500},
                {'name': 'Свеча зажигания', 'article': 'PLG-001', 'price': 450},
                {'name': 'Катушка зажигания', 'article': 'COL-001', 'price': 2500},
                {'name': 'Датчик ABS передний', 'article': 'SNS-ABS-F', 'price': 1200},
                {'name': 'Датчик температуры ОЖ', 'article': 'SNS-TMP', 'price': 650},
                {'name': 'Датчик положения коленвала', 'article': 'SNS-CRK', 'price': 850},
                {'name': 'Датчик кислорода (лямбда-зонд)', 'article': 'SNS-O2', 'price': 2800},
            ],
            'Фары': [
                {'name': 'Фара передняя левая', 'article': 'LMP-FL', 'price': 8500},
                {'name': 'Фара передняя правая', 'article': 'LMP-FR', 'price': 8500},
                {'name': 'Фонарь задний левый', 'article': 'LMP-RL', 'price': 3500},
                {'name': 'Фонарь задний правый', 'article': 'LMP-RR', 'price': 3500},
                {'name': 'Лампа H7 12V 55W', 'article': 'BLB-H7', 'price': 250},
                {'name': 'Лампа H4 12V 60/55W', 'article': 'BLB-H4', 'price': 300},
            ],
            'Система охлаждения двигателя': [
                {'name': 'Радиатор охлаждения', 'article': 'RAD-CLN', 'price': 5500},
                {'name': 'Вентилятор радиатора', 'article': 'FAN-RAD', 'price': 2800},
                {'name': 'Термостат', 'article': 'TST-001', 'price': 1100},
                {'name': 'Датчик температуры', 'article': 'SNS-TMP-2', 'price': 650},
                {'name': 'Патрубок радиатора верхний', 'article': 'HSE-RAD-U', 'price': 850},
                {'name': 'Патрубок радиатора нижний', 'article': 'HSE-RAD-L', 'price': 850},
                {'name': 'Антифриз G12 5л', 'article': 'CLN-G12', 'price': 1200},
            ],
            'Система питания': [
                {'name': 'Топливный насос', 'article': 'PMP-FUEL', 'price': 4500},
                {'name': 'Форсунка топливная', 'article': 'INJ-001', 'price': 3500},
                {'name': 'Дроссельная заслонка', 'article': 'THR-001', 'price': 6500},
                {'name': 'Датчик массового расхода воздуха', 'article': 'SNS-MAF', 'price': 3800},
                {'name': 'Регулятор давления топлива', 'article': 'REG-FUEL', 'price': 1800},
            ],
        }
        
        created_count = 0
        
        for category_name, products in products_data.items():
            category = categories_map.get(category_name)
            if not category:
                self.stdout.write(self.style.WARNING(f'Категория "{category_name}" не найдена, пропуск...'))
                continue
            
            for product_data in products:
                # Выбираем случайные модификации (от 3 до 8 модификаций на товар)
                num_modifications = random.randint(3, 8)
                random_modifications = random.sample(modifications, min(num_modifications, len(modifications)))
                
                product, created = Product.objects.get_or_create(
                    part_number=product_data['article'],
                    defaults={
                        'name': product_data['name'],
                        'category': category,
                        'price': Decimal(product_data['price']),
                        'stock': random.randint(5, 50),
                        'vehicle_type': 'car',
                    }
                )
                
                if created:
                    # Привязываем модификации
                    product.car_modifications.set(random_modifications)
                    created_count += 1
                    
                    # Показываем информацию о первых 3 модификациях
                    mods_info = ', '.join([f'{m.generation.model.brand.name} {m.generation.model.name}' 
                                          for m in random_modifications[:3]])
                    if len(random_modifications) > 3:
                        mods_info += f' и ещё {len(random_modifications) - 3}'
                    
                    self.stdout.write(
                        f'  ✓ {product.name} (арт: {product.part_number}) - '
                        f'{product.price} руб. - {mods_info}'
                    )
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Создано товаров: {created_count}'))
