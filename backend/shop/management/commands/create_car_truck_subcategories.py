from django.core.management.base import BaseCommand
from shop.models import Category


class Command(BaseCommand):
    help = 'Создает подкатегории для легковых автомобилей и грузовиков'

    def handle(self, *args, **options):
        # Получаем родительские категории
        try:
            cars_parent = Category.objects.get(slug='legkovye-avtomobili')
            trucks_parent = Category.objects.get(slug='gruzoviki')
        except Category.DoesNotExist as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка: не найдена родительская категория. {e}')
            )
            return

        # Подкатегории для легковых автомобилей
        car_subcategories = [
            {
                'name': 'Двигатель',
                'slug': 'dvigatel-legkovye',
                'description': 'Запчасти для двигателя легковых автомобилей',
                'order': 1,
            },
            {
                'name': 'Трансмиссия',
                'slug': 'transmissiya-legkovye',
                'description': 'КПП, сцепление, привод',
                'order': 2,
            },
            {
                'name': 'Подвеска и рулевое управление',
                'slug': 'podveska-i-rulevoe-legkovye',
                'description': 'Амортизаторы, пружины, рулевые тяги',
                'order': 3,
            },
            {
                'name': 'Тормозная система',
                'slug': 'tormoznaya-sistema-legkovye',
                'description': 'Тормозные диски, колодки, суппорты',
                'order': 4,
            },
            {
                'name': 'Система охлаждения',
                'slug': 'sistema-ohlazhdeniya-legkovye',
                'description': 'Радиаторы, термостаты, помпы',
                'order': 5,
            },
            {
                'name': 'Топливная система',
                'slug': 'toplivnaya-sistema-legkovye',
                'description': 'Топливные насосы, форсунки, фильтры',
                'order': 6,
            },
            {
                'name': 'Выхлопная система',
                'slug': 'vyhlopnaya-sistema-legkovye',
                'description': 'Глушители, резонаторы, катализаторы',
                'order': 7,
            },
            {
                'name': 'Электрооборудование',
                'slug': 'elektrooborudovanie-legkovye',
                'description': 'Генераторы, стартеры, аккумуляторы',
                'order': 8,
            },
            {
                'name': 'Кузовные детали',
                'slug': 'kuzovnye-detali-legkovye',
                'description': 'Крылья, бамперы, капоты, двери',
                'order': 9,
            },
            {
                'name': 'Салон',
                'slug': 'salon-legkovye',
                'description': 'Сиденья, обшивки, панели',
                'order': 10,
            },
        ]

        # Подкатегории для грузовиков
        truck_subcategories = [
            {
                'name': 'Двигатель',
                'slug': 'dvigatel-gruzoviki',
                'description': 'Запчасти для двигателя грузовых автомобилей',
                'order': 1,
            },
            {
                'name': 'Трансмиссия',
                'slug': 'transmissiya-gruzoviki',
                'description': 'КПП, сцепление, привод для грузовиков',
                'order': 2,
            },
            {
                'name': 'Подвеска',
                'slug': 'podveska-gruzoviki',
                'description': 'Рессоры, амортизаторы, балки мостов',
                'order': 3,
            },
            {
                'name': 'Тормозная система',
                'slug': 'tormoznaya-sistema-gruzoviki',
                'description': 'Тормозные камеры, барабаны, колодки',
                'order': 4,
            },
            {
                'name': 'Система охлаждения',
                'slug': 'sistema-ohlazhdeniya-gruzoviki',
                'description': 'Радиаторы, интеркулеры, термостаты',
                'order': 5,
            },
            {
                'name': 'Топливная система',
                'slug': 'toplivnaya-sistema-gruzoviki',
                'description': 'ТНВД, форсунки, баки',
                'order': 6,
            },
            {
                'name': 'Выхлопная система',
                'slug': 'vyhlopnaya-sistema-gruzoviki',
                'description': 'Глушители, гофры, сажевые фильтры',
                'order': 7,
            },
            {
                'name': 'Электрооборудование',
                'slug': 'elektrooborudovanie-gruzoviki',
                'description': 'Генераторы, стартеры, проводка',
                'order': 8,
            },
            {
                'name': 'Кузовные детали',
                'slug': 'kuzovnye-detali-gruzoviki',
                'description': 'Крылья, бамперы, решетки',
                'order': 9,
            },
            {
                'name': 'Кабина',
                'slug': 'kabina-gruzoviki',
                'description': 'Детали кабины, сиденья, обшивки',
                'order': 10,
            },
        ]

        created_count = 0
        updated_count = 0

        # Создаем подкатегории для легковых автомобилей
        self.stdout.write(self.style.HTTP_INFO('\n📦 Создание подкатегорий для ЛЕГКОВЫХ АВТОМОБИЛЕЙ:'))
        for subcat_data in car_subcategories:
            subcat_data['parent'] = cars_parent
            subcat_data['show_in'] = 'cars'
            subcat_data['is_active'] = True
            subcat_data['show_brands'] = False
            
            category, created = Category.objects.update_or_create(
                slug=subcat_data['slug'],
                defaults=subcat_data
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

        # Создаем подкатегории для грузовиков
        self.stdout.write(self.style.HTTP_INFO('\n🚚 Создание подкатегорий для ГРУЗОВИКОВ:'))
        for subcat_data in truck_subcategories:
            subcat_data['parent'] = trucks_parent
            subcat_data['show_in'] = 'trucks'
            subcat_data['is_active'] = True
            subcat_data['show_brands'] = False
            
            category, created = Category.objects.update_or_create(
                slug=subcat_data['slug'],
                defaults=subcat_data
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
                f'Готово!\n'
                f'Создано новых подкатегорий: {created_count}\n'
                f'Обновлено существующих: {updated_count}\n'
                f'Всего подкатегорий: {created_count + updated_count}\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
            )
        )


