from django.core.management.base import BaseCommand
from shop.models import Category


class Command(BaseCommand):
    help = 'Создает 10 корневых категорий для всех разделов магазина'

    def handle(self, *args, **options):
        categories_data = [
            {
                'name': 'Легковые автомобили',
                'slug': 'legkovye-avtomobili',
                'show_in': 'cars',
                'description': 'Запчасти для легковых автомобилей',
                'order': 1,
                'is_active': True,
                'show_brands': True,
            },
            {
                'name': 'Грузовики',
                'slug': 'gruzoviki',
                'show_in': 'trucks',
                'description': 'Запчасти для грузовых автомобилей',
                'order': 2,
                'is_active': True,
                'show_brands': True,
            },
            {
                'name': 'Мототехника',
                'slug': 'mototehnika',
                'show_in': 'moto',
                'description': 'Запчасти для мототехники',
                'order': 3,
                'is_active': True,
                'show_brands': True,
            },
            {
                'name': 'Спецтехника',
                'slug': 'spectehnika',
                'show_in': 'special',
                'description': 'Запчасти для спецтехники',
                'order': 4,
                'is_active': True,
                'show_brands': True,
            },
            {
                'name': 'Аксессуары',
                'slug': 'aksessuary',
                'show_in': 'accessories',
                'description': 'Автомобильные аксессуары',
                'order': 5,
                'is_active': True,
                'show_brands': False,
            },
            {
                'name': 'Автохимия и масла',
                'slug': 'avtohimiya-i-masla',
                'show_in': 'chemistry',
                'description': 'Автохимия, масла и технические жидкости',
                'order': 6,
                'is_active': True,
                'show_brands': False,
            },
            {
                'name': 'Инструменты',
                'slug': 'instrumenty',
                'show_in': 'tools',
                'description': 'Инструменты для ремонта и обслуживания',
                'order': 7,
                'is_active': True,
                'show_brands': False,
            },
            {
                'name': 'Шины и диски',
                'slug': 'shiny-i-diski',
                'show_in': 'tires',
                'description': 'Шины и диски для автомобилей',
                'order': 8,
                'is_active': True,
                'show_brands': False,
            },
            {
                'name': 'Автоэлектрика',
                'slug': 'avtoelektrika',
                'show_in': 'electrics',
                'description': 'Электрооборудование и электроника',
                'order': 9,
                'is_active': True,
                'show_brands': False,
            },
            {
                'name': 'Для ТО',
                'slug': 'dlya-to',
                'show_in': 'dlya-to',
                'description': 'Товары для технического обслуживания',
                'order': 10,
                'is_active': True,
                'show_brands': False,
            },
        ]

        created_count = 0
        updated_count = 0

        for cat_data in categories_data:
            category, created = Category.objects.update_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Создана категория: {category.name}')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    self.style.WARNING(f'⟳ Обновлена категория: {category.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                f'Готово!\n'
                f'Создано новых категорий: {created_count}\n'
                f'Обновлено существующих: {updated_count}\n'
                f'Всего категорий: {created_count + updated_count}\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
            )
        )


