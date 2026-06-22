from django.core.management.base import BaseCommand
from shop.models import Category


class Command(BaseCommand):
    help = 'Добавляет тестовые подподкатегории (по 10 штук) в подкатегории: Двигатель, Трансмиссия, Подвеска, Тормозная система'

    def handle(self, *args, **options):
        # Найти корневую категорию "Легковые автомобили"
        cars_root = Category.objects.filter(
            name__icontains='легков',
            parent__isnull=True
        ).first()
        
        # Если не найдена по имени, ищем по show_in
        if not cars_root:
            cars_root = Category.objects.filter(
                show_in='cars',
                parent__isnull=True
            ).first()
        
        if not cars_root:
            self.stdout.write(
                self.style.ERROR('❌ Корневая категория "Легковые автомобили" не найдена')
            )
            return

        # Найти нужные подкатегории
        parent_categories = {
            'Двигатель': Category.objects.filter(
                parent=cars_root,
                slug='dvigatel-legkovye'
            ).first(),
            'Трансмиссия': Category.objects.filter(
                parent=cars_root,
                slug='transmissiya-legkovye'
            ).first(),
            'Подвеска': Category.objects.filter(
                parent=cars_root,
                slug='podveska-i-rulevoe-legkovye'
            ).first(),
            'Тормозная система': Category.objects.filter(
                parent=cars_root,
                slug='tormoznaya-sistema-legkovye'
            ).first(),
        }

        # Тестовые подподкатегории для Двигатель
        engine_subcategories = [
            {'name': 'ГРМ комплект', 'description': 'Ремни ГРМ, ролики, натяжители', 'order': 1},
            {'name': 'Поршневая группа', 'description': 'Поршни, кольца, пальцы', 'order': 2},
            {'name': 'Коленчатый вал', 'description': 'Коленвалы, вкладыши', 'order': 3},
            {'name': 'Головка блока цилиндров', 'description': 'ГБЦ, клапаны, седла', 'order': 4},
            {'name': 'Система смазки', 'description': 'Масляные насосы, фильтры', 'order': 5},
            {'name': 'Прокладки двигателя', 'description': 'Прокладки ГБЦ, клапанной крышки', 'order': 6},
            {'name': 'Навесное оборудование', 'description': 'Генератор, стартер, компрессор', 'order': 7},
            {'name': 'Система охлаждения двигателя', 'description': 'Помпа, термостат, радиатор', 'order': 8},
            {'name': 'Турбокомпрессор', 'description': 'Турбины, интеркулеры', 'order': 9},
            {'name': 'Система впуска', 'description': 'Впускной коллектор, дроссельная заслонка', 'order': 10},
        ]

        # Тестовые подподкатегории для Трансмиссия
        transmission_subcategories = [
            {'name': 'Сцепление', 'description': 'Комплекты сцепления, диски, корзины', 'order': 1},
            {'name': 'КПП механическая', 'description': 'Запчасти МКПП', 'order': 2},
            {'name': 'АКПП', 'description': 'Запчасти автоматических КПП', 'order': 3},
            {'name': 'Вариатор CVT', 'description': 'Запчасти вариатора', 'order': 4},
            {'name': 'Приводы', 'description': 'ШРУС, полуоси, пыльники', 'order': 5},
            {'name': 'Раздаточная коробка', 'description': 'Запчасти раздатки', 'order': 6},
            {'name': 'Карданный вал', 'description': 'Карданы, крестовины', 'order': 7},
            {'name': 'Дифференциал', 'description': 'Запчасти дифференциала', 'order': 8},
            {'name': 'Масло для КПП', 'description': 'Трансмиссионные масла', 'order': 9},
            {'name': 'Подшипники трансмиссии', 'description': 'Подшипники КПП, раздатки', 'order': 10},
        ]

        # Тестовые подподкатегории для Подвеска
        suspension_subcategories = [
            {'name': 'Амортизаторы', 'description': 'Стойки, амортизаторы передние и задние', 'order': 1},
            {'name': 'Пружины', 'description': 'Пружины подвески', 'order': 2},
            {'name': 'Рычаги подвески', 'description': 'Рычаги передние и задние', 'order': 3},
            {'name': 'Шаровые опоры', 'description': 'Шаровые опоры, наконечники', 'order': 4},
            {'name': 'Сайлентблоки', 'description': 'Резино-металлические шарниры', 'order': 5},
            {'name': 'Рулевые тяги', 'description': 'Рулевые наконечники, тяги', 'order': 6},
            {'name': 'Рулевая рейка', 'description': 'Рулевые рейки и редукторы', 'order': 7},
            {'name': 'Стойки стабилизатора', 'description': 'Стойки стабилизатора поперечной устойчивости', 'order': 8},
            {'name': 'Подшипники ступиц', 'description': 'Подшипники передних и задних ступиц', 'order': 9},
            {'name': 'Опора двигателя', 'description': 'Подушки двигателя и КПП', 'order': 10},
        ]

        # Тестовые подподкатегории для Тормозная система
        brakes_subcategories = [
            {'name': 'Тормозные диски', 'description': 'Передние и задние диски', 'order': 1},
            {'name': 'Тормозные колодки', 'description': 'Колодки передние и задние', 'order': 2},
            {'name': 'Тормозные суппорты', 'description': 'Суппорты, скобы, поршни', 'order': 3},
            {'name': 'Тормозные шланги', 'description': 'Шланги, трубки тормозной системы', 'order': 4},
            {'name': 'Главный тормозной цилиндр', 'description': 'ГТЦ, вакуумный усилитель', 'order': 5},
            {'name': 'Рабочий тормозной цилиндр', 'description': 'Тормозные цилиндры задние', 'order': 6},
            {'name': 'Тормозная жидкость', 'description': 'Тормозные жидкости', 'order': 7},
            {'name': 'ABS датчики', 'description': 'Датчики ABS, индуктивные кольца', 'order': 8},
            {'name': 'Тормозные барабаны', 'description': 'Тормозные барабаны задние', 'order': 9},
            {'name': 'Тормозные колодки барабанные', 'description': 'Колодки для барабанных тормозов', 'order': 10},
        ]

        # Словарь с данными для каждой категории
        categories_data = {
            'Двигатель': engine_subcategories,
            'Трансмиссия': transmission_subcategories,
            'Подвеска': suspension_subcategories,
            'Тормозная система': brakes_subcategories,
        }

        created_count = 0
        updated_count = 0
        errors = 0

        for category_name, parent_category in parent_categories.items():
            if not parent_category:
                self.stdout.write(
                    self.style.ERROR(f'\n❌ Не найдена категория: {category_name}')
                )
                errors += 1
                continue

            subcategories = categories_data.get(category_name, [])
            
            self.stdout.write(
                self.style.HTTP_INFO(f'\n📁 Создание подподкатегорий для "{parent_category.name}":')
            )

            for subcat_data in subcategories:
                # Генерируем slug из названия
                from shop.utils import cyrillic_slugify
                base_slug = cyrillic_slugify(subcat_data['name'])
                
                # Создаем уникальный slug
                slug = base_slug
                counter = 1
                while Category.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                category_data = {
                    'name': subcat_data['name'],
                    'slug': slug,
                    'parent': parent_category,
                    'show_in': parent_category.show_in,
                    'is_active': True,
                    'show_brands': False,
                    'description': subcat_data.get('description', ''),
                    'order': subcat_data.get('order', 0),
                }

                category, created = Category.objects.update_or_create(
                    slug=slug,
                    defaults=category_data
                )

                if created:
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✓ Создана: {category.name}')
                    )
                else:
                    updated_count += 1
                    self.stdout.write(
                        self.style.WARNING(f'  ⟳ Обновлена: {category.name}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                f'✅ Готово!\n'
                f'Создано новых подподкатегорий: {created_count}\n'
                f'Обновлено существующих: {updated_count}\n'
                f'Ошибок: {errors}\n'
                f'Всего подподкатегорий: {created_count + updated_count}\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
            )
        )

