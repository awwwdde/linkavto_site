"""
Команда для заполнения базы данных моделями легковых автомобилей.

Подход:
- Берем существующие CarBrand (по умолчанию is_active=True)
- Для каждой марки запрашиваем список моделей из NHTSA vPIC API
- Создаем недостающие CarModel (slug генерируется автоматически в BaseSlugModel.save)

Важно:
- vPIC содержит "глобальный" справочник, но наиболее полно покрывает рынок США.
- Названия марок иногда отличаются (например, "Mercedes-Benz" vs "Mercedes Benz"),
  поэтому пробуем несколько вариантов запроса.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Iterable, Optional
from urllib.error import URLError

from django.core.management.base import BaseCommand

from shop.models import CarBrand, CarModel


@dataclass(frozen=True)
class VpicModelRow:
    make_name: str
    model_name: str


def _fetch_json(url: str, timeout: int = 20, retries: int = 0, backoff_s: float = 0.5) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            # vPIC иногда строг к отсутствию UA
            "User-Agent": "linkavto/1.0 (fill_car_models)",
            "Accept": "application/json",
        },
    )
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec - URL is fixed host
                raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw)
        except (TimeoutError, URLError, OSError, json.JSONDecodeError) as e:
            last_err = e
            if attempt >= retries:
                break
            time.sleep(backoff_s * (attempt + 1))
    raise last_err  # type: ignore[misc]


def _normalize_key(value: str) -> str:
    # Нормализация для сопоставления названий (убираем все кроме букв/цифр)
    return "".join(ch for ch in (value or "").upper() if ch.isalnum())


def _vpic_all_makes(timeout: int = 20, retries: int = 0) -> list[dict]:
    # https://vpic.nhtsa.dot.gov/api/vehicles/getallmakes?format=json
    url = "https://vpic.nhtsa.dot.gov/api/vehicles/GetAllMakes?format=json"
    data = _fetch_json(url, timeout=timeout, retries=retries)
    return data.get("Results") or []


def _vpic_makes_for_vehicle_type(vehicle_type: str, timeout: int = 20, retries: int = 0) -> list[dict]:
    # Более легкий эндпоинт, чем GetAllMakes
    # https://vpic.nhtsa.dot.gov/api/vehicles/GetMakesForVehicleType/car?format=json
    vt = urllib.parse.quote(vehicle_type)
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetMakesForVehicleType/{vt}?format=json"
    data = _fetch_json(url, timeout=timeout, retries=retries)
    return data.get("Results") or []


def _vpic_models_for_make(make: str, timeout: int = 20, retries: int = 0) -> list[VpicModelRow]:
    make_q = urllib.parse.quote(make)
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMake/{make_q}?format=json"
    data = _fetch_json(url, timeout=timeout, retries=retries)

    results = data.get("Results") or []
    out: list[VpicModelRow] = []
    for row in results:
        make_name = (row.get("Make_Name") or "").strip()
        model_name = (row.get("Model_Name") or "").strip()
        if not model_name:
            continue
        out.append(VpicModelRow(make_name=make_name, model_name=model_name))
    return out


def _vpic_models_for_make_id(make_id: int, timeout: int = 20, retries: int = 0) -> list[VpicModelRow]:
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/GetModelsForMakeId/{make_id}?format=json"
    data = _fetch_json(url, timeout=timeout, retries=retries)

    results = data.get("Results") or []
    out: list[VpicModelRow] = []
    for row in results:
        make_name = (row.get("Make_Name") or "").strip()
        model_name = (row.get("Model_Name") or "").strip()
        if not model_name:
            continue
        out.append(VpicModelRow(make_name=make_name, model_name=model_name))
    return out


def _make_query_candidates(brand_name: str) -> list[str]:
    name = (brand_name or "").strip()
    if not name:
        return []

    candidates = [
        name,
        name.upper(),
        name.replace("-", " "),
        name.replace("-", " ").upper(),
        name.replace("&", "and"),
        name.replace("-", " ").replace("&", "and"),
        name.replace("-", " ").replace("&", "and").upper(),
    ]

    # Частые варианты из vPIC
    if name.lower() == "mercedes-benz":
        candidates.insert(0, "Mercedes Benz")
    if name.lower() == "rolls-royce":
        candidates.insert(0, "Rolls Royce")
    if name.lower() == "great wall":
        candidates.insert(0, "GREAT WALL")

    # Уберем дубликаты, сохранив порядок
    seen: set[str] = set()
    uniq: list[str] = []
    for c in candidates:
        c = " ".join(c.split())
        if c and c not in seen:
            uniq.append(c)
            seen.add(c)
    return uniq


class Command(BaseCommand):
    help = "Заполняет базу данных моделями легковых авто (CarModel) через vPIC"

    def add_arguments(self, parser):
        parser.add_argument(
            "--brands",
            default="",
            help="Список брендов через запятую (slug или name). Если пусто — все активные.",
        )
        parser.add_argument(
            "--max-models-per-brand",
            type=int,
            default=0,
            help="Ограничить кол-во моделей на бренд (0 = без ограничений). Полезно для теста.",
        )
        parser.add_argument(
            "--sleep",
            type=float,
            default=0.2,
            help="Пауза между запросами к API (сек).",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=20,
            help="Таймаут HTTP-запроса (сек).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Ничего не записывать в БД, только показать статистику.",
        )
        parser.add_argument(
            "--only-missing",
            action="store_true",
            help="Обрабатывать только бренды, у которых сейчас 0 моделей.",
        )
        parser.add_argument(
            "--retries",
            type=int,
            default=2,
            help="Сколько раз повторять сетевые запросы при ошибках/таймаутах.",
        )
        parser.add_argument(
            "--use-all-makes",
            action="store_true",
            help="Если не удалось сопоставить марку через Passenger Car индекс, лениво подтянуть тяжелый GetAllMakes.",
        )

    def _build_make_index(self, timeout_s: int, retries: int) -> dict[str, list[tuple[int, str]]]:
        """
        Индекс всех марок из vPIC:
        normalized_key -> [(Make_ID, Make_Name), ...]
        """
        # Берем только марки для Passenger Car — это сильно быстрее/меньше чем GetAllMakes
        # В ответе поля называются MakeId / MakeName.
        makes = _vpic_makes_for_vehicle_type("car", timeout=timeout_s, retries=retries)
        if not makes:
            makes = _vpic_makes_for_vehicle_type("passenger car", timeout=timeout_s, retries=retries)
        idx: dict[str, list[tuple[int, str]]] = {}
        for row in makes:
            make_id = row.get("MakeId") or row.get("Make_ID")
            make_name = (row.get("MakeName") or row.get("Make_Name") or "").strip()
            if not make_id or not make_name:
                continue
            key = _normalize_key(make_name)
            if not key:
                continue
            idx.setdefault(key, []).append((int(make_id), make_name))
        return idx

    def _match_make_id(
        self, brand_name: str, make_index: dict[str, list[tuple[int, str]]]
    ) -> Optional[int]:
        """
        Пытаемся сопоставить наш бренд с маркой vPIC и вернуть Make_ID.
        Сначала точное совпадение по нормализованному ключу, затем "contains" эвристика.
        """
        candidates = _make_query_candidates(brand_name)
        cand_keys = [_normalize_key(c) for c in candidates if _normalize_key(c)]

        # 1) exact
        for key in cand_keys:
            if key in make_index:
                # если несколько — берем первый (обычно это одно значение)
                return make_index[key][0][0]

        # 2) heuristic contains (чтобы поймать, например, "DS" -> "DS AUTOMOBILES")
        best: tuple[int, int] | None = None  # (score, make_id)
        for cand_key in cand_keys:
            for make_key, pairs in make_index.items():
                if not make_key:
                    continue
                if cand_key in make_key or make_key in cand_key:
                    # score: чем ближе длины — тем лучше
                    score = abs(len(make_key) - len(cand_key))
                    make_id = pairs[0][0]
                    if best is None or score < best[0]:
                        best = (score, make_id)
        return best[1] if best else None

    def handle(self, *args, **options):
        from django.db.models import Q

        raw_brands: str = options["brands"]
        max_per_brand: int = int(options["max_models_per_brand"] or 0)
        sleep_s: float = float(options["sleep"] or 0)
        timeout_s: int = int(options["timeout"] or 20)
        dry_run: bool = bool(options["dry_run"])
        only_missing: bool = bool(options["only_missing"])
        retries: int = int(options["retries"] or 0)
        use_all_makes: bool = bool(options["use_all_makes"])

        if raw_brands.strip():
            tokens = [t.strip() for t in raw_brands.split(",") if t.strip()]
            q = Q()
            for t in tokens:
                q |= Q(slug=t) | Q(name=t)
            brands = CarBrand.objects.filter(is_active=True).filter(q).order_by("name")
        else:
            brands = CarBrand.objects.filter(is_active=True).order_by("name")

        if only_missing:
            brands = brands.filter(car_models__isnull=True)

        total_created = 0
        total_skipped_existing = 0
        total_failed_brands = 0
        total_brands = brands.count()

        self.stdout.write(f"Найдено брендов: {total_brands}")
        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: изменения в БД не будут сохранены"))

        self.stdout.write("Загружаю справочник марок vPIC (Passenger Car)...")
        try:
            make_index = self._build_make_index(timeout_s=timeout_s, retries=retries)
            self.stdout.write(
                self.style.SUCCESS(f"✓ Загружено марок vPIC: {sum(len(v) for v in make_index.values())}")
            )
        except Exception as e:  # noqa: BLE001
            make_index = {}
            self.stdout.write(self.style.WARNING(f"! Не удалось загрузить индекс марок vPIC: {e}"))
            self.stdout.write(self.style.WARNING("  Продолжаю без fallback по Make_ID (только запросы по имени)"))

        all_makes_index: dict[str, list[tuple[int, str]]] | None = None

        for idx, brand in enumerate(brands, start=1):
            self.stdout.write(f"[{idx}/{total_brands}] {brand.name} ({brand.slug})")

            existing_names = set(
                CarModel.objects.filter(brand=brand).values_list("name", flat=True)
            )

            models: list[VpicModelRow] = []
            last_err: Exception | None = None

            # 1) Пробуем по имени марки
            for candidate in _make_query_candidates(brand.name):
                try:
                    models = _vpic_models_for_make(candidate, timeout=timeout_s, retries=retries)
                except Exception as e:  # noqa: BLE001 - show per-brand errors, continue
                    last_err = e
                    models = []
                if models:
                    break

            # 2) Fallback: пытаемся найти Make_ID и запросить по нему
            if not models:
                make_id = self._match_make_id(brand.name, make_index) if make_index else None
                if make_id is not None:
                    try:
                        models = _vpic_models_for_make_id(make_id, timeout=timeout_s, retries=retries)
                        last_err = None
                    except Exception as e:  # noqa: BLE001
                        last_err = e
                        models = []

            # 3) Последний шанс: тяжелый индекс GetAllMakes (лениво, один раз)
            if not models and use_all_makes:
                try:
                    if all_makes_index is None:
                        self.stdout.write("  ... подгружаю GetAllMakes (это может быть долго)")
                        makes = _vpic_all_makes(timeout=timeout_s * 6, retries=retries)
                        idx_all: dict[str, list[tuple[int, str]]] = {}
                        for row in makes:
                            make_id = row.get("Make_ID")
                            make_name = (row.get("Make_Name") or "").strip()
                            if not make_id or not make_name:
                                continue
                            key = _normalize_key(make_name)
                            if not key:
                                continue
                            idx_all.setdefault(key, []).append((int(make_id), make_name))
                        all_makes_index = idx_all

                    make_id = self._match_make_id(brand.name, all_makes_index or {})
                    if make_id is not None:
                        models = _vpic_models_for_make_id(make_id, timeout=timeout_s, retries=retries)
                        last_err = None
                except Exception as e:  # noqa: BLE001
                    last_err = e
                    models = []

            if not models:
                total_failed_brands += 1
                msg = f"  ! Не удалось получить модели из vPIC"
                if last_err:
                    msg += f": {last_err}"
                self.stdout.write(self.style.WARNING(msg))
                if sleep_s:
                    time.sleep(sleep_s)
                continue

            created = 0
            skipped = 0

            # Уникализируем модели внутри бренда (на случай дублей от API)
            seen_model_names: set[str] = set()
            for row in models:
                model_name = row.model_name.strip()
                if not model_name:
                    continue
                if model_name in seen_model_names:
                    continue
                seen_model_names.add(model_name)

                if model_name in existing_names:
                    skipped += 1
                    continue

                if max_per_brand and created >= max_per_brand:
                    break

                if not dry_run:
                    obj = CarModel(brand=brand, name=model_name, is_active=True)
                    obj.save()
                created += 1
                existing_names.add(model_name)

            total_created += created
            total_skipped_existing += skipped

            self.stdout.write(self.style.SUCCESS(f"  ✓ Добавлено моделей: {created}, уже было: {skipped}"))

            if sleep_s:
                time.sleep(sleep_s)

        self.stdout.write(self.style.SUCCESS("\n✓ Готово"))
        self.stdout.write(self.style.SUCCESS(f"  Добавлено моделей всего: {total_created}"))
        self.stdout.write(self.style.SUCCESS(f"  Пропущено (уже в базе): {total_skipped_existing}"))
        self.stdout.write(self.style.SUCCESS(f"  Брендов без данных vPIC: {total_failed_brands}"))
