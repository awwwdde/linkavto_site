from django.core.management.base import BaseCommand
from shop.models import (
    Category, CarBrand, CarModel, CarGeneration, Product, PartSubcategory
)


class Command(BaseCommand):
    help = 'Добавляет тестовые данные для легковых авто (BMW и Audi) в категорию Двигатель'

    def handle(self, *args, **options):
        # Находим корневую категорию "Легковые автомобили"
        root_category = Category.objects.filter(
            show_in='cars',
            parent__isnull=True
        ).first()

        if not root_category:
            self.stdout.write(self.style.ERROR('❌ Корневая категория "Легковые автомобили" не найдена'))
            return

        # Находим категорию "Двигатель"
        engine_category = Category.objects.filter(
            parent=root_category,
            slug='dvigatel-legkovye'
        ).first()
        
        # Если не найдена по slug, ищем по имени
        if not engine_category:
            engine_category = Category.objects.filter(
                parent=root_category,
                name__icontains='двигатель'
            ).first()
        
        # Если не найдена, ищем по slug с icontains
        if not engine_category:
            engine_category = Category.objects.filter(
                parent=root_category,
                slug__icontains='dvigatel'
            ).first()

        if not engine_category:
            self.stdout.write(self.style.ERROR('❌ Категория "Двигатель" не найдена'))
            return

        # Создаем или получаем марки BMW и Audi
        bmw_brand, created = CarBrand.objects.get_or_create(
            slug='bmw',
            defaults={
                'name': 'BMW',
                'is_active': True,
                'country': 'Германия'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Создана марка: {bmw_brand.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Найдена марка: {bmw_brand.name}'))

        audi_brand, created = CarBrand.objects.get_or_create(
            slug='audi',
            defaults={
                'name': 'Audi',
                'is_active': True,
                'country': 'Германия'
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Создана марка: {audi_brand.name}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✓ Найдена марка: {audi_brand.name}'))

        # Создаем модели для BMW
        bmw_models_data = [
            {'name': '3 Series', 'slug': '3-series', 'year_start': 2019},
            {'name': '5 Series', 'slug': '5-series', 'year_start': 2017},
            {'name': 'X5', 'slug': 'x5', 'year_start': 2019},
        ]

        bmw_models = []
        for model_data in bmw_models_data:
            model, created = CarModel.objects.get_or_create(
                slug=model_data['slug'],
                brand=bmw_brand,
                defaults={
                    'name': model_data['name'],
                    'year_start': model_data['year_start'],
                    'is_active': True
                }
            )
            bmw_models.append(model)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✅ Создана модель: {bmw_brand.name} {model.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Найдена модель: {bmw_brand.name} {model.name}'))

        # Создаем модели для Audi
        audi_models_data = [
            {'name': 'A4', 'slug': 'a4', 'year_start': 2016},
            {'name': 'A6', 'slug': 'a6', 'year_start': 2018},
            {'name': 'Q5', 'slug': 'q5', 'year_start': 2017},
        ]

        audi_models = []
        for model_data in audi_models_data:
            model, created = CarModel.objects.get_or_create(
                slug=model_data['slug'],
                brand=audi_brand,
                defaults={
                    'name': model_data['name'],
                    'year_start': model_data['year_start'],
                    'is_active': True
                }
            )
            audi_models.append(model)
            if created:
                self.stdout.write(self.style.SUCCESS(f'  ✅ Создана модель: {audi_brand.name} {model.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'  ✓ Найдена модель: {audi_brand.name} {model.name}'))

        # Создаем поколения для моделей BMW
        bmw_generations_data = [
            {'model_slug': '3-series', 'name': 'G20', 'year_start': 2019, 'year_end': 2023},
            {'model_slug': '3-series', 'name': 'G21', 'year_start': 2019, 'year_end': None},
            {'model_slug': '5-series', 'name': 'G30', 'year_start': 2017, 'year_end': 2023},
            {'model_slug': 'x5', 'name': 'G05', 'year_start': 2019, 'year_end': None},
        ]

        bmw_generations = []
        for gen_data in bmw_generations_data:
            model = next((m for m in bmw_models if m.slug == gen_data['model_slug']), None)
            if model:
                generation, created = CarGeneration.objects.get_or_create(
                    slug=f'{model.slug}-{gen_data["name"].lower()}',
                    model=model,
                    defaults={
                        'name': gen_data['name'],
                        'year_start': gen_data['year_start'],
                        'year_end': gen_data.get('year_end'),
                        'is_active': True
                    }
                )
                bmw_generations.append(generation)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'    ✅ Создано поколение: {model.brand.name} {model.name} {generation.name}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Найдено поколение: {model.brand.name} {model.name} {generation.name}'))

        # Создаем поколения для моделей Audi
        audi_generations_data = [
            {'model_slug': 'a4', 'name': 'B9', 'year_start': 2016, 'year_end': 2023},
            {'model_slug': 'a4', 'name': 'B9.5', 'year_start': 2019, 'year_end': None},
            {'model_slug': 'a6', 'name': 'C8', 'year_start': 2018, 'year_end': None},
            {'model_slug': 'q5', 'name': 'FY', 'year_start': 2017, 'year_end': 2023},
        ]

        audi_generations = []
        for gen_data in audi_generations_data:
            model = next((m for m in audi_models if m.slug == gen_data['model_slug']), None)
            if model:
                generation, created = CarGeneration.objects.get_or_create(
                    slug=f'{model.slug}-{gen_data["name"].lower()}',
                    model=model,
                    defaults={
                        'name': gen_data['name'],
                        'year_start': gen_data['year_start'],
                        'year_end': gen_data.get('year_end'),
                        'is_active': True
                    }
                )
                audi_generations.append(generation)
                if created:
                    self.stdout.write(self.style.SUCCESS(f'    ✅ Создано поколение: {model.brand.name} {model.name} {generation.name}'))
                else:
                    self.stdout.write(self.style.SUCCESS(f'    ✓ Найдено поколение: {model.brand.name} {model.name} {generation.name}'))

        # Создаем тестовые продукты для BMW
        bmw_products = [
            {'name': 'Двигатель BMW 3 Series G20 2.0 TDI', 'price': 150000, 'stock': 5},
            {'name': 'Блок цилиндров BMW 5 Series G30', 'price': 200000, 'stock': 3},
            {'name': 'Головка блока цилиндров BMW X5 G05', 'price': 180000, 'stock': 4},
            {'name': 'Коленчатый вал BMW 3 Series', 'price': 120000, 'stock': 6},
            {'name': 'Поршневая группа BMW 5 Series', 'price': 80000, 'stock': 8},
        ]

        for i, product_data in enumerate(bmw_products):
            model = bmw_models[i % len(bmw_models)]
            generation = next((g for g in bmw_generations if g.model == model), None)
            
            product, created = Product.objects.get_or_create(
                slug=f'bmw-{model.slug}-{i+1}',
                defaults={
                    'name': product_data['name'],
                    'category': engine_category,
                    'car_brand': bmw_brand,
                    'price': product_data['price'],
                    'stock': product_data['stock'],
                    'is_active': True,
                }
            )
            
            if created:
                product.car_models.add(model)
                if generation:
                    product.car_generations.add(generation)
                self.stdout.write(self.style.SUCCESS(f'      ✅ Создан продукт: {product.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'      ✓ Найден продукт: {product.name}'))

        # Создаем тестовые продукты для Audi
        audi_products = [
            {'name': 'Двигатель Audi A4 B9 2.0 TFSI', 'price': 160000, 'stock': 4},
            {'name': 'Блок цилиндров Audi A6 C8', 'price': 210000, 'stock': 2},
            {'name': 'Головка блока цилиндров Audi Q5 FY', 'price': 190000, 'stock': 3},
            {'name': 'Коленчатый вал Audi A4', 'price': 130000, 'stock': 5},
            {'name': 'Поршневая группа Audi A6', 'price': 85000, 'stock': 7},
        ]

        for i, product_data in enumerate(audi_products):
            model = audi_models[i % len(audi_models)]
            generation = next((g for g in audi_generations if g.model == model), None)
            
            product, created = Product.objects.get_or_create(
                slug=f'audi-{model.slug}-{i+1}',
                defaults={
                    'name': product_data['name'],
                    'category': engine_category,
                    'car_brand': audi_brand,
                    'price': product_data['price'],
                    'stock': product_data['stock'],
                    'is_active': True,
                }
            )
            
            if created:
                product.car_models.add(model)
                if generation:
                    product.car_generations.add(generation)
                self.stdout.write(self.style.SUCCESS(f'      ✅ Создан продукт: {product.name}'))
            else:
                self.stdout.write(self.style.SUCCESS(f'      ✓ Найден продукт: {product.name}'))

        self.stdout.write(self.style.SUCCESS('\n✅ Тестовые данные успешно добавлены!'))

