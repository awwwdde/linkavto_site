"""
Команда для заполнения базы данных марками легковых автомобилей.

Важно:
- Добавляет ТОЛЬКО марки (CarBrand), без моделей/поколений/модификаций.
- Использует slug как ключ, чтобы не плодить дубликаты.
"""

from django.core.management.base import BaseCommand

from shop.models import CarBrand
from shop.utils import cyrillic_slugify


# Достаточно полный список марок (ASCII-названия, чтобы slug был валиден).
CAR_BRANDS: list[str] = [
    "AC",
    "Acura",
    "Aixam",
    "Alfa Romeo",
    "Alpina",
    "Aston Martin",
    "Audi",
    "Aurus",
    "BAIC",
    "BYD",
    "Bentley",
    "Bestune",
    "BMW",
    "Borgward",
    "Brilliance",
    "Bugatti",
    "Buick",
    "Cadillac",
    "Changan",
    "Chery",
    "Chevrolet",
    "Chrysler",
    "Citroen",
    "Cupra",
    "Dacia",
    "Daewoo",
    "Daihatsu",
    "Datsun",
    "Denza",
    "Dodge",
    "Dongfeng",
    "DS",
    "Evolute",
    "Exeed",
    "FAW",
    "Ferrari",
    "Fiat",
    "Fisker",
    "Ford",
    "Forthing",
    "Foton",
    "GAC",
    "GAZ",
    "Geely",
    "Genesis",
    "GMC",
    "Great Wall",
    "Haval",
    "Hawtai",
    "HiPhi",
    "Honda",
    "Hongqi",
    "Hummer",
    "Hyundai",
    "Infiniti",
    "Isuzu",
    "Iveco",
    "JAC",
    "Jaecoo",
    "Jaguar",
    "Jeep",
    "Jetour",
    "JMC",
    "KAIYI",
    "Kia",
    "Koenigsegg",
    "LADA",
    "Lamborghini",
    "Lancia",
    "Land Rover",
    "Lexus",
    "Li Auto",
    "Lifan",
    "Lincoln",
    "Lotus",
    "Lucid",
    "M-Hero",
    "Maserati",
    "Maybach",
    "Mazda",
    "McLaren",
    "Mercedes-Benz",
    "Mercury",
    "MG",
    "Mini",
    "Mitsubishi",
    "Moskvich",
    "NIO",
    "Nissan",
    "Oldsmobile",
    "Omoda",
    "Opel",
    "Ora",
    "Peugeot",
    "Plymouth",
    "Polestar",
    "Pontiac",
    "Porsche",
    "Proton",
    "RAM",
    "Ravon",
    "Renault",
    "Rivian",
    "Roewe",
    "Rolls-Royce",
    "Rover",
    "Saab",
    "Saipa",
    "Samsung",
    "Saturn",
    "Scion",
    "SEAT",
    "Seres",
    "Skoda",
    "Smart",
    "SsangYong",
    "Subaru",
    "Suzuki",
    "Tank",
    "Tata",
    "Tesla",
    "Toyota",
    "UAZ",
    "Vauxhall",
    "VAZ",
    "Venucia",
    "Volkswagen",
    "Volvo",
    "Voyah",
    "Wey",
    "Wuling",
    "Xiaomi",
    "Xpeng",
    "ZAZ",
    "ZEEKR",
    "Zotye",
]


class Command(BaseCommand):
    help = "Заполняет базу данных марками легковых автомобилей (CarBrand)"

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for name in CAR_BRANDS:
            name = (name or "").strip()
            if not name:
                continue

            slug = cyrillic_slugify(name)
            brand, was_created = CarBrand.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "is_active": True,
                },
            )

            # Если запись уже была, но имя/активность отличаются — приведем к ожидаемому виду.
            if not was_created:
                changed = False
                if brand.name != name:
                    brand.name = name
                    changed = True
                if brand.is_active is not True:
                    brand.is_active = True
                    changed = True
                if changed:
                    brand.save(update_fields=["name", "is_active"])
                    updated += 1
            else:
                created += 1

        total = CarBrand.objects.count()
        self.stdout.write(self.style.SUCCESS("✓ Марки легковых авто заполнены"))
        self.stdout.write(self.style.SUCCESS(f"  Создано: {created}"))
        self.stdout.write(self.style.SUCCESS(f"  Обновлено: {updated}"))
        self.stdout.write(self.style.SUCCESS(f"  Всего в базе: {total}"))
