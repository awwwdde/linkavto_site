import random
import string
from dataclasses import dataclass
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import IntegrityError, transaction
from django.utils.text import slugify

from shop.models import (
    CarBrand,
    CarGeneration,
    CarModel,
    CarModification,
    Category,
    Manufacturer,
    ManufacturerCategoryRelation,
    PartSubcategory,
    Product,
)


@dataclass(frozen=True)
class Counts:
    brands: int
    models_per_brand: int
    generations_per_model: int
    modifications_per_generation: int
    products: int
    part_subcategories_per_category: int
    manufacturers: int


def _rand_suffix(rng: random.Random, k: int = 5) -> str:
    return "".join(rng.choices(string.ascii_uppercase + string.digits, k=k))


def _unique_part_number(rng: random.Random, prefix: str = "TEST") -> str:
    # Robust enough for thousands of products; collision is extremely unlikely.
    return f"{prefix}-{rng.randint(100_000, 999_999)}-{_rand_suffix(rng, 3)}"


class Command(BaseCommand):
    help = (
        "Генерирует много тестовых данных для проверки фильтров: "
        "категории (cars), производителей, марки/модели/поколения/модификации и товары."
    )

    def add_arguments(self, parser):
        parser.add_argument("--seed", type=int, default=42, help="Seed для детерминированной генерации")
        parser.add_argument("--products", type=int, default=600, help="Сколько товаров создать")
        parser.add_argument("--brands", type=int, default=14, help="Сколько марок (CarBrand) создать/использовать")
        parser.add_argument("--models-per-brand", type=int, default=4, help="Сколько моделей на марку")
        parser.add_argument("--generations-per-model", type=int, default=3, help="Сколько поколений на модель")
        parser.add_argument(
            "--mods-per-generation", type=int, default=3, help="Сколько модификаций на поколение"
        )
        parser.add_argument(
            "--manufacturers", type=int, default=10, help="Сколько производителей (Manufacturer) создать/использовать"
        )
        parser.add_argument(
            "--part-subcategories-per-category",
            type=int,
            default=4,
            help="Сколько подкатегорий запчастей (PartSubcategory) создать на категорию",
        )
        parser.add_argument(
            "--no-create-categories",
            action="store_false",
            dest="create_categories",
            default=True,
            help="Не трогать категории (использовать существующие)",
        )
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Удалить ранее сгенерированные данные (по префиксу TEST/TEST-*) и выйти",
        )

    def handle(self, *args, **options):
        rng = random.Random(options["seed"])

        counts = Counts(
            brands=max(1, int(options["brands"])),
            models_per_brand=max(1, int(options["models_per_brand"])),
            generations_per_model=max(1, int(options["generations_per_model"])),
            modifications_per_generation=max(0, int(options["mods_per_generation"])),
            products=max(1, int(options["products"])),
            part_subcategories_per_category=max(0, int(options["part_subcategories_per_category"])),
            manufacturers=max(1, int(options["manufacturers"])),
        )

        if options["clear"]:
            self._clear()
            return

        if options["create_categories"]:
            self._ensure_categories()

        root = Category.objects.filter(show_in="cars", parent__isnull=True).order_by("order", "id").first()
        if not root:
            raise RuntimeError("Не найдена корневая категория для show_in='cars'. Запусти с --create-categories.")

        leaf_categories = list(
            Category.objects.filter(show_in="cars", is_active=True)
            .exclude(children__is_active=True)
            .order_by("id")
        )
        if not leaf_categories:
            leaf_categories = [root]

        self.stdout.write(self.style.HTTP_INFO(f"Root категория: {root.name} ({root.slug})"))
        self.stdout.write(self.style.HTTP_INFO(f"Листовых категорий для распределения товаров: {len(leaf_categories)}"))

        manufacturers = self._ensure_manufacturers(rng, counts.manufacturers)
        self._ensure_manufacturer_category_relations(rng, manufacturers, leaf_categories)
        self._ensure_part_subcategories(rng, leaf_categories, counts.part_subcategories_per_category)

        brands = self._ensure_car_brands(rng, counts.brands)
        model_map, gen_map, mod_map = self._ensure_car_hierarchy(
            rng,
            brands,
            counts.models_per_brand,
            counts.generations_per_model,
            counts.modifications_per_generation,
        )

        created = self._create_products(
            rng=rng,
            total=counts.products,
            categories=leaf_categories,
            manufacturers=manufacturers,
            brands=brands,
            model_map=model_map,
            gen_map=gen_map,
            mod_map=mod_map,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Готово!\n"
                f"- Марок (активных): {len(brands)}\n"
                f"- Товаров создано: {created}\n"
                f"Seed: {options['seed']}\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            )
        )

    def _ensure_categories(self):
        """
        Переиспользуем ваши готовые команды, чтобы не плодить новую логику по дереву категорий.
        """
        from django.core.management import call_command

        self.stdout.write(self.style.HTTP_INFO("Создаю/обновляю дерево категорий (root + sub + subsub)..."))
        call_command("create_root_categories", verbosity=0)
        call_command("create_car_truck_subcategories", verbosity=0)
        call_command("create_subsubcategories", verbosity=0)

    def _clear(self):
        """
        Удаляем только то, что легко идентифицировать по префиксу.
        НИЧЕГО “пользовательского/боевого” не трогаем.
        """
        self.stdout.write(self.style.WARNING("Очистка TEST-данных..."))

        with transaction.atomic():
            # Products first (M2M cleaned automatically)
            prod_qs = Product.objects.filter(part_number__startswith="TEST-")
            prod_cnt = prod_qs.count()
            prod_qs.delete()

            mod_cnt = CarModification.objects.filter(name__startswith="TEST ").count()
            CarModification.objects.filter(name__startswith="TEST ").delete()

            gen_cnt = CarGeneration.objects.filter(name__startswith="TEST ").count()
            CarGeneration.objects.filter(name__startswith="TEST ").delete()

            model_cnt = CarModel.objects.filter(name__startswith="TEST ").count()
            CarModel.objects.filter(name__startswith="TEST ").delete()

            brand_cnt = CarBrand.objects.filter(name__startswith="TEST ").count()
            CarBrand.objects.filter(name__startswith="TEST ").delete()

            sub_cnt = PartSubcategory.objects.filter(name__startswith="TEST ").count()
            PartSubcategory.objects.filter(name__startswith="TEST ").delete()

            mrel_cnt = ManufacturerCategoryRelation.objects.filter(manufacturer__name__startswith="TEST ").count()
            ManufacturerCategoryRelation.objects.filter(manufacturer__name__startswith="TEST ").delete()

            man_cnt = Manufacturer.objects.filter(name__startswith="TEST ").count()
            Manufacturer.objects.filter(name__startswith="TEST ").delete()

        self.stdout.write(
            self.style.SUCCESS(
                "Удалено:\n"
                f"- Products: {prod_cnt}\n"
                f"- CarModification: {mod_cnt}\n"
                f"- CarGeneration: {gen_cnt}\n"
                f"- CarModel: {model_cnt}\n"
                f"- CarBrand: {brand_cnt}\n"
                f"- PartSubcategory: {sub_cnt}\n"
                f"- ManufacturerCategoryRelation: {mrel_cnt}\n"
                f"- Manufacturer: {man_cnt}\n"
            )
        )

    def _ensure_manufacturers(self, rng: random.Random, count: int) -> list[Manufacturer]:
        base = [
            "Bosch",
            "MANN-FILTER",
            "Mahle",
            "Sachs",
            "Brembo",
            "Ferodo",
            "Gates",
            "Dayco",
            "NGK",
            "Denso",
            "Valeo",
            "Febi",
            "Lemforder",
            "TRW",
        ]
        rng.shuffle(base)

        manufacturers: list[Manufacturer] = []
        for i in range(count):
            name = base[i] if i < len(base) else f"TEST Manufacturer {i + 1}"
            slug = slugify(name)[:100] or f"test-manufacturer-{i + 1}"
            man, _ = Manufacturer.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "is_active": True,
                    "country": rng.choice(["Германия", "Япония", "Корея", "Франция", "Италия", "США", "Китай"]),
                    "year_founded": rng.randint(1900, 2015),
                },
            )
            if not man.is_active:
                man.is_active = True
                man.save(update_fields=["is_active"])
            manufacturers.append(man)
        return manufacturers

    def _ensure_manufacturer_category_relations(
        self, rng: random.Random, manufacturers: list[Manufacturer], categories: list[Category]
    ) -> None:
        # Чтобы фильтр “Производитель” был не пустой: category.manufacturers...
        for category in categories:
            # Привяжем несколько производителей к каждой категории
            for man in rng.sample(manufacturers, k=min(4, len(manufacturers))):
                ManufacturerCategoryRelation.objects.get_or_create(
                    manufacturer=man,
                    category=category,
                    defaults={"is_main": False},
                )

    def _ensure_part_subcategories(self, rng: random.Random, categories: list[Category], per_category: int) -> None:
        if per_category <= 0:
            return
        for category in categories:
            for i in range(per_category):
                name = f"TEST {category.name}: подкатегория {i + 1}"
                slug = slugify(f"{category.slug}-ps-{i + 1}")[:100] or f"{category.id}-ps-{i + 1}"
                PartSubcategory.objects.get_or_create(
                    slug=slug,
                    defaults={"name": name, "parent_category": category},
                )

    def _ensure_car_brands(self, rng: random.Random, count: int) -> list[CarBrand]:
        # Популярные марки — чтобы в админке/фильтрах выглядело естественно.
        base = [
            "Audi",
            "BMW",
            "Mercedes-Benz",
            "Volkswagen",
            "Toyota",
            "Honda",
            "Nissan",
            "Mazda",
            "Mitsubishi",
            "Kia",
            "Hyundai",
            "Renault",
            "Skoda",
            "Ford",
            "Peugeot",
            "Citroen",
            "Volvo",
            "Opel",
        ]
        rng.shuffle(base)

        brands: list[CarBrand] = []
        for i in range(count):
            name = base[i] if i < len(base) else f"TEST Brand {i + 1}"
            slug = slugify(name)[:100] or f"test-brand-{i + 1}"
            brand, _ = CarBrand.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": name,
                    "is_active": True,
                    "country": rng.choice(["Германия", "Япония", "Корея", "Франция", "Италия", "США"]),
                    "year_founded": rng.randint(1890, 2010),
                },
            )
            if not brand.is_active:
                brand.is_active = True
                brand.save(update_fields=["is_active"])
            brands.append(brand)
        return brands

    def _ensure_car_hierarchy(
        self,
        rng: random.Random,
        brands: list[CarBrand],
        models_per_brand: int,
        generations_per_model: int,
        modifications_per_generation: int,
    ) -> tuple[dict[int, list[CarModel]], dict[int, list[CarGeneration]], dict[int, list[CarModification]]]:
        """
        Возвращает:
        - model_map[brand_id] -> models
        - gen_map[model_id] -> generations
        - mod_map[generation_id] -> modifications
        """
        model_map: dict[int, list[CarModel]] = {}
        gen_map: dict[int, list[CarGeneration]] = {}
        mod_map: dict[int, list[CarModification]] = {}

        for b in brands:
            models: list[CarModel] = []
            for i in range(models_per_brand):
                name = f"TEST {b.name} Model {i + 1}"
                slug = slugify(f"{b.slug}-m{i + 1}")[:100] or f"{b.id}-m{i + 1}"
                year_start = rng.randint(1995, 2022)

                m, _ = CarModel.objects.get_or_create(
                    slug=slug,
                    defaults={
                        "name": name,
                        "brand": b,
                        "year_start": year_start,
                        "year_end": None if rng.random() < 0.5 else rng.randint(max(year_start + 1, 1996), 2025),
                        "is_active": True,
                    },
                )
                if not m.is_active:
                    m.is_active = True
                    m.save(update_fields=["is_active"])
                models.append(m)

            model_map[b.id] = models

            for m in models:
                gens: list[CarGeneration] = []
                base_year = m.year_start or rng.randint(1995, 2020)
                for j in range(generations_per_model):
                    year_start = base_year + j * rng.randint(2, 5)
                    year_end = None if rng.random() < 0.45 else year_start + rng.randint(2, 6)
                    name = f"TEST {m.name}: Gen {j + 1}"
                    slug = slugify(f"{m.slug}-g{j + 1}")[:100] or f"{m.id}-g{j + 1}"
                    g, _ = CarGeneration.objects.get_or_create(
                        slug=slug,
                        defaults={
                            "name": name,
                            "model": m,
                            "year_start": max(1900, year_start),
                            "year_end": year_end,
                            "is_active": True,
                        },
                    )
                    if not g.is_active:
                        g.is_active = True
                        g.save(update_fields=["is_active"])
                    gens.append(g)
                gen_map[m.id] = gens

                for g in gens:
                    mods: list[CarModification] = []
                    for k in range(modifications_per_generation):
                        mod_name = rng.choice(
                            [
                                "1.6 MT",
                                "2.0 AT",
                                "1.4T DSG",
                                "2.0D AT",
                                "Hybrid eCVT",
                                "EV Single Motor",
                            ]
                        )
                        name = f"TEST {mod_name} #{k + 1}"
                        mod, _ = CarModification.objects.get_or_create(
                            generation=g,
                            name=name,
                            defaults={
                                "engine_type": rng.choice(["gasoline", "diesel", "hybrid", "electric", "unknown"]),
                                "engine_volume": rng.choice(["1.4", "1.6", "1.8", "2.0", "2.5", "3.0T"]),
                                "power": rng.choice([90, 110, 150, 180, 220, 280, None]),
                                "transmission": rng.choice(["manual", "automatic", "robot", "cvt", "unknown"]),
                                "drive_type": rng.choice(["front", "rear", "awd", "unknown"]),
                                "body_type": rng.choice(["седан", "хэтчбек", "универсал", "кроссовер", "купе", ""]),
                            },
                        )
                        mods.append(mod)
                    mod_map[g.id] = mods

        return model_map, gen_map, mod_map

    def _create_products(
        self,
        *,
        rng: random.Random,
        total: int,
        categories: list[Category],
        manufacturers: list[Manufacturer],
        brands: list[CarBrand],
        model_map: dict[int, list[CarModel]],
        gen_map: dict[int, list[CarGeneration]],
        mod_map: dict[int, list[CarModification]],
    ) -> int:
        part_names = [
            "Фильтр масляный",
            "Колодки тормозные",
            "Диск тормозной",
            "Амортизатор",
            "Свеча зажигания",
            "Рычаг подвески",
            "Стойка стабилизатора",
            "Ремень ГРМ",
            "Помпа водяная",
            "Термостат",
            "Радиатор",
            "ШРУС наружный",
        ]

        created = 0
        # Делаем коммит разом, чтобы быстрее.
        with transaction.atomic():
            for i in range(total):
                brand = rng.choice(brands)
                models = model_map.get(brand.id) or []
                model = rng.choice(models) if models else None
                gens = gen_map.get(model.id) if model else []
                gen = rng.choice(gens) if gens else None
                mods = mod_map.get(gen.id) if gen else []

                category = rng.choice(categories)
                manufacturer = rng.choice(manufacturers)

                base = rng.choice(part_names)
                suffix = _rand_suffix(rng, 4)
                name = f"{base} {brand.name} {model.name if model else ''} {gen.name if gen else ''} [{suffix}]".strip()

                # Уникальный part_number (у модели поле unique=True)
                part_number = _unique_part_number(rng, prefix="TEST")
                for _ in range(20):
                    if not Product.objects.filter(part_number=part_number).exists():
                        break
                    part_number = _unique_part_number(rng, prefix="TEST")

                price = Decimal(rng.randint(250, 250_000))
                old_price = None
                if rng.random() < 0.25:
                    old_price = (price * Decimal(rng.uniform(1.1, 1.5))).quantize(Decimal("0.01"))

                try:
                    product = Product.objects.create(
                        name=name,
                        category=category,
                        manufacturer=manufacturer,
                        car_brand=brand,
                        vehicle_type="car",
                        price=price,
                        old_price=old_price,
                        stock=rng.randint(0, 60),
                        is_active=True,
                        is_featured=rng.random() < 0.15,
                        is_new=rng.random() < 0.20,
                        is_original=rng.random() < 0.25,
                        part_number=part_number,
                        short_description=base,
                        description=f"TEST товар для проверки фильтров. {base} для {brand.name}.",
                    )
                except IntegrityError:
                    # На всякий случай: если столкнулись на уникальностях (slug/part_number) — пропустим итерацию.
                    continue

                if model:
                    product.car_models.add(model)
                if gen:
                    product.car_generations.add(gen)
                if mods:
                    # Добавим 1-2 модификации
                    for mod in rng.sample(mods, k=min(rng.randint(1, 2), len(mods))):
                        product.car_modifications.add(mod)

                # Иногда привяжем подкатегорию запчастей, чтобы проверить этот фильтр.
                if rng.random() < 0.5:
                    ps = (
                        PartSubcategory.objects.filter(parent_category=category).order_by("id").first()
                    )
                    if ps:
                        product.part_subcategory = ps
                        product.save(update_fields=["part_subcategory"])

                created += 1

        return created


