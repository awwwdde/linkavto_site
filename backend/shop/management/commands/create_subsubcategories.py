from django.core.management.base import BaseCommand
from shop.models import Category


class Command(BaseCommand):
    help = 'Создает подподкатегории (3-й уровень) для тестирования'

    def handle(self, *args, **options):
        # Подподкатегории для "Двигатель" (легковые)
        engine_car_data = {
            'parent_slug': 'dvigatel-legkovye',
            'subcategories': [
                {'name': 'ГРМ', 'slug': 'grm-legkovye', 'description': 'Ремни, ролики, цепи ГРМ', 'order': 1},
                {'name': 'Поршневая группа', 'slug': 'porshnevaya-gruppa-legkovye', 'description': 'Поршни, кольца, пальцы', 'order': 2},
                {'name': 'Система смазки', 'slug': 'sistema-smazki-legkovye', 'description': 'Масляные насосы, фильтры', 'order': 3},
                {'name': 'Прокладки двигателя', 'slug': 'prokladki-dvigatelya-legkovye', 'description': 'Прокладки ГБЦ, клапанной крышки', 'order': 4},
                {'name': 'Навесное оборудование', 'slug': 'navesnoe-oborudovanie-legkovye', 'description': 'Генератор, компрессор кондиционера', 'order': 5},
            ]
        }

        # Подподкатегории для "Трансмиссия" (легковые)
        transmission_car_data = {
            'parent_slug': 'transmissiya-legkovye',
            'subcategories': [
                {'name': 'Сцепление', 'slug': 'stseplenie-legkovye', 'description': 'Комплекты сцепления, диски', 'order': 1},
                {'name': 'КПП', 'slug': 'kpp-legkovye', 'description': 'Запчасти коробки передач', 'order': 2},
                {'name': 'АКПП', 'slug': 'akpp-legkovye', 'description': 'Запчасти автоматических КПП', 'order': 3},
                {'name': 'Приводы', 'slug': 'privody-legkovye', 'description': 'ШРУС, полуоси', 'order': 4},
                {'name': 'Раздаточная коробка', 'slug': 'razdatochnaya-korobka-legkovye', 'description': 'Запчасти раздатки', 'order': 5},
            ]
        }

        # Подподкатегории для "Подвеска" (легковые)
        suspension_car_data = {
            'parent_slug': 'podveska-i-rulevoe-legkovye',
            'subcategories': [
                {'name': 'Амортизаторы', 'slug': 'amortizatory-legkovye', 'description': 'Стойки, амортизаторы', 'order': 1},
                {'name': 'Пружины', 'slug': 'pruzhiny-legkovye', 'description': 'Пружины подвески', 'order': 2},
                {'name': 'Рычаги', 'slug': 'rychagi-legkovye', 'description': 'Рычаги подвески', 'order': 3},
                {'name': 'Шаровые опоры', 'slug': 'sharovye-opory-legkovye', 'description': 'Шаровые, опоры', 'order': 4},
                {'name': 'Рулевые тяги', 'slug': 'rulevye-tyagi-legkovye', 'description': 'Рулевые наконечники, тяги', 'order': 5},
                {'name': 'Рулевая рейка', 'slug': 'rulevaya-reyka-legkovye', 'description': 'Рулевые рейки и редукторы', 'order': 6},
            ]
        }

        # Подподкатегории для "Тормозная система" (легковые)
        brakes_car_data = {
            'parent_slug': 'tormoznaya-sistema-legkovye',
            'subcategories': [
                {'name': 'Тормозные диски', 'slug': 'tormoznye-diski-legkovye', 'description': 'Передние и задние диски', 'order': 1},
                {'name': 'Тормозные колодки', 'slug': 'tormoznye-kolodki-legkovye', 'description': 'Колодки передние и задние', 'order': 2},
                {'name': 'Тормозные суппорты', 'slug': 'tormoznye-supporty-legkovye', 'description': 'Суппорты, скобы', 'order': 3},
                {'name': 'Тормозные шланги', 'slug': 'tormoznye-shlangi-legkovye', 'description': 'Шланги, трубки', 'order': 4},
                {'name': 'Главный тормозной цилиндр', 'slug': 'glavnyj-tormoznoj-tsilindr-legkovye', 'description': 'ГТЦ, вакуумный усилитель', 'order': 5},
            ]
        }

        # Подподкатегории для "Двигатель" (грузовики)
        engine_truck_data = {
            'parent_slug': 'dvigatel-gruzoviki',
            'subcategories': [
                {'name': 'ГРМ', 'slug': 'grm-gruzoviki', 'description': 'Ремни, ролики, цепи ГРМ', 'order': 1},
                {'name': 'Поршневая группа', 'slug': 'porshnevaya-gruppa-gruzoviki', 'description': 'Поршни, кольца, гильзы', 'order': 2},
                {'name': 'Топливная аппаратура', 'slug': 'toplivnaya-apparatura-gruzoviki', 'description': 'ТНВД, форсунки', 'order': 3},
                {'name': 'Турбины', 'slug': 'turbiny-gruzoviki', 'description': 'Турбокомпрессоры', 'order': 4},
                {'name': 'Прокладки', 'slug': 'prokladki-gruzoviki', 'description': 'Прокладки двигателя', 'order': 5},
            ]
        }

        # Подподкатегории для "Трансмиссия" (грузовики)
        transmission_truck_data = {
            'parent_slug': 'transmissiya-gruzoviki',
            'subcategories': [
                {'name': 'Сцепление', 'slug': 'stseplenie-gruzoviki', 'description': 'Корзины, диски сцепления', 'order': 1},
                {'name': 'КПП', 'slug': 'kpp-gruzoviki', 'description': 'Запчасти КПП', 'order': 2},
                {'name': 'Карданные валы', 'slug': 'kardannye-valy-gruzoviki', 'description': 'Карданы, крестовины', 'order': 3},
                {'name': 'Мосты', 'slug': 'mosty-gruzoviki', 'description': 'Запчасти мостов', 'order': 4},
            ]
        }

        all_data = [
            engine_car_data,
            transmission_car_data,
            suspension_car_data,
            brakes_car_data,
            engine_truck_data,
            transmission_truck_data,
        ]

        created_count = 0
        updated_count = 0
        errors = 0

        for data in all_data:
            try:
                parent = Category.objects.get(slug=data['parent_slug'])
                
                self.stdout.write(
                    self.style.HTTP_INFO(f'\n📁 Создание подподкатегорий для "{parent.name}":')
                )

                for subcat_data in data['subcategories']:
                    subcat_data['parent'] = parent
                    subcat_data['show_in'] = parent.show_in
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

            except Category.DoesNotExist:
                errors += 1
                self.stdout.write(
                    self.style.ERROR(f'  ✗ Не найдена родительская категория: {data["parent_slug"]}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                f'Готово!\n'
                f'Создано новых подподкатегорий: {created_count}\n'
                f'Обновлено существующих: {updated_count}\n'
                f'Ошибок: {errors}\n'
                f'Всего подподкатегорий: {created_count + updated_count}\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
            )
        )


