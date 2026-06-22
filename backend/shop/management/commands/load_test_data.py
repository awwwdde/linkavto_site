from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from shop.models import (
    CarBrand, CarModel, CarGeneration, Category, Product, 
    Manufacturer, CarType, ProductImage
)
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Load test data for the shop'

    def handle(self, *args, **options):
        self.stdout.write('Loading test data...')
        
        # Создаем производителей
        manufacturers = []
        for name in ['Audi', 'BMW', 'Mercedes-Benz', 'Volkswagen', 'Toyota']:
            manufacturer, created = Manufacturer.objects.get_or_create(name=name)
            manufacturers.append(manufacturer)
            if created:
                self.stdout.write(f'Created manufacturer: {name}')

        # Создаем типы автомобилей
        car_types = []
        for name in ['Легковые', 'Грузовые', 'Мотоциклы']:
            car_type, created = CarType.objects.get_or_create(
                name=name,
                defaults={'slug': name.lower()}
            )
            car_types.append(car_type)
            if created:
                self.stdout.write(f'Created car type: {name}')

        # Создаем бренды автомобилей
        brands = []
        for name in ['Audi', 'BMW', 'Mercedes-Benz', 'Volkswagen', 'Toyota']:
            brand, created = CarBrand.objects.get_or_create(
                name=name,
                defaults={
                    'logo': f'brands/{name.lower()}.png',
                    'is_active': True
                }
            )
            brands.append(brand)
            if created:
                self.stdout.write(f'Created brand: {name}')

        # Создаем категории с правильными slug'ами
        categories = []
        category_data = [
            ('Двигатель', 'engine'),
            ('Тормозная система', 'brake-system'),
            ('Подвеска', 'suspension'),
            ('Электрика', 'electrics'),
            ('Кузов', 'body'),
            ('Салон', 'interior'),
            ('Масла и жидкости', 'oils-fluids')
        ]
        
        for name, slug in category_data:
            category, created = Category.objects.get_or_create(
                name=name,
                defaults={
                    'slug': slug,
                    'is_active': True,
                    'show_in': 'main'
                }
            )
            categories.append(category)
            if created:
                self.stdout.write(f'Created category: {name} ({slug})')

        # Создаем модели автомобилей
        models = []
        model_data = [
            ('Audi', 'A4', 2015, 2020),
            ('BMW', 'X5', 2018, 2023),
            ('Mercedes-Benz', 'C-Class', 2016, 2021),
            ('Volkswagen', 'Golf', 2017, 2022),
            ('Toyota', 'Camry', 2019, 2024),
        ]
        
        for brand_name, model_name, year_start, year_end in model_data:
            brand = next((b for b in brands if b.name == brand_name), None)
            if brand:
                model, created = CarModel.objects.get_or_create(
                    name=model_name,
                    brand=brand,
                    defaults={
                        'year_start': year_start,
                        'year_end': year_end
                    }
                )
                models.append(model)
                if created:
                    self.stdout.write(f'Created model: {brand_name} {model_name}')

        # Создаем поколения
        generations = []
        for model in models:
            generation, created = CarGeneration.objects.get_or_create(
                name=f'{model.name} {model.year_start}-{model.year_end}',
                model=model,
                defaults={
                    'year_start': model.year_start,
                    'year_end': model.year_end
                }
            )
            generations.append(generation)
            if created:
                self.stdout.write(f'Created generation: {generation.name}')

        # Создаем тестовые товары с правильными slug'ами
        product_data = [
            ('Масляный фильтр', 'oil-filter'),
            ('Тормозные колодки', 'brake-pads'),
            ('Свечи зажигания', 'spark-plugs'),
            ('Амортизатор', 'shock-absorber'),
            ('Генератор', 'generator'),
            ('Стартер', 'starter'),
            ('Аккумулятор', 'battery'),
            ('Фара', 'headlight'),
            ('Бампер', 'bumper'),
            ('Коврики', 'mats'),
            ('Моторное масло 5W-30', 'motor-oil-5w30'),
            ('Тормозная жидкость', 'brake-fluid'),
            ('Антифриз', 'antifreeze'),
            ('Стеклоочистители', 'wipers')
        ]

        for i, (name, slug) in enumerate(product_data):
            # Выбираем случайные данные
            brand = random.choice(brands)
            category = random.choice(categories)
            model = random.choice(models)
            generation = random.choice(generations)
            
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'slug': slug,
                    'part_number': f'TEST-{i+1:03d}',
                    'price': Decimal(str(random.randint(500, 50000))),
                    'description': f'Тестовый товар {name} для {brand.name} {model.name}',
                    'category': category,
                    'is_active': True,
                    'is_featured': random.choice([True, False]),
                    'is_new': random.choice([True, False]),
                    'stock': random.randint(0, 100),
                    'product_type': 'spare_part'
                }
            )
            
            if created:
                self.stdout.write(f'Created product: {name} ({slug})')
                
                # Добавляем изображение товара
                ProductImage.objects.create(
                    product=product,
                    image=f'products/test_{i+1}.jpg'
                )

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded test data!')
        )
