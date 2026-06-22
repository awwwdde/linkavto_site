# Кодовые изменения для переноса в GitLab

Ниже собраны основные кодовые вставки, которые были добавлены или изменены.
Полный список файлов см. в `docs/vin_search_crosses_setup.md`.

## `shop/models.py`

Добавлена нормализация артикула:

```python
def normalize_article_number(value):
    if not value:
        return ''
    return ''.join(char for char in str(value).upper() if char.isalnum())
```

В `Product` добавлено служебное поле:

```python
normalized_part_number = models.CharField(
    _("Normalized part number"),
    max_length=100,
    blank=True,
    default='',
    db_index=True,
    editable=False,
    help_text=_("Service field for part-number and cross-reference search")
)
```

В `Product.save()` добавлено заполнение нормализованного артикула:

```python
def save(self, *args, **kwargs):
    is_new = self.pk is None
    should_generate_code = not self.internal_code
    self.normalized_part_number = normalize_article_number(self.part_number)

    super().save(*args, **kwargs)
```

Добавлена модель кроссов и аналогов:

```python
class ProductCrossReference(models.Model):
    RELATION_TYPES = [
        ('cross', _('Cross reference')),
        ('analog', _('Analog')),
        ('oem', _('OEM number')),
        ('replacement', _('Replacement')),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cross_references',
        verbose_name=_("Product")
    )
    article_number = models.CharField(_("Article number"), max_length=100)
    normalized_article = models.CharField(
        _("Normalized article"),
        max_length=100,
        blank=True,
        default='',
        db_index=True,
        editable=False
    )
    brand = models.CharField(_("Brand"), max_length=100, blank=True, default='')
    relation_type = models.CharField(
        _("Relation type"),
        max_length=20,
        choices=RELATION_TYPES,
        default='cross'
    )
    analog_product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        related_name='incoming_cross_references',
        null=True,
        blank=True,
        verbose_name=_("Analog product")
    )
    comment = models.CharField(_("Comment"), max_length=255, blank=True, default='')
    is_active = models.BooleanField(_("Active"), default=True)
    created_at = models.DateTimeField(_("Created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated at"), auto_now=True)

    class Meta:
        verbose_name = _("Product cross reference")
        verbose_name_plural = _("Product cross references")
        unique_together = ('product', 'normalized_article', 'brand', 'relation_type')
        indexes = [
            models.Index(fields=['normalized_article', 'is_active']),
            models.Index(fields=['product', 'relation_type']),
            models.Index(fields=['analog_product', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        self.normalized_article = normalize_article_number(self.article_number)
        super().save(*args, **kwargs)
```

## `shop/admin.py`

Добавлен импорт:

```python
from .models import ProductCrossReference
```

Добавлен inline для карточки товара:

```python
class ProductCrossReferenceInline(admin.TabularInline):
    model = ProductCrossReference
    extra = 1
    fields = (
        'article_number',
        'brand',
        'relation_type',
        'analog_product',
        'comment',
        'is_active',
    )
    readonly_fields = ('normalized_article',)
    autocomplete_fields = ('analog_product',)
```

В `ProductAdmin.search_fields` добавлены:

```python
'normalized_part_number',
'cross_references__article_number',
'cross_references__normalized_article',
```

В `ProductAdmin.inlines` добавлен:

```python
ProductCrossReferenceInline
```

Добавлена отдельная админка:

```python
@admin.register(ProductCrossReference)
class ProductCrossReferenceAdmin(admin.ModelAdmin):
    list_display = (
        'article_number',
        'brand',
        'relation_type',
        'product',
        'analog_product',
        'is_active',
    )
    list_filter = ('relation_type', 'is_active', 'brand')
    search_fields = (
        'article_number',
        'normalized_article',
        'brand',
        'product__name',
        'product__part_number',
        'analog_product__name',
        'analog_product__part_number',
    )
    autocomplete_fields = ('product', 'analog_product')
    readonly_fields = ('normalized_article', 'created_at', 'updated_at')
```

## `shop/migrations/0015_product_cross_references.py`

Добавлена миграция:

```python
from django.db import migrations, models
import django.db.models.deletion


def normalize_article_number(value):
    if not value:
        return ''
    return ''.join(char for char in str(value).upper() if char.isalnum())


def populate_normalized_part_numbers(apps, schema_editor):
    Product = apps.get_model('shop', 'Product')
    for product in Product.objects.all().only('id', 'part_number'):
        Product.objects.filter(pk=product.pk).update(
            normalized_part_number=normalize_article_number(product.part_number)
        )
```

