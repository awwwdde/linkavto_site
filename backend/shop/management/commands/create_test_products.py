from django.core.management.base import BaseCommand
from shop.models import Category, Product, CarBrand, Manufacturer
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Создает тестовые товары для легковых автомобилей'

    def handle(self, *args, **options):
        # Получаем бренды
        try:
            brands = list(CarBrand.objects.filter(is_active=True)[:8])
            if not brands:
                self.stdout.write(self.style.ERROR('Не найдены бренды легковых автомобилей'))
                return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Ошибка при получении брендов: {e}'))
            return

        # Получаем или создаем производителей
        manufacturers_data = [
            'Bosch', 'Mann+Hummel', 'Mahle', 'Sachs', 'Brembo',
            'Ferodo', 'Gates', 'Dayco', 'NGK', 'Denso'
        ]
        manufacturers = []
        for name in manufacturers_data:
            manufacturer, _ = Manufacturer.objects.get_or_create(
                name=name,
                defaults={'slug': name.lower().replace('+', '-'), 'is_active': True}
            )
            manufacturers.append(manufacturer)

        # Шаблоны товаров для каждой подподкатегории
        products_templates = {
            'grm-legkovye': [
                {'name': 'Ремень ГРМ', 'price_range': (1500, 4500), 'keywords': ['усиленный', 'оригинальный', 'зубчатый']},
                {'name': 'Ролик ГРМ натяжной', 'price_range': (800, 2500), 'keywords': ['натяжной', 'опорный', 'обводной']},
                {'name': 'Помпа водяная', 'price_range': (2000, 5500), 'keywords': ['с металлической крыльчаткой', 'усиленная', 'с прокладкой']},
                {'name': 'Комплект ГРМ', 'price_range': (3500, 9000), 'keywords': ['полный', 'с помпой', 'усиленный']},
                {'name': 'Цепь ГРМ', 'price_range': (4000, 12000), 'keywords': ['усиленная', 'двухрядная', 'оригинальная']},
            ],
            'porshnevaya-gruppa-legkovye': [
                {'name': 'Поршень двигателя', 'price_range': (1200, 4000), 'keywords': ['стандартный', 'ремонтный +0.25', 'ремонтный +0.5']},
                {'name': 'Кольца поршневые', 'price_range': (800, 2500), 'keywords': ['стандарт', 'ремонт +0.25', 'хромированные']},
                {'name': 'Палец поршневой', 'price_range': (300, 900), 'keywords': ['с стопорными кольцами', 'усиленный', 'полнопроходной']},
                {'name': 'Гильза цилиндра', 'price_range': (1500, 4500), 'keywords': ['мокрая', 'сухая', 'с буртом']},
            ],
            'sistema-smazki-legkovye': [
                {'name': 'Масляный насос', 'price_range': (2500, 7000), 'keywords': ['с шестернями', 'с редукционным клапаном', 'усиленный']},
                {'name': 'Фильтр масляный', 'price_range': (250, 800), 'keywords': ['стандартный', 'удлиненный', 'с клапаном']},
                {'name': 'Маслоприемник', 'price_range': (600, 1800), 'keywords': ['с сеткой', 'с прокладкой', 'усиленный']},
                {'name': 'Прокладка масляного поддона', 'price_range': (200, 600), 'keywords': ['резиновая', 'пробковая', 'с герметиком']},
            ],
            'prokladki-dvigatelya-legkovye': [
                {'name': 'Прокладка ГБЦ', 'price_range': (1200, 4500), 'keywords': ['металлическая', 'усиленная', 'многослойная']},
                {'name': 'Прокладка клапанной крышки', 'price_range': (300, 1200), 'keywords': ['резиновая', 'с металлической основой', 'термостойкая']},
                {'name': 'Прокладка впускного коллектора', 'price_range': (400, 1500), 'keywords': ['резиновая', 'паронитовая', 'термостойкая']},
                {'name': 'Комплект прокладок двигателя', 'price_range': (2500, 8000), 'keywords': ['полный', 'малый', 'верхний']},
            ],
            'stseplenie-legkovye': [
                {'name': 'Комплект сцепления', 'price_range': (3500, 12000), 'keywords': ['трехкомпонентный', 'усиленный', 'керамический']},
                {'name': 'Диск сцепления', 'price_range': (1500, 5000), 'keywords': ['ведомый', 'усиленный', 'демпферный']},
                {'name': 'Корзина сцепления', 'price_range': (2000, 7000), 'keywords': ['нажимная', 'усиленная', 'диафрагменная']},
                {'name': 'Выжимной подшипник', 'price_range': (500, 1800), 'keywords': ['гидравлический', 'механический', 'усиленный']},
            ],
            'kpp-legkovye': [
                {'name': 'Синхронизатор КПП', 'price_range': (1200, 4000), 'keywords': ['1-2 передачи', '3-4 передачи', '5-6 передачи']},
                {'name': 'Подшипник первичного вала', 'price_range': (800, 2500), 'keywords': ['роликовый', 'шариковый', 'усиленный']},
                {'name': 'Сальник КПП', 'price_range': (200, 700), 'keywords': ['первичного вала', 'вторичного вала', 'дифференциала']},
                {'name': 'Масло трансмиссионное', 'price_range': (600, 2500), 'keywords': ['75W-90', '75W-85', 'синтетика']},
            ],
            'privody-legkovye': [
                {'name': 'ШРУС внутренний', 'price_range': (1500, 5000), 'keywords': ['левый', 'правый', 'усиленный']},
                {'name': 'ШРУС наружный', 'price_range': (1200, 4000), 'keywords': ['левый', 'правый', 'с ABS']},
                {'name': 'Пыльник ШРУСа', 'price_range': (150, 500), 'keywords': ['внутренний', 'наружный', 'усиленный']},
                {'name': 'Полуось', 'price_range': (3000, 9000), 'keywords': ['левая', 'правая', 'в сборе с ШРУСами']},
            ],
            'amortizatory-legkovye': [
                {'name': 'Амортизатор передний', 'price_range': (2000, 7000), 'keywords': ['газомасляный', 'масляный', 'газовый']},
                {'name': 'Амортизатор задний', 'price_range': (1800, 6000), 'keywords': ['газомасляный', 'масляный', 'усиленный']},
                {'name': 'Стойка передняя в сборе', 'price_range': (4000, 12000), 'keywords': ['левая', 'правая', 'с подшипником']},
                {'name': 'Опора амортизатора', 'price_range': (400, 1500), 'keywords': ['передняя', 'задняя', 'с подшипником']},
            ],
            'rychagi-legkovye': [
                {'name': 'Рычаг передний нижний', 'price_range': (1500, 5500), 'keywords': ['левый', 'правый', 'с сайлентблоками']},
                {'name': 'Рычаг передний верхний', 'price_range': (1200, 4500), 'keywords': ['левый', 'правый', 'усиленный']},
                {'name': 'Сайлентблок рычага', 'price_range': (200, 800), 'keywords': ['передний', 'задний', 'полиуретановый']},
                {'name': 'Втулка стабилизатора', 'price_range': (150, 500), 'keywords': ['полиуретановая', 'резиновая', 'усиленная']},
            ],
            'sharovye-opory-legkovye': [
                {'name': 'Шаровая опора передняя', 'price_range': (500, 2500), 'keywords': ['нижняя', 'верхняя', 'усиленная']},
                {'name': 'Шаровая опора задняя', 'price_range': (600, 2800), 'keywords': ['верхняя', 'нижняя', 'с креплением']},
            ],
            'rulevye-tyagi-legkovye': [
                {'name': 'Наконечник рулевой тяги', 'price_range': (400, 1500), 'keywords': ['левый', 'правый', 'усиленный']},
                {'name': 'Тяга рулевая', 'price_range': (800, 2800), 'keywords': ['левая', 'правая', 'регулируемая']},
                {'name': 'Рулевая трапеция', 'price_range': (1500, 5000), 'keywords': ['в сборе', 'усиленная', 'с наконечниками']},
            ],
            'tormoznye-diski-legkovye': [
                {'name': 'Диск тормозной передний', 'price_range': (1200, 4500), 'keywords': ['вентилируемый', 'невентилируемый', 'перфорированный']},
                {'name': 'Диск тормозной задний', 'price_range': (1000, 4000), 'keywords': ['сплошной', 'вентилируемый', 'с покрытием']},
            ],
            'tormoznye-kolodki-legkovye': [
                {'name': 'Колодки тормозные передние', 'price_range': (800, 3500), 'keywords': ['керамические', 'полуметаллические', 'органические']},
                {'name': 'Колодки тормозные задние', 'price_range': (700, 3000), 'keywords': ['дисковые', 'барабанные', 'керамические']},
            ],
            'tormoznye-supporty-legkovye': [
                {'name': 'Суппорт тормозной передний', 'price_range': (2500, 8000), 'keywords': ['левый', 'правый', 'с поршнями']},
                {'name': 'Поршень суппорта', 'price_range': (300, 1200), 'keywords': ['передний', 'задний', 'набор']},
                {'name': 'Ремкомплект суппорта', 'price_range': (400, 1500), 'keywords': ['передний', 'задний', 'с пыльниками']},
            ],
        }

        created_count = 0
        skipped_count = 0

        for category_slug, templates in products_templates.items():
            try:
                # Получаем подподкатегорию (3-й уровень)
                subsubcategory = Category.objects.get(slug=category_slug, is_active=True)
                # Получаем подкатегорию (2-й уровень) - родитель
                subcategory = subsubcategory.parent
                if not subcategory:
                    self.stdout.write(self.style.WARNING(f'Нет родительской категории для {category_slug}'))
                    continue

                self.stdout.write(
                    self.style.HTTP_INFO(f'\n📦 Создание товаров для "{subsubcategory.name}":')
                )

                # Создаем товары для каждого шаблона
                for template in templates:
                    # Создаем несколько вариантов товара с разными брендами и ключевыми словами
                    for keyword in template['keywords'][:2]:  # Берем первые 2 варианта
                        for brand in random.sample(brands, min(3, len(brands))):  # 3 случайных бренда
                            product_name = f"{template['name']} {keyword} {brand.name}"
                            
                            # Проверяем, существует ли такой товар
                            if Product.objects.filter(name=product_name).exists():
                                skipped_count += 1
                                continue

                            # Генерируем цену
                            price = Decimal(random.randint(
                                template['price_range'][0],
                                template['price_range'][1]
                            ))
                            
                            # Случайно добавляем старую цену для акций
                            old_price = None
                            if random.random() < 0.3:  # 30% товаров со скидкой
                                old_price = price * Decimal(random.uniform(1.15, 1.4))

                            # Создаем товар
                            product = Product.objects.create(
                                name=product_name,
                                category=subsubcategory,  # Привязываем к подподкатегории
                                manufacturer=random.choice(manufacturers),
                                car_brand=brand,
                                price=price,
                                old_price=old_price,
                                stock=random.randint(0, 50),
                                is_active=True,
                                is_featured=random.random() < 0.2,  # 20% рекомендуемых
                                is_new=random.random() < 0.15,  # 15% новинок
                                is_original=random.random() < 0.3,  # 30% оригинальных
                                vehicle_type='car',
                                description=f"Качественные {template['name'].lower()} {keyword} для {brand.name}. "
                                           f"Подходят для большинства моделей. Гарантия качества.",
                                short_description=f"{template['name']} {keyword}",
                                part_number=f"{brand.slug.upper()}-{random.randint(10000, 99999)}",
                            )

                            created_count += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'  ✓ {product.name} - {product.price}₽')
                            )

            except Category.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'Не найдена категория: {category_slug}')
                )
                continue
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Ошибка при создании товаров для {category_slug}: {e}')
                )
                continue

        self.stdout.write(
            self.style.SUCCESS(
                f'\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                f'Готово!\n'
                f'Создано товаров: {created_count}\n'
                f'Пропущено (дубликаты): {skipped_count}\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
            )
        )


