# 🗄️ Руководство по базе данных LinkAvto

## 📋 Что у нас есть

### ✅ Готовые скрипты:
- `final_test_data.py` - **ОСНОВНОЙ** скрипт для заполнения БД
- `simple_test_data.py` - упрощенная версия (есть ошибки)
- `create_hierarchical_categories.py` - только категории
- `create_products_with_hierarchy.py` - только товары

### 📚 Документация:
- `DATABASE_STRUCTURE.md` - подробная структура БД
- `README_DATABASE.md` - это руководство

## 🚀 Как использовать

### 1. Запуск основного скрипта:
```bash
python3 final_test_data.py
```

### 2. Что создается:
- **Производители**: Bosch, VAG, Toyota Motor, Hyundai Motor, Castrol, Mobil, Liqui Moly, Shell
- **Бренды авто**: Audi, BMW, Mercedes-Benz, Toyota, Volkswagen, Honda, Ford, Hyundai
- **Категории**: Двигатель, Тормозная система, Подвеска, Электрика, Система питания, Автохимия
- **Подкатегории**: ГРМ, Тормозные диски, Амортизаторы, Аккумуляторы и т.д.
- **Товары**: 11 разнообразных товаров с правильными связями

## 🏗️ Архитектура БД (кратко)

### Основные модели:
1. **`Category`** - иерархические категории (корневая → подкатегория → подподкатегория)
2. **`Product`** - товары с множественными связями
3. **`CarBrand`** - бренды автомобилей
4. **`Manufacturer`** - производители запчастей
5. **`OilAndChemistryCategory`** - категории масел и химии
6. **`OilAndChemistryBrand`** - бренды масел

### Ключевые связи:
- **Товар → Категория** (обязательно)
- **Товар → Производитель** (обязательно)
- **Товар → Бренд авто** (для запчастей)
- **Товар → Специализированная категория** (для масел, инструментов)

## 🎯 Типы товаров

### 1. **Запчасти** (`spare_part`)
- Привязываются к `car_brand`, `car_models`
- Имеют VIN-коды для совместимости
- Используют основные категории

### 2. **Автохимия** (`oil_chem`)
- Привязываются к `oil_chem_category`, `oil_chem_brand`
- Имеют поля `viscosity`, `volume`
- Используют корневую категорию "Автохимия и масла"

### 3. **Инструменты** (`tool`)
- Привязываются к `tool_category`, `tool_brand`

### 4. **Шины и диски** (`tire_wheel`)
- Привязываются к `tire_wheel_category`, `tire_wheel_brand`

## 🔧 Как добавить новые товары

### Пример 1: Запчасть для конкретного авто
```python
Product.objects.create(
    name='Ремень ГРМ BMW 320d',
    description='Оригинальный ремень ГРМ',
    price=Decimal('12000.00'),
    category=Category.objects.get(slug='timing-system'),
    car_brand=CarBrand.objects.get(name='BMW'),
    manufacturer=Manufacturer.objects.get(name='Bosch'),
    part_number='BMW-GRM-003',
    vin='WBAFR7C50DC123456',
    product_type='spare_part',
    vehicle_type='car'
)
```

### Пример 2: Масло
```python
Product.objects.create(
    name='Моторное масло Shell 5W-30 4л',
    description='Синтетическое моторное масло',
    price=Decimal('2800.00'),
    category=Category.objects.get(slug='chemistry'),
    oil_chem_category=OilAndChemistryCategory.objects.get(slug='engine-oils'),
    oil_chem_brand=OilAndChemistryBrand.objects.get(name='Shell'),
    manufacturer=Manufacturer.objects.get(name='Shell'),
    part_number='SHELL-5W30-4L',
    product_type='oil_chem',
    vehicle_type='universal',
    viscosity='5W-30',
    volume=Decimal('4.0')
)
```

## 📊 Статистика после запуска

- **Производителей**: 21
- **Брендов авто**: 9  
- **Категорий**: 48
- **Товаров**: 40

## ⚠️ Важные моменты

1. **Артикулы уникальны** - скрипт автоматически генерирует уникальные артикулы
2. **VIN-коды** - используются для определения совместимости
3. **Специализированные поля** - заполняются в зависимости от типа товара
4. **Категории иерархические** - товары привязываются к конечным категориям (листьям дерева)

## 🎉 Готово!

Теперь у вас есть:
- ✅ Понятная структура БД
- ✅ Рабочий скрипт для заполнения
- ✅ Подробная документация
- ✅ Примеры использования

Можете запускать `python3 final_test_data.py` и получать тестовые данные!