Миграция также добавляет поле `normalized_part_number` и создает модель
`ProductCrossReference`.

## `garage/services.py`

Добавлен общий нормализатор VIN:

```python
VIN_CYRILLIC_TO_LATIN = str.maketrans({
    'А': 'A',
    'В': 'B',
    'Е': 'E',
    'К': 'K',
    'М': 'M',
    'Н': 'H',
    'О': 'O',
    'Р': 'P',
    'С': 'C',
    'Т': 'T',
    'У': 'Y',
    'Х': 'X',
})


class VINService:
    @staticmethod
    def normalize_vin(vin):
        """Normalize VIN before validation and storing."""
        if not vin:
            return ''

        vin = str(vin).upper().translate(VIN_CYRILLIC_TO_LATIN)
        return ''.join(char for char in vin if char.isalnum())
```

В `VINService.validate_vin()` VIN теперь нормализуется и возвращает
`normalized_vin`:

```python
vin = VINService.normalize_vin(vin)

if len(vin) != 17:
    return {
        'valid': False,
        'error': 'VIN номер должен содержать ровно 17 символов',
        'normalized_vin': vin,
    }

return {'valid': True, 'error': None, 'normalized_vin': vin}
```

В `VINService.decode_vin()` добавлено:

```python
vin = VINService.normalize_vin(vin)
validation = VINService.validate_vin(vin)

info = {
    'success': True,
    'valid': True,
    'vin': vin,
    'normalized_vin': vin,
    'wmi': vin[:3],
    'vds': vin[3:9],
    'vis': vin[9:],
}
```

## `garage/models.py`

В `Vehicle.clean()` добавлена серверная нормализация и защита от дублей:

```python
if self.vin:
    from .services import VINService

    vin_validation = VINService.validate_vin(self.vin)
    self.vin = vin_validation.get('normalized_vin') or VINService.normalize_vin(self.vin)
    if not vin_validation['valid']:
        raise ValidationError({'vin': vin_validation['error']})

    if self.user_id and self.is_active:
        duplicate_qs = self.__class__.objects.filter(
            user_id=self.user_id,
            vin=self.vin,
            is_active=True,
        )
        if self.pk:
            duplicate_qs = duplicate_qs.exclude(pk=self.pk)
        if duplicate_qs.exists():
            raise ValidationError({
                'vin': 'Автомобиль с таким VIN уже есть в гараже пользователя'
            })
```

В `Vehicle.save()` добавлено:

```python
def save(self, *args, **kwargs):
    if self.vin:
        from .services import VINService
        self.vin = VINService.normalize_vin(self.vin)

    self.full_clean()
    super().save(*args, **kwargs)
```

## `garage/forms.py`

Добавлен импорт:

```python
from django.core.validators import MaxLengthValidator
from .services import VINService
```

Настроено поле VIN в форме:

```python
if 'vin' in self.fields:
    self.fields['vin'].max_length = 32
    self.fields['vin'].validators = [
        validator for validator in self.fields['vin'].validators
        if not isinstance(validator, MaxLengthValidator)
    ]
    self.fields['vin'].widget.attrs.update({
        'maxlength': 32,
        'autocomplete': 'off',
        'spellcheck': 'false',
    })
```

Добавлен `clean_vin()`:

```python
def clean_vin(self):
    vin = self.cleaned_data.get('vin')
    if not vin:
        return None

    vin_validation = VINService.validate_vin(vin)
    if not vin_validation['valid']:
        raise forms.ValidationError(vin_validation['error'])

    return vin_validation['normalized_vin']
```

## `garage/views.py`

В добавлении автомобиля VIN теперь нормализуется:

```python
vin = VINService.normalize_vin(data.get('vin', ''))
```

Добавлена проверка дубля:

```python
if Vehicle.objects.filter(user=request.user, vin=vin, is_active=True).exists():
    return JsonResponse({
        'success': False,
        'error': 'Автомобиль с таким VIN уже есть в вашем гараже'
    }, status=400)
```

Добавлена автоподстановка года из VIN:

```python
year = int(data.get('year')) if data.get('year') else None
if vin and not year:
    decoded_vin = VINService.decode_vin(vin)
    year = decoded_vin.get('year') if decoded_vin.get('success') else None
```

В редактировании автомобиля:

