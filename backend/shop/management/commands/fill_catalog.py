"""
Команда для заполнения каталога категориями
"""
from django.core.management.base import BaseCommand
from shop.models import Category


class Command(BaseCommand):
    help = 'Заполняет каталог категориями'

    def handle(self, *args, **options):
        self.stdout.write('Создание категорий...')
        
        # Категории для легковых автомобилей
        car_categories = [
            'Двигатель',
            'Крепеж',
            'Кузовные детали',
            'Подвеска',
            'Приводные ремни',
            'Рулевое управление',
            'Система выпуска отработавших газов',
            'Система отопления и вентиляции',
            'Система охлаждения двигателя',
            'Система очистки стёкол и фар',
            'Система питания',
            'Стекло',
            'Тормозная система',
            'Трансмиссия',
            'Фильтры',
            'Электрооборудование',
            'Фары'
        ]
        
        # Категории для грузовых автомобилей
        truck_categories = [
            'Двигатель',
            'Кузовные детали',
            'Система охлаждения',
            'Топливная система',
            'Тормозная система',
            'Трансмиссия',
            'Фары',
            'Ходовая часть и мосты',
            'Электрооборудование'
        ]
        
        # Категории для мототехники
        moto_categories = [
            'Аксессуары и оборудование',
            'Крепеж и мелочи',
            'Кузов и обвес',
            'Рулевое управление',
            'Система выхлопа',
            'Система охлаждения',
            'Топливная система',
            'Тормозная система',
            'Трансмиссия',
            'Ходовая часть',
            'Электрооборудование',
            'Двигатель'
        ]
        
        # Категории для спецтехники
        special_categories = [
            'Гидравлическая система',
            'Двигатель',
            'Трансмиссия',
            'Ходовая часть'
        ]
        
        # Создаем корневые категории
        root_categories = {
            'Легковые автомобили': car_categories,
            'Грузовые автомобили': truck_categories,
            'Мототехника': moto_categories,
            'Спецтехника': special_categories,
            'Шины и диски': ['Шины', 'Диски'],
            'Для ТО': []
        }
        
        created_count = 0
        for root_name, subcategories in root_categories.items():
            # Создаем корневую категорию
            root_cat, created = Category.objects.get_or_create(
                name=root_name,
                defaults={'parent': None}
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✓ Создана корневая категория: {root_name}')
            
            # Создаем подкатегории
            for subcat_name in subcategories:
                subcat, created = Category.objects.get_or_create(
                    name=subcat_name,
                    parent=root_cat
                )
                if created:
                    created_count += 1
                    self.stdout.write(f'    ✓ Создана подкатегория: {subcat_name}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Создано категорий: {created_count}'))
