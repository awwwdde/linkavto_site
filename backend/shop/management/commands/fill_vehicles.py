"""
Команда для заполнения автомобилей (марки, модели, поколения, модификации)
"""
from django.core.management.base import BaseCommand
from shop.models import CarBrand, CarModel, CarGeneration, CarModification


class Command(BaseCommand):
    help = 'Заполняет базу данных марками, моделями, поколениями и модификациями автомобилей'

    def handle(self, *args, **options):
        self.stdout.write('Создание автомобилей...')
        
        # Структура: Марка -> [Модели -> [Поколения -> [Модификации]]]
        vehicles_data = {
            'Audi': {
                'A3': {
                    '8P (2003-2012)': [
                        {'name': '1.6 FSI (115 л.с.)', 'engine': '1.6', 'power': 115, 'year_from': 2003, 'year_to': 2012},
                        {'name': '2.0 FSI (150 л.с.)', 'engine': '2.0', 'power': 150, 'year_from': 2003, 'year_to': 2012},
                        {'name': '2.0 TFSI (200 л.с.)', 'engine': '2.0', 'power': 200, 'year_from': 2004, 'year_to': 2012},
                        {'name': '1.9 TDI (105 л.с.)', 'engine': '1.9', 'power': 105, 'year_from': 2003, 'year_to': 2010},
                    ],
                    '8V (2012-2020)': [
                        {'name': '1.4 TFSI (125 л.с.)', 'engine': '1.4', 'power': 125, 'year_from': 2012, 'year_to': 2020},
                        {'name': '1.8 TFSI (180 л.с.)', 'engine': '1.8', 'power': 180, 'year_from': 2012, 'year_to': 2020},
                        {'name': '2.0 TDI (150 л.с.)', 'engine': '2.0', 'power': 150, 'year_from': 2012, 'year_to': 2020},
                    ],
                },
                'A4': {
                    'B8 (2007-2015)': [
                        {'name': '1.8 TFSI (160 л.с.)', 'engine': '1.8', 'power': 160, 'year_from': 2007, 'year_to': 2015},
                        {'name': '2.0 TFSI (180 л.с.)', 'engine': '2.0', 'power': 180, 'year_from': 2007, 'year_to': 2015},
                        {'name': '2.0 TDI (143 л.с.)', 'engine': '2.0', 'power': 143, 'year_from': 2007, 'year_to': 2015},
                        {'name': '3.0 TDI (240 л.с.)', 'engine': '3.0', 'power': 240, 'year_from': 2008, 'year_to': 2015},
                    ],
                    'B9 (2015-2023)': [
                        {'name': '1.4 TFSI (150 л.с.)', 'engine': '1.4', 'power': 150, 'year_from': 2015, 'year_to': 2023},
                        {'name': '2.0 TFSI (252 л.с.)', 'engine': '2.0', 'power': 252, 'year_from': 2015, 'year_to': 2023},
                    ],
                },
                'Q5': {
                    'I (2008-2017)': [
                        {'name': '2.0 TFSI (211 л.с.)', 'engine': '2.0', 'power': 211, 'year_from': 2008, 'year_to': 2017},
                        {'name': '3.0 TDI (245 л.с.)', 'engine': '3.0', 'power': 245, 'year_from': 2008, 'year_to': 2017},
                    ],
                    'II (2017-н.в.)': [
                        {'name': '2.0 TFSI (252 л.с.)', 'engine': '2.0', 'power': 252, 'year_from': 2017, 'year_to': None},
                        {'name': '3.0 TDI (286 л.с.)', 'engine': '3.0', 'power': 286, 'year_from': 2017, 'year_to': None},
                    ],
                },
            },
            'BMW': {
                '3 Series': {
                    'E90 (2005-2012)': [
                        {'name': '318i (143 л.с.)', 'engine': '2.0', 'power': 143, 'year_from': 2005, 'year_to': 2012},
                        {'name': '320i (170 л.с.)', 'engine': '2.0', 'power': 170, 'year_from': 2005, 'year_to': 2012},
                        {'name': '325i (218 л.с.)', 'engine': '2.5', 'power': 218, 'year_from': 2005, 'year_to': 2012},
                        {'name': '330i (272 л.с.)', 'engine': '3.0', 'power': 272, 'year_from': 2005, 'year_to': 2012},
                    ],
                    'F30 (2012-2019)': [
                        {'name': '316i (136 л.с.)', 'engine': '1.6', 'power': 136, 'year_from': 2012, 'year_to': 2019},
                        {'name': '320i (184 л.с.)', 'engine': '2.0', 'power': 184, 'year_from': 2012, 'year_to': 2019},
                        {'name': '328i (245 л.с.)', 'engine': '2.0', 'power': 245, 'year_from': 2012, 'year_to': 2019},
                    ],
                },
                '5 Series': {
                    'E60 (2003-2010)': [
                        {'name': '520i (170 л.с.)', 'engine': '2.2', 'power': 170, 'year_from': 2003, 'year_to': 2010},
                        {'name': '525i (218 л.с.)', 'engine': '2.5', 'power': 218, 'year_from': 2003, 'year_to': 2010},
                        {'name': '530i (272 л.с.)', 'engine': '3.0', 'power': 272, 'year_from': 2003, 'year_to': 2010},
                    ],
                    'F10 (2010-2017)': [
                        {'name': '520i (184 л.с.)', 'engine': '2.0', 'power': 184, 'year_from': 2010, 'year_to': 2017},
                        {'name': '528i (245 л.с.)', 'engine': '2.0', 'power': 245, 'year_from': 2010, 'year_to': 2017},
                    ],
                },
                'X5': {
                    'E70 (2006-2013)': [
                        {'name': 'xDrive30i (272 л.с.)', 'engine': '3.0', 'power': 272, 'year_from': 2006, 'year_to': 2013},
                        {'name': 'xDrive35i (306 л.с.)', 'engine': '3.0', 'power': 306, 'year_from': 2006, 'year_to': 2013},
                    ],
                    'F15 (2013-2018)': [
                        {'name': 'xDrive30d (258 л.с.)', 'engine': '3.0', 'power': 258, 'year_from': 2013, 'year_to': 2018},
                        {'name': 'xDrive40e (313 л.с.)', 'engine': '2.0', 'power': 313, 'year_from': 2015, 'year_to': 2018},
                    ],
                },
            },
            'Mercedes-Benz': {
                'C-Class': {
                    'W204 (2007-2014)': [
                        {'name': 'C180 (156 л.с.)', 'engine': '1.8', 'power': 156, 'year_from': 2007, 'year_to': 2014},
                        {'name': 'C200 (184 л.с.)', 'engine': '1.8', 'power': 184, 'year_from': 2007, 'year_to': 2014},
                        {'name': 'C250 (204 л.с.)', 'engine': '1.8', 'power': 204, 'year_from': 2011, 'year_to': 2014},
                    ],
                    'W205 (2014-2021)': [
                        {'name': 'C180 (156 л.с.)', 'engine': '1.6', 'power': 156, 'year_from': 2014, 'year_to': 2021},
                        {'name': 'C200 (184 л.с.)', 'engine': '2.0', 'power': 184, 'year_from': 2014, 'year_to': 2021},
                        {'name': 'C300 (258 л.с.)', 'engine': '2.0', 'power': 258, 'year_from': 2015, 'year_to': 2021},
                    ],
                },
                'E-Class': {
                    'W212 (2009-2016)': [
                        {'name': 'E200 (184 л.с.)', 'engine': '2.0', 'power': 184, 'year_from': 2009, 'year_to': 2016},
                        {'name': 'E250 (211 л.с.)', 'engine': '2.1', 'power': 211, 'year_from': 2009, 'year_to': 2016},
                    ],
                    'W213 (2016-н.в.)': [
                        {'name': 'E200 (184 л.с.)', 'engine': '2.0', 'power': 184, 'year_from': 2016, 'year_to': None},
                        {'name': 'E300 (258 л.с.)', 'engine': '2.0', 'power': 258, 'year_from': 2016, 'year_to': None},
                    ],
                },
            },
            'Volkswagen': {
                'Golf': {
                    'VI (2008-2013)': [
                        {'name': '1.4 TSI (122 л.с.)', 'engine': '1.4', 'power': 122, 'year_from': 2008, 'year_to': 2013},
                        {'name': '1.6 TDI (105 л.с.)', 'engine': '1.6', 'power': 105, 'year_from': 2008, 'year_to': 2013},
                        {'name': '2.0 GTI (210 л.с.)', 'engine': '2.0', 'power': 210, 'year_from': 2009, 'year_to': 2013},
                    ],
                    'VII (2012-2020)': [
                        {'name': '1.2 TSI (105 л.с.)', 'engine': '1.2', 'power': 105, 'year_from': 2012, 'year_to': 2020},
                        {'name': '1.4 TSI (140 л.с.)', 'engine': '1.4', 'power': 140, 'year_from': 2012, 'year_to': 2020},
                        {'name': '2.0 TDI (150 л.с.)', 'engine': '2.0', 'power': 150, 'year_from': 2012, 'year_to': 2020},
                    ],
                },
                'Passat': {
                    'B7 (2010-2015)': [
                        {'name': '1.4 TSI (122 л.с.)', 'engine': '1.4', 'power': 122, 'year_from': 2010, 'year_to': 2015},
                        {'name': '1.8 TSI (160 л.с.)', 'engine': '1.8', 'power': 160, 'year_from': 2010, 'year_to': 2015},
                        {'name': '2.0 TDI (140 л.с.)', 'engine': '2.0', 'power': 140, 'year_from': 2010, 'year_to': 2015},
                    ],
                    'B8 (2014-2022)': [
                        {'name': '1.4 TSI (125 л.с.)', 'engine': '1.4', 'power': 125, 'year_from': 2014, 'year_to': 2022},
                        {'name': '2.0 TSI (220 л.с.)', 'engine': '2.0', 'power': 220, 'year_from': 2014, 'year_to': 2022},
                    ],
                },
                'Tiguan': {
                    'I (2007-2017)': [
                        {'name': '1.4 TSI (150 л.с.)', 'engine': '1.4', 'power': 150, 'year_from': 2007, 'year_to': 2017},
                        {'name': '2.0 TDI (140 л.с.)', 'engine': '2.0', 'power': 140, 'year_from': 2007, 'year_to': 2017},
                    ],
                    'II (2016-н.в.)': [
                        {'name': '1.4 TSI (150 л.с.)', 'engine': '1.4', 'power': 150, 'year_from': 2016, 'year_to': None},
                        {'name': '2.0 TSI (180 л.с.)', 'engine': '2.0', 'power': 180, 'year_from': 2016, 'year_to': None},
                    ],
                },
            },
            'Toyota': {
                'Camry': {
                    'XV50 (2011-2017)': [
                        {'name': '2.0 (148 л.с.)', 'engine': '2.0', 'power': 148, 'year_from': 2011, 'year_to': 2017},
                        {'name': '2.5 (181 л.с.)', 'engine': '2.5', 'power': 181, 'year_from': 2011, 'year_to': 2017},
                        {'name': '3.5 (249 л.с.)', 'engine': '3.5', 'power': 249, 'year_from': 2011, 'year_to': 2017},
                    ],
                    'XV70 (2017-н.в.)': [
                        {'name': '2.5 (181 л.с.)', 'engine': '2.5', 'power': 181, 'year_from': 2017, 'year_to': None},
                        {'name': '3.5 (249 л.с.)', 'engine': '3.5', 'power': 249, 'year_from': 2017, 'year_to': None},
                    ],
                },
                'RAV4': {
                    'XA40 (2012-2018)': [
                        {'name': '2.0 (146 л.с.)', 'engine': '2.0', 'power': 146, 'year_from': 2012, 'year_to': 2018},
                        {'name': '2.5 (180 л.с.)', 'engine': '2.5', 'power': 180, 'year_from': 2012, 'year_to': 2018},
                    ],
                    'XA50 (2018-н.в.)': [
                        {'name': '2.0 (173 л.с.)', 'engine': '2.0', 'power': 173, 'year_from': 2018, 'year_to': None},
                        {'name': '2.5 (199 л.с.)', 'engine': '2.5', 'power': 199, 'year_from': 2018, 'year_to': None},
                    ],
                },
            },
        }
        
        created_brands = 0
        created_models = 0
        created_generations = 0
        created_modifications = 0
        
        for brand_name, models in vehicles_data.items():
            # Создаем бренд
            brand, created = CarBrand.objects.get_or_create(name=brand_name)
            if created:
                created_brands += 1
                self.stdout.write(f'  ✓ Создан бренд: {brand_name}')
            
            for model_name, generations in models.items():
                # Создаем модель
                model, created = CarModel.objects.get_or_create(
                    name=model_name,
                    brand=brand
                )
                if created:
                    created_models += 1
                    self.stdout.write(f'    ✓ Создана модель: {model_name}')
                
                for generation_name, modifications in generations.items():
                    # Извлекаем годы из названия поколения (например: "8P (2003-2012)")
                    import re
                    year_match = re.search(r'\((\d{4})-', generation_name)
                    year_start = int(year_match.group(1)) if year_match else 2000
                    
                    year_end_match = re.search(r'-(\d{4})\)', generation_name)
                    year_end = int(year_end_match.group(1)) if year_end_match else None
                    
                    # Создаем поколение
                    generation, created = CarGeneration.objects.get_or_create(
                        name=generation_name,
                        model=model,
                        defaults={
                            'year_start': year_start,
                            'year_end': year_end,
                        }
                    )
                    if created:
                        created_generations += 1
                        self.stdout.write(f'      ✓ Создано поколение: {generation_name}')
                    
                    # Создаем модификации
                    for mod_data in modifications:
                        modification, created = CarModification.objects.get_or_create(
                            name=mod_data['name'],
                            generation=generation,
                            defaults={
                                'engine_volume': mod_data['engine'],
                                'power': mod_data['power'],
                            }
                        )
                        if created:
                            created_modifications += 1
                            self.stdout.write(f'        ✓ Создана модификация: {mod_data["name"]}')
        
        self.stdout.write(self.style.SUCCESS(f'\n✓ Создано:'))
        self.stdout.write(self.style.SUCCESS(f'  Брендов: {created_brands}'))
        self.stdout.write(self.style.SUCCESS(f'  Моделей: {created_models}'))
        self.stdout.write(self.style.SUCCESS(f'  Поколений: {created_generations}'))
        self.stdout.write(self.style.SUCCESS(f'  Модификаций: {created_modifications}'))