```python
vin = VINService.normalize_vin(data['vin'])
```

И проверка дубля с исключением текущего автомобиля:

```python
if Vehicle.objects.filter(
    user=request.user,
    vin=vin,
    is_active=True
).exclude(pk=vehicle.pk).exists():
    return JsonResponse({
        'success': False,
        'error': 'Автомобиль с таким VIN уже есть в вашем гараже'
    }, status=400)
```

## `garage/templates/garage/add.html`

Поле VIN изменено:

```html
<input type="text" name="vin" id="id_vin" class="form-control rounded-3"
       placeholder="17 символов" maxlength="32" autocomplete="off"
       autocapitalize="characters" spellcheck="false">
<div id="vin-feedback" class="form-text"></div>
```

Добавлен JS-нормализатор:

```javascript
var vinCyrillicMap = {
    'А': 'A',
    'В': 'B',
    'Е': 'E',
    'К': 'K',
    'М': 'M',
    'Н': 'H',
    'О': 'O',
    'Р': 'P',
    'С': 'C',
    'Т': 'T',
    'У': 'Y',
    'Х': 'X'
};

function normalizeVin(value) {
    return (value || '')
        .toUpperCase()
        .split('')
        .map(function(char) { return vinCyrillicMap[char] || char; })
        .join('')
        .replace(/[^A-Z0-9]/g, '');
}
```

Перед отправкой формы добавлена проверка:

```javascript
if (vinEl && vinEl.value) {
    vinEl.value = normalizeVin(vinEl.value);
    if (vinEl.value.length !== 17) {
        setVinFeedback('VIN должен содержать 17 символов.', 'error');
        vinEl.focus();
        return;
    }
}
```

## `sellers/views.py`

Добавлен импорт и helper:

```python
from garage.services import VINService


def _get_validated_product_vin(data):
    vin = VINService.normalize_vin(data.get('vin_number', ''))
    if not vin:
        return None, None

    vin_validation = VINService.validate_vin(vin)
    if not vin_validation['valid']:
        return None, vin_validation['error']

    return vin_validation.get('normalized_vin') or vin, None
```

В `product_add()` перед созданием товара:

```python
vin_number, vin_error = _get_validated_product_vin(request.POST)
if vin_error:
    return JsonResponse({'success': False, 'error': vin_error})
```

В создании `Product`:

```python
vin=vin_number,
```

В `product_edit()`:

```python
vin_number, vin_error = _get_validated_product_vin(request.POST)
if vin_error:
    return JsonResponse({'success': False, 'error': vin_error})

product.vin = vin_number
```

В `get_vin_info()` заменена небезопасная работа с декодером:

```python
vin = VINService.normalize_vin(request.GET.get('vin', ''))
vin_validation = VINService.validate_vin(vin) if vin else {
    'valid': False,
    'error': 'VIN обязателен',
    'normalized_vin': vin,
}

if not vin_validation['valid']:
    return JsonResponse({
        'success': False,
        'error': vin_validation['error'],
        'normalized_vin': vin_validation.get('normalized_vin') or vin,
    })

try:
    from vehicles.vin_decoder import VINDecoder
    decoded = VINDecoder.decode(vin)
except Exception:
    decoded = None

if not decoded:
    return _get_vin_info_old(request, vin)
```

## `sellers/templates/sellers/add_product.html`

Поле VIN изменено:

```html
<input type="text" class="form-control" id="vinInput" name="vin_number"
       placeholder="Введите VIN номер" maxlength="32" autocomplete="off"
       autocapitalize="characters" spellcheck="false"
       value="{% if product %}{{ product.vin|default:'' }}{% endif %}">
```

Добавлен JS:

```javascript
let vinTimeout;
const vinInput = document.getElementById('vinInput');
const vinInfo = document.getElementById('vinInfo');
const vinCyrillicMap = {
    'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H',
    'О': 'O', 'Р': 'P', 'С': 'C', 'Т': 'T', 'У': 'Y', 'Х': 'X'
};

function normalizeVin(value) {
    return (value || '')
        .toUpperCase()
        .split('')
        .map(char => vinCyrillicMap[char] || char)
        .join('')
        .replace(/[^A-Z0-9]/g, '');
}

function prepareProductVinForSubmit() {
    if (!vinInput || !vinInput.value) return true;

    vinInput.value = normalizeVin(vinInput.value);
    if (vinInput.value.length !== 17) {
        setVinInfo('<span class="text-danger">VIN должен содержать ровно 17 символов.</span>');
        vinInput.focus();
        return false;
    }

    return true;
}

if (vinInput) {
    vinInput.addEventListener('input', checkVinInfo);
    vinInput.addEventListener('blur', checkVinInfo);
}
```

В отправку формы добавлена проверка:

```javascript
if (!prepareProductVinForSubmit()) {
    showError('Пожалуйста, проверьте VIN номер');
    return;
}
```

## `search/services.py`

Добавлены основные функции и методы:

```python
LICENSE_PLATE_TRANSLATION = str.maketrans({
    'А': 'A',
    'В': 'B',
    'Е': 'E',
    'К': 'K',
    'М': 'M',
    'Н': 'H',
    'О': 'O',
    'Р': 'P',
    'С': 'C',
    'Т': 'T',
    'У': 'Y',
    'Х': 'X',
})


def normalize_vehicle_identifier(value):
    if not value:
        return ''
    value = str(value).upper().translate(LICENSE_PLATE_TRANSLATION)
    return ''.join(char for char in value if char.isalnum())
```

Типы поиска:

```python
@staticmethod
def detect_search_type(query):
    normalized_identifier = normalize_vehicle_identifier(query)
    normalized_article = normalize_article_number(query)

    if VIN_PATTERN.match(normalized_identifier):
        return 'vin'
    if LICENSE_PLATE_PATTERN.match(normalized_identifier):
        return 'license_plate'
    if normalized_article and any(char.isdigit() for char in normalized_article):
        return 'part_number'
    return 'text'
```

Поиск принимает пользователя:

```python
def search_products(self, query, filters=None):
    filters = filters or {}
    user = filters.pop('user', None)
```

И собирает результаты по релевантности:

```python
ordered_ids.extend(self._exact_product_ids(query, normalized_article))
ordered_ids.extend(self._cross_and_analog_product_ids(normalized_article))
ordered_ids.extend(self._vehicle_product_ids(search_type, normalized_identifier, user))
```

## `search/fuzzy_search.py`

В нечеткий поиск добавлены кроссы:

```python
from shop.models import Product, ProductCrossReference, normalize_article_number
```

Подсказки по кроссам:

```python
for cross in ProductCrossReference.objects.filter(
    normalized_article__icontains=normalized_query,
    is_active=True,
).select_related('product')[:limit]:
    suggestions.append({
        'type': 'cross_reference',
        'value': cross.article_number,
        'display': f'{cross.brand} {cross.article_number}'.strip(),
        'slug': cross.product.slug,
    })
```

## `search/templates/search/autocomplete.html`

Подсказки теперь используют чистое значение:

```html
<div class="autocomplete-item"
     data-type="{{ suggestion.type }}"
     data-value="{{ suggestion.value }}"
     data-slug="{{ suggestion.slug|default:'' }}">
```

Добавлен тип `cross_reference`.

## `shop/views.py` и `search/views.py`

В поиск теперь передается пользователь:

```python
service_filters['user'] = request.user
products = search_service.search_products(query, service_filters)
```

В контекст добавлено:

```python
'search_type': search_type,
'is_plate_search': search_type == 'license_plate',
```

## `shop/templates/shop/search.html`

Добавлен заголовок для поиска по госномеру:

```django
{% elif is_plate_search %}
    Поиск по госномеру: "{{ query }}"
```

Автоподсказки теперь берут `data-value`:

```javascript
let searchValue = this.dataset.value || this.textContent;
```

## `shop/management/commands/import_cross_references.py`

Добавлена команда:

```python
class Command(BaseCommand):
    help = 'Import product cross references from CSV or Excel file'

    def add_arguments(self, parser):
        parser.add_argument('file_path')
        parser.add_argument('--dry-run', action='store_true')
```

Основная логика:

```python
product = Product.objects.filter(
    normalized_part_number=normalize_article_number(product_article)
).first()

ProductCrossReference.objects.update_or_create(
    product=product,
    normalized_article=normalize_article_number(cross_article),
    brand=brand,
    relation_type=relation_type,
    defaults={
        'article_number': cross_article,
        'analog_product': analog_product,
        'comment': comment,
        'is_active': True,
    }
)
```

Запуск:

```bash
python manage.py import_cross_references crosses.csv
python manage.py import_cross_references crosses.csv --dry-run
```

## Документация

Добавлен файл:

```text
docs/vin_search_crosses_setup.md
```
