from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg
from django.utils import timezone
from django.conf import settings
from django.utils.crypto import get_random_string
from .utils import cyrillic_slugify
from django import forms

User = get_user_model()


def normalize_article_number(value):
    """Normalize vendor part numbers for exact cross-reference matching."""
    if not value:
        return ''
    return ''.join(char for char in str(value).upper() if char.isalnum())


class BaseSlugModel(models.Model):
    """Абстрактная модель с автоматическим созданием slug"""
    name = models.CharField(_("Название"), max_length=100)
    slug = models.SlugField(_("URL"), max_length=100, unique=True, blank=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = cyrillic_slugify(self.name)
            # Проверка уникальности slug
            model = self.__class__
            counter = 1
            while model.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{cyrillic_slugify(self.name)}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(BaseSlugModel):
    """
    Модель категорий товаров с иерархической структурой.
    Поддерживает различные типы транспорта и специальные категории.
    """
    SHOW_IN_CHOICES = [
        ('cars', _('Легковые автомобили')),
        ('trucks', _('Грузовики')),
        ('moto', _('Мототехника')),
        ('special', _('Спецтехника')),
        ('accessories', _('Аксессуары')),
        ('chemistry', _('Автохимия и масла')),
        ('tools', _('Инструменты')),
        ('tires', _('Шины и диски')),
        ('electrics', _('Автоэлектрика')),
        ('dlya-to', _('Для ТО')),
    ]

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Родительская категория"),
        related_name='children'
    )
    show_in = models.CharField(
        _("Отображать в разделе"),
        max_length=20,
        choices=SHOW_IN_CHOICES,
        default='cars'
    )
    icon = models.CharField(
        _("Иконка"),
        max_length=50,
        blank=True,
        help_text=_("Название иконки из Bootstrap Icons")
    )
    image = models.ImageField(
        _("Изображение"),
        upload_to='categories/',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(_("Активна"), default=True)
    description = models.TextField(_("Описание"), blank=True)
    order = models.PositiveIntegerField(_("Порядок сортировки"), default=0)
    slug = models.SlugField(max_length=100, unique=True, db_index=True)  # Оставляем unique=True
    show_brands = models.BooleanField(_("Показывать бренды"), default=False)

    class Meta:
        verbose_name = _("Категория")
        verbose_name_plural = _("Категории")
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['show_in']),
            models.Index(fields=['is_active']),
            models.Index(fields=['slug', 'parent']),  # Индекс для быстрого поиска по slug+parent
        ]

    def clean(self):
        # Защита от циклической вложенности
        if self.parent and self.parent.id == self.id:
            raise ValidationError(_("Категория не может быть родителем самой себя"))

        if self.parent and self.parent.parent and self.parent.parent.id == self.id:
            raise ValidationError(_("Обнаружена циклическая зависимость в иерархии категорий"))

        # Проверка уникальности slug в контексте parent (для валидации)
        # Но slug все равно должен быть уникальным глобально для работы с URL
        if self.slug:
            if self.parent is None:
                # Для корневых категорий slug должен быть уникальным глобально
                existing = Category.objects.filter(slug=self.slug, parent__isnull=True).exclude(pk=self.pk).first()
                if existing:
                    raise ValidationError(
                        {'slug': _(
                            'Категория с таким slug уже существует (корневая категория должна иметь уникальный slug)')}
                    )
            else:
                # Для подкатегорий проверяем, нет ли конфликта в том же parent
                existing_same_parent = Category.objects.filter(slug=self.slug, parent=self.parent).exclude(
                    pk=self.pk).first()
                if existing_same_parent:
                    raise ValidationError(
                        {'slug': _('Категория с таким slug уже существует в этой родительской категории')}
                    )

    def get_full_path(self):
        """
        Возвращает полный путь категории в виде списка категорий от корня до текущей.
        Полезно для хлебных крошек или отладки.
        """
        path = []
        current = self
        while current:
            path.insert(0, current)
            current = current.parent
        return path

    def save(self, *args, **kwargs):
        """
        Переопределяем save для создания коротких slug'ов.
        Slug уникален только в контексте parent - одинаковые названия в разных родителях допустимы.
        """
        # Проверяем, нужно ли перегенерировать slug
        regenerate_slug = False

        if self.pk:
            # При обновлении существующей категории
            try:
                old_instance = Category.objects.get(pk=self.pk)
                # Если изменился parent или название, нужно перегенерировать slug
                if old_instance.parent != self.parent or old_instance.name != self.name:
                    regenerate_slug = True
            except Category.DoesNotExist:
                # Если объект не найден (что не должно происходить), создаем новый slug
                regenerate_slug = not self.slug
        else:
            # При создании новой категории
            regenerate_slug = not self.slug

        if regenerate_slug:
            # Всегда используем только slug названия категории (короткий)
            base_slug = cyrillic_slugify(self.name)
            self.slug = base_slug

            # Проверяем уникальность глобально (так как slug должен быть unique=True)
            # НО: если slug занят категорией из другого parent - это нормально, добавляем суффикс
            # Если slug занят категорией из того же parent - это ошибка (но будет обработано в clean())
            counter = 1
            while Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                # Проверяем - занят ли slug категорией из того же parent (это конфликт)
                existing = Category.objects.filter(slug=self.slug).exclude(pk=self.pk).first()
                if existing and existing.parent == self.parent:
                    # Если из того же parent - это будет обработано в clean() как ошибка
                    # Но здесь просто добавляем суффикс чтобы избежать ошибки unique constraint
                    self.slug = f"{base_slug}-{counter}"
                elif existing and existing.parent != self.parent:
                    # Если из другого parent - это нормально, но slug должен быть уникальным глобально
                    # Добавляем короткий суффикс для уникальности
                    self.slug = f"{base_slug}-{counter}"
                else:
                    self.slug = f"{base_slug}-{counter}"
                counter += 1

                # Защита от бесконечного цикла
                if counter > 1000:
                    raise ValidationError(_('Не удалось создать уникальный slug'))

        # Если slug задан вручную, убедимся что он уникален глобально
        elif self.slug and self.pk:
            existing = Category.objects.filter(slug=self.slug).exclude(pk=self.pk).first()
            if existing:
                # Если такой slug уже существует, добавляем счетчик
                counter = 1
                base_slug = self.slug
                while Category.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                    self.slug = f"{base_slug}-{counter}"
                    counter += 1

        super(BaseSlugModel, self).save(*args, **kwargs)

    # ----------- Списки брендов для разных типов техники -----------

    def car_brands_list(self):
        """Бренды легковых авто, связанные через CarBrandCategoryRelation"""
        from .models import CarBrand
        return CarBrand.objects.filter(
            is_active=True,
            category_relations__category=self,
            category_relations__is_active=True
        ).distinct()

    def truck_brands_list(self):
        from .models import TruckBrand
        return TruckBrand.objects.filter(
            is_active=True,
            category_relations__category=self,
            category_relations__is_active=True
        ).distinct()

    def moto_brands_list(self):
        from .models import MotoBrand
        return MotoBrand.objects.filter(
            is_active=True,
            category_relations__category=self,
            category_relations__is_active=True
        ).distinct()

    def special_brands_list(self):
        from .models import SpecialBrand
        return SpecialBrand.objects.filter(
            is_active=True,
            category_relations__category=self,
            category_relations__is_active=True
        ).distinct()

    @property
    def brand_list(self):
        return getattr(self, 'brand_list', [])

    # ----------- Аксессуары -----------

    def main_accessory_categories(self):
        """Возвращает только активные родительские аксессуары"""
        return self.accessorycategory_set.filter(parent=None, is_active=True)

    @property
    def brand_list(self):
        """Возвращает список брендов из временного атрибута или вычисляет заново"""
        if hasattr(self, 'brand_list'):
            return self.brand_list

        if not self.show_brands:
            return []

        if self.show_in == 'cars':
            return self.car_brands_list()
        elif self.show_in == 'trucks':
            return self.truck_brands_list()
        elif self.show_in == 'moto':
            return self.moto_brands_list()
        elif self.show_in == 'special':
            return self.special_brands_list()
        return []

    def get_ancestors(self, include_self=False):
        """
        Возвращает список всех родительских категорий (от корня до текущей).

        Args:
            include_self (bool): Включать ли текущую категорию в результат

        Returns:
            list: Список категорий от корневой до текущей
        """
        ancestors = []
        current = self

        while current:
            ancestors.append(current)
            current = current.parent

        # Развернем список чтобы получить путь от корня к текущей
        ancestors.reverse()

        # Убираем текущую категорию если не нужно включать
        if not include_self and ancestors:
            ancestors.pop()

        return ancestors


class CategoryRequest(models.Model):
    """Заявка продавца на добавление новой категории/подкатегории."""

    STATUS_CHOICES = [
        ('pending', 'На проверке'),
        ('approved', 'Одобрена'),
        ('rejected', 'Отклонена'),
    ]

    seller = models.ForeignKey(
        'sellers.Seller',
        on_delete=models.CASCADE,
        related_name='category_requests',
        verbose_name='Продавец',
    )
    parent_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_requests',
        verbose_name='Родительская категория',
        help_text='Укажите, в какую категорию должна войти новая подкатегория',
    )
    name = models.CharField('Название категории', max_length=255)
    description = models.TextField('Описание / обоснование', blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='pending')
    moderator_comment = models.TextField('Комментарий модератора', blank=True)
    created_category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_from_request',
        verbose_name='Созданная категория',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_category_requests',
        verbose_name='Проверил',
    )

    class Meta:
        verbose_name = 'Заявка на категорию'
        verbose_name_plural = 'Заявки на категории'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.name} ({self.get_status_display()}) — {self.seller}'


class CategoryHierarchyModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # Получаем полный путь категории
        path = []
        current = obj
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' → '.join(path) if path else obj.name


class CategoryHierarchySelect2Widget(forms.Select):
    class Media:
        css = {'all': ('admin/css/vendor/select2/select2.min.css', 'admin/css/autocomplete.css', 'admin/css/category_select2.css')}
        js = ('admin/js/vendor/select2/select2.full.min.js', 'admin/js/category_select2_init.js')

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs']['class'] = 'category-hierarchy-select2'
        super().__init__(*args, **kwargs)


class CategoryHierarchySelect2Field(forms.ModelChoiceField):
    """ModelChoiceField с иерархическим отображением категорий и поиском через select2."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', CategoryHierarchySelect2Widget())
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        path = []
        current = obj
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' → '.join(path) if path else obj.name


class CategoryHierarchyMultipleSelect2Widget(forms.SelectMultiple):
    class Media:
        css = {'all': ('admin/css/vendor/select2/select2.min.css', 'admin/css/autocomplete.css', 'admin/css/category_select2.css')}
        js = ('admin/js/vendor/select2/select2.full.min.js', 'admin/js/category_select2_init.js')

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs']['class'] = 'category-hierarchy-select2-multiple'
        super().__init__(*args, **kwargs)


class CategoryHierarchyMultipleSelect2Field(forms.ModelMultipleChoiceField):
    """ModelMultipleChoiceField с иерархическим отображением категорий и поиском через select2."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', CategoryHierarchyMultipleSelect2Widget())
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        path = []
        current = obj
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' → '.join(path) if path else obj.name


class ParentCategoryHierarchySelect2Widget(forms.Select):
    class Media:
        css = {'all': ('admin/css/vendor/select2/select2.min.css', 'admin/css/autocomplete.css', 'admin/css/category_select2.css')}
        js = ('admin/js/vendor/select2/select2.full.min.js', 'admin/js/category_select2_init.js')

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('attrs', {})
        kwargs['attrs']['class'] = 'parent-category-select2'
        super().__init__(*args, **kwargs)


class ParentCategoryHierarchyModelChoiceField(forms.ModelChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', ParentCategoryHierarchySelect2Widget())
        super().__init__(*args, **kwargs)

    def label_from_instance(self, obj):
        path = []
        current = obj
        while current:
            path.insert(0, current.name)
            current = current.parent
        return ' → '.join(path) if path else obj.name


class Manufacturer(BaseSlugModel):
    """
    Производители запчастей и аксессуаров (Bosch, Brembo и т.д.)
    """
    country = models.CharField(_("Страна"), max_length=50, blank=True)
    logo = models.ImageField(_("Логотип"), upload_to='manufacturers/', blank=True)
    description = models.TextField(_("Описание"), blank=True)
    year_founded = models.PositiveIntegerField(
        _("Год основания"),
        null=True,
        blank=True
    )
    is_active = models.BooleanField(_("Активен"), default=True)
    categories = models.ManyToManyField(
        Category,
        through='ManufacturerCategoryRelation',
        verbose_name=_("Категории"),
        blank=True,
        related_name='manufacturers'
    )

    class Meta:
        verbose_name = _("Производитель")
        verbose_name_plural = _("Производители")
        ordering = ['name']


class ManufacturerCategoryRelation(models.Model):
    """
    Связь производителей с категориями товаров
    """
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    is_main = models.BooleanField(_("Основная категория"), default=False)

    class Meta:
        unique_together = ('manufacturer', 'category')
        verbose_name = _("Связь производителя с категорией")
        verbose_name_plural = _("Связи производителей с категориями")

    def __str__(self):
        return f"{self.manufacturer.name} - {self.category.name}"


class VehicleType(models.Model):
    """
    Базовый тип транспортного средства (легковые, грузовики и т.д.)
    """
    name = models.CharField(_("Название"), max_length=50)
    slug = models.SlugField(_("URL"), unique=True)
    icon = models.CharField(_("Иконка"), max_length=50, blank=True)
    is_active = models.BooleanField(_("Активен"), default=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class CarType(VehicleType):
    """Типы легковых автомобилей (седан, хэтчбек и т.д.)"""

    class Meta:
        verbose_name = _("Тип легкового автомобиля")
        verbose_name_plural = _("Типы легковых автомобилей")


class TruckType(VehicleType):
    """Типы грузовой техники (грузовики, автобусы и т.д.)"""

    class Meta:
        verbose_name = _("Тип грузовой техники")
        verbose_name_plural = _("Типы грузовой техники")


class MotoType(VehicleType):
    """Типы мототехники (мотоциклы, скутеры и т.д.)"""

    class Meta:
        verbose_name = _("Тип мототехники")
        verbose_name_plural = _("Типы мототехники")


class SpecialType(VehicleType):
    """Типы спецтехники (экскаваторы, бульдозеры и т.д.)"""

    class Meta:
        verbose_name = _("Тип спецтехники")
        verbose_name_plural = _("Типы спецтехники")


class VehicleBrand(BaseSlugModel):
    """
    Абстрактная модель бренда транспортного средства
    """
    logo = models.ImageField(
        _("Логотип"),
        upload_to='brands/',
        blank=True,
        null=True
    )
    description = models.TextField(_("Описание"), blank=True)
    year_founded = models.PositiveIntegerField(
        _("Год основания"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1800)]
    )
    country = models.CharField(_("Страна"), max_length=50, blank=True)
    is_active = models.BooleanField(_("Активен"), default=True)

    class Meta:
        abstract = True
        ordering = ['name']


# Бренды

class CarBrand(VehicleBrand):
    """Бренды легковых автомобилей (Toyota, BMW и т.д.)"""
    types = models.ManyToManyField(
        CarType,
        through='CarBrandTypeRelation',
        verbose_name=_("Типы автомобилей"),
        blank=True
    )
    categories = models.ManyToManyField(
        Category,
        through='CarBrandCategoryRelation',
        verbose_name=_("Категории запчастей"),
        blank=True
    )

    class Meta:
        verbose_name = _("Марка легкового автомобиля")
        verbose_name_plural = _("Марки легковых автомобилей")


class TruckBrand(VehicleBrand):
    """Бренды грузовой техники (Volvo, MAN и т.д.)"""
    types = models.ManyToManyField(
        TruckType,
        through='TruckBrandTypeRelation',
        verbose_name=_("Типы техники"),
        blank=True
    )
    categories = models.ManyToManyField(
        Category,
        through='TruckBrandCategoryRelation',
        verbose_name=_("Категории запчастей"),
        blank=True
    )

    class Meta:
        verbose_name = _("Марка грузовой техники")
        verbose_name_plural = _("Марки грузовой техники")


class MotoBrand(VehicleBrand):
    """Бренды мототехники (Harley-Davidson, Yamaha и т.д.)"""
    types = models.ManyToManyField(
        MotoType,
        through='MotoBrandTypeRelation',
        verbose_name=_("Типы мототехники"),
        blank=True
    )
    categories = models.ManyToManyField(
        Category,
        through='MotoBrandCategoryRelation',
        verbose_name=_("Категории запчастей"),
        blank=True
    )

    class Meta:
        verbose_name = _("Марка мототехники")
        verbose_name_plural = _("Марки мототехники")


class SpecialBrand(VehicleBrand):
    """Бренды спецтехники (Caterpillar, Komatsu и т.д.)"""
    types = models.ManyToManyField(
        SpecialType,
        through='SpecialBrandTypeRelation',
        verbose_name=_("Типы спецтехники"),
        blank=True
    )
    categories = models.ManyToManyField(
        Category,
        through='SpecialBrandCategoryRelation',
        verbose_name=_("Категории запчастей"),
        blank=True
    )

    class Meta:
        verbose_name = _("Марка спецтехники")
        verbose_name_plural = _("Марки спецтехники")


class BrandTypeRelation(models.Model):
    """Абстрактная модель связи бренда с типом транспорта"""
    is_main = models.BooleanField(_("Основной тип"), default=False)

    class Meta:
        abstract = True
        unique_together = ('brand', 'type')


class CarBrandTypeRelation(BrandTypeRelation):
    """Связь брендов легковых авто с типами кузова"""
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE)
    type = models.ForeignKey(CarType, on_delete=models.CASCADE)

    class Meta(BrandTypeRelation.Meta):
        verbose_name = _("Связь бренда с типом автомобиля")
        verbose_name_plural = _("Связи брендов с типами автомобилей")


class TruckBrandTypeRelation(BrandTypeRelation):
    """Связь брендов грузовиков с типами техники"""
    brand = models.ForeignKey(TruckBrand, on_delete=models.CASCADE)
    type = models.ForeignKey(TruckType, on_delete=models.CASCADE)

    class Meta(BrandTypeRelation.Meta):
        verbose_name = _("Связь бренда с типом грузовой техники")
        verbose_name_plural = _("Связи брендов с типами грузовой техники")


class MotoBrandTypeRelation(BrandTypeRelation):
    """Связь брендов мототехники с типами мото"""
    brand = models.ForeignKey(MotoBrand, on_delete=models.CASCADE)
    type = models.ForeignKey(MotoType, on_delete=models.CASCADE)

    class Meta(BrandTypeRelation.Meta):
        verbose_name = _("Связь бренда с типом мототехники")
        verbose_name_plural = _("Связи брендов с типами мототехники")


class SpecialBrandTypeRelation(BrandTypeRelation):
    """Связь брендов спецтехники с типами спецтехники"""
    brand = models.ForeignKey(SpecialBrand, on_delete=models.CASCADE)
    type = models.ForeignKey(SpecialType, on_delete=models.CASCADE)

    class Meta(BrandTypeRelation.Meta):
        verbose_name = _("Связь бренда с типом спецтехники")
        verbose_name_plural = _("Связи брендов с типами спецтехники")


class BrandCategoryRelation(models.Model):
    """Абстрактная модель связи бренда с категорией"""
    is_main = models.BooleanField(_("Основная категория"), default=False)

    class Meta:
        abstract = True
        unique_together = ('brand', 'category')


class CarBrandCategoryRelation(BrandCategoryRelation):
    """Связь категории с брендами легковых авто"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='car_brand_relations')
    brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE, related_name='category_relations')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('category', 'brand')


class TruckBrandCategoryRelation(BrandCategoryRelation):
    """Связь категории с брендами грузовиков"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='truck_brand_relations')
    brand = models.ForeignKey(TruckBrand, on_delete=models.CASCADE, related_name='category_relations')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('category', 'brand')


class MotoBrandCategoryRelation(BrandCategoryRelation):
    """Связь категории с брендами мототехники"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='moto_brand_relations')
    brand = models.ForeignKey(MotoBrand, on_delete=models.CASCADE, related_name='category_relations')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('category', 'brand')


class SpecialBrandCategoryRelation(BrandCategoryRelation):
    """Связь категории с брендами спецтехники"""
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='special_brand_relations')
    brand = models.ForeignKey(SpecialBrand, on_delete=models.CASCADE, related_name='category_relations')
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('category', 'brand')


class VehicleModel(BaseSlugModel):
    """
    Абстрактная модель транспортного средства
    """
    brand = models.ForeignKey(
        VehicleBrand,
        on_delete=models.CASCADE,
        related_name='models',
        verbose_name=_("Бренд")
    )
    type = models.ForeignKey(
        VehicleType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Тип")
    )
    year_start = models.PositiveIntegerField(
        _("Год начала выпуска"),
        validators=[MinValueValidator(1900)],
        null=True,  # Делаем поле необязательным
        blank=True
    )
    year_end = models.PositiveIntegerField(
        _("Год окончания выпуска"),
        null=True,
        blank=True
    )
    image = models.ImageField(
        _("Изображение"),
        upload_to='models/',
        blank=True,
        null=True
    )
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        abstract = True
        ordering = ['brand__name', 'name']
        unique_together = ('brand', 'name')

    def __str__(self):
        return f"{self.brand.name} {self.name}"

    def get_production_period(self):
        """Возвращает форматированную строку периода выпуска"""
        if self.year_end:
            return f"{self.year_start}-{self.year_end}"
        return f"{self.year_start}-{_('н.в.')}"


# Модели
class CarModel(VehicleModel):
    """Модели легковых автомобилей"""
    brand = models.ForeignKey(
        CarBrand,
        on_delete=models.CASCADE,
        related_name='car_models',
        verbose_name=_("Бренд")
    )
    type = models.ForeignKey(
        CarType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Тип кузова")
    )

    class Meta(VehicleModel.Meta):
        verbose_name = _("Модель легкового автомобиля")
        verbose_name_plural = _("Модели легковых автомобилей")


class TruckModel(VehicleModel):
    """Модели грузовой техники"""
    brand = models.ForeignKey(
        TruckBrand,
        on_delete=models.CASCADE,
        related_name='truck_models',
        verbose_name=_("Бренд")
    )
    type = models.ForeignKey(
        TruckType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Тип техники")
    )

    class Meta(VehicleModel.Meta):
        verbose_name = _("Модель грузовой техники")
        verbose_name_plural = _("Модели грузовой техники")


class MotoModel(VehicleModel):
    """Модели мототехники"""
    brand = models.ForeignKey(
        MotoBrand,
        on_delete=models.CASCADE,
        related_name='moto_models',
        verbose_name=_("Бренд")
    )
    type = models.ForeignKey(
        MotoType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Тип мототехники")
    )

    class Meta(VehicleModel.Meta):
        verbose_name = _("Модель мототехники")
        verbose_name_plural = _("Модели мототехники")


class SpecialModel(VehicleModel):
    """Модели спецтехники"""
    brand = models.ForeignKey(
        SpecialBrand,
        on_delete=models.CASCADE,
        related_name='special_models',
        verbose_name=_("Бренд")
    )
    type = models.ForeignKey(
        SpecialType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Тип спецтехники")
    )

    class Meta(VehicleModel.Meta):
        verbose_name = _("Модель спецтехники")
        verbose_name_plural = _("Модели спецтехники")


class VehicleGeneration(BaseSlugModel):
    """
    Абстрактная модель поколения транспортного средства
    """
    model = models.ForeignKey(
        VehicleModel,
        on_delete=models.CASCADE,
        related_name='generations',
        verbose_name=_("Модель")
    )
    year_start = models.PositiveIntegerField(
        _("Год начала выпуска"),
        validators=[MinValueValidator(1900)]
    )
    year_end = models.PositiveIntegerField(
        _("Год окончания выпуска"),
        null=True,
        blank=True
    )
    image = models.ImageField(
        _("Изображение"),
        upload_to='generations/',
        blank=True,
        null=True
    )
    is_active = models.BooleanField(_("Активно"), default=True)

    class Meta:
        abstract = True
        ordering = ['model__brand__name', 'model__name', 'year_start']
        unique_together = ('model', 'name')

    def __str__(self):
        return f"{self.model.brand.name} {self.model.name} ({self.name})"


# Поколения

class CarGeneration(VehicleGeneration):
    """Поколения моделей легковых автомобилей"""
    model = models.ForeignKey(
        CarModel,
        on_delete=models.CASCADE,
        related_name='car_generations',
        verbose_name=_("Модель")
    )

    class Meta(VehicleGeneration.Meta):
        verbose_name = _("Поколение легкового автомобиля")
        verbose_name_plural = _("Поколения легковых автомобилей")


class TruckGeneration(VehicleGeneration):
    """Поколения моделей грузовой техники"""
    model = models.ForeignKey(
        TruckModel,
        on_delete=models.CASCADE,
        related_name='truck_generations',
        verbose_name=_("Модель")
    )
    load_capacity = models.PositiveIntegerField(
        _("Грузоподъемность (кг)"),
        null=True,
        blank=True
    )

    class Meta(VehicleGeneration.Meta):
        verbose_name = _("Поколение грузовой техники")
        verbose_name_plural = _("Поколения грузовой техники")


class MotoGeneration(VehicleGeneration):
    """Поколения моделей мототехники"""
    model = models.ForeignKey(
        MotoModel,
        on_delete=models.CASCADE,
        related_name='moto_generations',
        verbose_name=_("Модель")
    )
    engine_volume = models.PositiveIntegerField(
        _("Объем двигателя (см³)"),
        null=True,
        blank=True
    )
    engine_power = models.PositiveIntegerField(
        _("Мощность двигателя (л.с.)"),
        null=True,
        blank=True
    )

    class Meta(VehicleGeneration.Meta):
        verbose_name = _("Поколение мототехники")
        verbose_name_plural = _("Поколения мототехники")


class SpecialGeneration(VehicleGeneration):
    """Поколения моделей спецтехники"""
    model = models.ForeignKey(
        SpecialModel,
        on_delete=models.CASCADE,
        related_name='special_generations',
        verbose_name=_("Модель")
    )
    weight = models.PositiveIntegerField(
        _("Вес (кг)"),
        null=True,
        blank=True
    )
    power = models.PositiveIntegerField(
        _("Мощность (л.с.)"),
        null=True,
        blank=True
    )

    class Meta(VehicleGeneration.Meta):
        verbose_name = _("Поколение спецтехники")
        verbose_name_plural = _("Поколения спецтехники")


############# Хештег ###########

class Tag(models.Model):
    """Модель для тегов/хэштегов товаров"""
    name = models.CharField(
        _("Название тега"),
        max_length=50,
        unique=True,
        db_index=True
    )
    slug = models.SlugField(unique=True)
    color = models.CharField(
        _("Цвет тега"),
        max_length=7,
        default='#6c757d',
        help_text=_("Цвет в формате HEX, например: #007bff")
    )
    is_active = models.BooleanField(_("Активен"), default=True)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True)

    class Meta:
        verbose_name = _("Тег")
        verbose_name_plural = _("Теги")
        ordering = ['name']

    def __str__(self):
        return f"#{self.name}"

    def get_absolute_url(self):
        return reverse('shop:tag_detail', kwargs={'slug': self.slug})


# Модификации


class CarModification(models.Model):
    """Модификация (комплектация) поколения легкового автомобиля"""
    generation = models.ForeignKey(
        CarGeneration,
        on_delete=models.CASCADE,
        related_name='modifications',
        verbose_name=_("Поколение")
    )
    name = models.CharField(_("Название модификации"), max_length=100, db_index=True)
    slug = models.SlugField(max_length=150, unique=True, db_index=True, blank=True)
    engine_type = models.CharField(
        _("Тип двигателя"),
        max_length=20,
        choices=[
            ('gasoline', _("Бензиновый")),
            ('diesel', _("Дизельный")),
            ('hybrid', _("Гибридный")),
            ('electric', _("Электрический")),
            ('unknown', _("Не указано")),
        ],
        default='unknown'
    )
    engine_volume = models.CharField(_("Объем двигателя"), max_length=20, blank=True)  # Например: "1.6", "2.0T"
    power = models.PositiveIntegerField(_("Мощность (л.с.)"), null=True, blank=True)
    transmission = models.CharField(
        _("Коробка передач"),
        max_length=20,
        choices=[
            ('manual', _("Механическая")),
            ('automatic', _("Автоматическая")),
            ('robot', _("Роботизированная")),
            ('cvt', _("Вариатор")),
            ('unknown', _("Не указано")),
        ],
        default='unknown'
    )
    drive_type = models.CharField(
        _("Привод"),
        max_length=20,
        choices=[
            ('front', _("Передний")),
            ('rear', _("Задний")),
            ('awd', _("Полный")),
            ('unknown', _("Не указано")),
        ],
        default='unknown'
    )
    body_type = models.CharField(_("Тип кузова"), max_length=50, blank=True)  # Например: "седан", "хэтчбек"

    class Meta:
        verbose_name = _("Модификация легкового автомобиля")
        verbose_name_plural = _("Модификации легковых автомобилей")
        ordering = ['name']
        indexes = [
            models.Index(fields=['generation']),
            models.Index(fields=['name']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return f"{self.generation.model.brand.name} {self.generation.model.name} {self.generation.name} {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            # Создаем базовый slug из названия
            base_slug = slugify(self.name)

            # Добавляем информацию о поколении для уникальности
            generation_slug = slugify(self.generation.name)
            model_slug = slugify(self.generation.model.name)
            brand_slug = slugify(self.generation.model.brand.name)

            # Собираем полный slug
            full_slug = f"{brand_slug}-{model_slug}-{generation_slug}-{base_slug}"

            # Ограничиваем длину
            if len(full_slug) > 150:
                full_slug = full_slug[:147] + "..."

            # Делаем slug уникальным
            original_slug = full_slug
            counter = 1
            while CarModification.objects.filter(slug=full_slug).exclude(pk=self.pk).exists():
                full_slug = f"{original_slug}-{counter}"
                counter += 1

            self.slug = full_slug
        super().save(*args, **kwargs)


class TruckModification(models.Model):
    """Модификация (комплектация) поколения грузовика"""
    generation = models.ForeignKey(
        TruckGeneration,
        on_delete=models.CASCADE,
        related_name='modifications',
        verbose_name=_("Поколение")
    )
    name = models.CharField(_("Название модификации"), max_length=100, db_index=True)
    slug = models.SlugField(max_length=150, unique=True, db_index=True, blank=True)
    engine_type = models.CharField(
        _("Тип двигателя"),
        max_length=20,
        choices=[
            ('diesel', _("Дизельный")),
            ('gasoline', _("Бензиновый")),
            ('gas', _("Газовый")),
            ('unknown', _("Не указано")),
        ],
        default='unknown'
    )
    engine_power = models.PositiveIntegerField(_("Мощность двигателя (л.с.)"), null=True, blank=True)
    transmission = models.CharField(_("Коробка передач"), max_length=50, blank=True)
    cabin_type = models.CharField(
        _("Тип кабины"),
        max_length=50,
        blank=True,
        help_text=_("Например: спальная, одноместная")
    )

    class Meta:
        verbose_name = _("Модификация грузовика")
        verbose_name_plural = _("Модификации грузовиков")
        ordering = ['name']

    def __str__(self):
        return f"{self.generation.model.brand.name} {self.generation.model.name} {self.generation.name} {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            # Создаем базовый slug из названия
            base_slug = slugify(self.name)

            # Добавляем информацию о поколении для уникальности
            generation_slug = slugify(self.generation.name)
            model_slug = slugify(self.generation.model.name)
            brand_slug = slugify(self.generation.model.brand.name)

            # Собираем полный slug
            full_slug = f"{brand_slug}-{model_slug}-{generation_slug}-{base_slug}"

            # Ограничиваем длину
            if len(full_slug) > 150:
                full_slug = full_slug[:147] + "..."

            # Делаем slug уникальным
            original_slug = full_slug
            counter = 1
            while TruckModification.objects.filter(slug=full_slug).exclude(pk=self.pk).exists():
                full_slug = f"{original_slug}-{counter}"
                counter += 1

            self.slug = full_slug
        super().save(*args, **kwargs)


class MotoModification(models.Model):
    """Модификация (версия) поколения мотоцикла"""
    generation = models.ForeignKey(
        MotoGeneration,
        on_delete=models.CASCADE,
        related_name='modifications',
        verbose_name=_("Поколение")
    )
    name = models.CharField(_("Название модификации"), max_length=100, db_index=True)
    slug = models.SlugField(max_length=150, unique=True, db_index=True, blank=True)
    version_type = models.CharField(
        _("Тип версии"),
        max_length=50,
        choices=[
            ('standard', _("Стандарт")),
            ('deluxe', _("Делюкс")),
            ('sport', _("Спорт")),
            ('tour', _("Туризм")),
            ('special', _("Специальная")),
        ],
        default='standard'
    )

    class Meta:
        verbose_name = _("Модификация мотоцикла")
        verbose_name_plural = _("Модификации мотоциклов")
        ordering = ['name']

    def __str__(self):
        return f"{self.generation.model.brand.name} {self.generation.model.name} {self.generation.name} {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            # Создаем базовый slug из названия
            base_slug = slugify(self.name)

            # Добавляем информацию о поколении для уникальности
            generation_slug = slugify(self.generation.name)
            model_slug = slugify(self.generation.model.name)
            brand_slug = slugify(self.generation.model.brand.name)

            # Собираем полный slug
            full_slug = f"{brand_slug}-{model_slug}-{generation_slug}-{base_slug}"

            # Ограничиваем длину
            if len(full_slug) > 150:
                full_slug = full_slug[:147] + "..."

            # Делаем slug уникальным
            original_slug = full_slug
            counter = 1
            while MotoModification.objects.filter(slug=full_slug).exclude(pk=self.pk).exists():
                full_slug = f"{original_slug}-{counter}"
                counter += 1

            self.slug = full_slug
        super().save(*args, **kwargs)


class SpecialModification(models.Model):
    """Модификация (версия) поколения спецтехники"""
    generation = models.ForeignKey(
        SpecialGeneration,
        on_delete=models.CASCADE,
        related_name='modifications',
        verbose_name=_("Поколение")
    )
    name = models.CharField(_("Название модификации"), max_length=100, db_index=True)
    slug = models.SlugField(max_length=150, unique=True, db_index=True, blank=True)
    equipment_level = models.CharField(
        _("Уровень комплектации"),
        max_length=50,
        choices=[
            ('basic', _("Базовая")),
            ('standard', _("Стандартная")),
            ('premium', _("Премиум")),
            ('special', _("Специальная")),
        ],
        default='standard'
    )
    additional_equipment = models.TextField(_("Дополнительное оборудование"), blank=True)

    class Meta:
        verbose_name = _("Модификация спецтехники")
        verbose_name_plural = _("Модификации спецтехники")
        ordering = ['name']

    def __str__(self):
        return f"{self.generation.model.brand.name} {self.generation.model.name} {self.generation.name} {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            # Создаем базовый slug из названия
            base_slug = slugify(self.name)

            # Добавляем информацию о поколении для уникальности
            generation_slug = slugify(self.generation.name)
            model_slug = slugify(self.generation.model.name)
            brand_slug = slugify(self.generation.model.brand.name)

            # Собираем полный slug
            full_slug = f"{brand_slug}-{model_slug}-{generation_slug}-{base_slug}"

            # Ограничиваем длину
            if len(full_slug) > 150:
                full_slug = full_slug[:147] + "..."

            # Делаем slug уникальным
            original_slug = full_slug
            counter = 1
            while SpecialModification.objects.filter(slug=full_slug).exclude(pk=self.pk).exists():
                full_slug = f"{original_slug}-{counter}"
                counter += 1

            self.slug = full_slug
        super().save(*args, **kwargs)

################### Продукт ##################


class ProductManager(models.Manager):
    """Менеджер с методом для публичного каталога (только одобренные и активные товары)."""

    def visible_to_public(self):
        from django.db.models import Q
        # Товары без продавца (админские) показываем если активны; с продавцом — только одобренные
        return self.get_queryset().filter(is_active=True).filter(
            Q(seller__isnull=True) | (Q(seller__status='approved') & Q(moderation_status='approved'))
        )


class Product(BaseSlugModel):
    """
    Товары (автозапчасти, аксессуары и т.д.) с расширенной системой фильтрации
    """
    objects = ProductManager()

    VEHICLE_TYPES = [
        ('car', _('Легковой автомобиль')),
        ('truck', _('Грузовой автомобиль')),
        ('moto', _('Мототехника')),
        ('special', _('Спецтехника')),
        ('universal', _('Универсальный')),
    ]

    PRODUCT_TYPES = [
        ('spare_part', _('Запчасть')),
        ('oil_chem', _('Автохимия и масла')),
        ('maintenance', _('Техническое обслуживание')),
        ('tire_wheel', _('Шины и диски')),
        ('tool', _('Инструменты')),
        ('auto_electric', _('Автоэлектрика')),
        ('accessory', _('Аксессуар')),
    ]
    MAINTENANCE_TYPES = [
        ('oil_filter', 'Масляный фильтр'),
        ('air_filter', 'Воздушный фильтр'),
        ('fuel_filter', 'Топливный фильтр'),
        ('cabin_filter', 'Салонный фильтр'),
        ('spark_plug', 'Свеча зажигания'),
        ('engine_oil', 'Моторное масло'),
        ('transmission_oil', 'Трансмиссионное масло'),
        ('brake_fluid', 'Тормозная жидкость'),
        ('coolant', 'Антифриз'),
        ('belt', 'Ремень'),
        ('roller', 'Ролик'),
        ('other', 'Другое'),
    ]
    TIRE_WHEEL_TYPES = [
        ('tire', _('Шина')),
        ('wheel', _('Диск')),
        ('unknown', _('Не указано')),
    ]

    tire_wheel_type = models.CharField(
        _("Тип (шина/диск)"),
        max_length=20,
        choices=TIRE_WHEEL_TYPES,
        default='unknown',
        db_index=True
    )

    # Основная информация
    name = models.CharField(_("Название"), max_length=200, db_index=True)
    part_number = models.CharField(
        _("Артикул"),
        max_length=50,
        db_index=True,
        blank=True,
        null=True,
        help_text=_("Идентификатор товара (может повторяться)")
    )
    normalized_part_number = models.CharField(
        _("Normalized part number"),
        max_length=100,
        blank=True,
        default='',
        db_index=True,
        editable=False,
        help_text=_("Service field for part-number and cross-reference search")
    )
    internal_code = models.CharField(
        _("Внутренний код товара"),
        max_length=32,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
        help_text=_("Служебный внутренний код для техподдержки")
    )
    product_type = models.CharField(
        _("Тип товара"),
        max_length=20,
        choices=PRODUCT_TYPES,
        default='spare_part',
        db_index=True
    )
    description = models.TextField(_("Описание"), blank=True)
    short_description = models.TextField(_("Краткое описание"), blank=True)
    slug = models.SlugField(unique=True)

    image = models.ImageField(
        _("Изображение"),
        upload_to='products/%Y/%m/%d/',
        blank=True,
        null=True,
        default='products/default.png'
    )

    # Цена и наличие
    price = models.DecimalField(
        _("Цена"),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        db_index=True
    )
    old_price = models.DecimalField(
        _("Старая цена"),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    stock = models.PositiveIntegerField(
        _("Остаток на складе"),
        default=0
    )
    is_original = models.BooleanField(
        _("Оригинал"),
        default=False,
        help_text=_("Отметьте, если товар оригинальный")
    )
    is_active = models.BooleanField(_("Активен"), default=True)
    is_featured = models.BooleanField(_("Рекомендуемый"), default=False)
    is_new = models.BooleanField(_("Новинка"), default=False)

    # Модерация (для товаров продавцов)
    MODERATION_STATUS_CHOICES = [
        ('draft', _('Черновик')),
        ('pending', _('На проверке')),
        ('approved', _('Одобрен')),
        ('rejected', _('Отклонен')),
        ('suspended', _('Приостановлен')),
        ('revision', _('Требует правок')),
    ]
    moderation_status = models.CharField(
        _("Статус модерации"),
        max_length=20,
        choices=MODERATION_STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    moderation_notes = models.TextField(
        _("Замечания модератора"),
        blank=True,
        help_text=_("Причина отклонения или запроса правок")
    )
    moderated_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_products',
        verbose_name=_("Проверил")
    )
    moderated_at = models.DateTimeField(
        _("Дата модерации"),
        null=True,
        blank=True
    )

    # Основные категории и производители
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_("Основная категория")
    )
    extra_categories = models.ManyToManyField(
        Category,
        blank=True,
        related_name='extra_products',
        verbose_name=_("Дополнительные категории"),
        help_text=_("Товар будет отображаться во всех выбранных категориях")
    )
    manufacturer = models.ForeignKey(
        Manufacturer,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Производитель")
    )
    product_brand = models.ForeignKey(
        'ProductBrand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Бренд товара"),
        related_name='products'
    )
    # Специализированные категории и бренды
    oil_chem_category = models.ForeignKey(
        'OilAndChemistryCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Категория автохимии"),
        related_name='products'
    )
    oil_chem_brand = models.ForeignKey(
        'OilAndChemistryBrand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Бренд автохимии"),
        related_name='products'
    )
    maintenance_category = models.ForeignKey(
        'MaintenanceCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Категория ТО"),
        related_name='products'
    )
    maintenance_brand = models.ForeignKey(
        'MaintenanceBrand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Бренд ТО"),
        related_name='products'
    )
    tire_wheel_category = models.ForeignKey(
        'TireAndWheelCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Категория шин и дисков"),
        related_name='products'
    )
    tire_wheel_brand = models.ForeignKey(
        'TireAndWheelBrand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Бренд шин и дисков"),
        related_name='products'
    )

    tool_category = models.ForeignKey(
        'ToolCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Категория инструментов"),
        related_name='products'
    )
    tool_brand = models.ForeignKey(
        'ToolBrand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Бренд инструментов"),
        related_name='products'
    )

    auto_electric_category = models.ForeignKey(
        'AutoElectricCategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Категория автоэлектрики"),
        related_name='products'
    )
    auto_electric_brand = models.ForeignKey(
        'AutoElectricBrand',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Бренд автоэлектрики"),
        related_name='products'
    )
    vin = models.CharField(
        _("VIN запчасти"),
        max_length=50,
        blank=True,
        null=True,
        db_index=True,
        help_text=_("VIN-код оригинальной запчасти")
    )

    # Тип транспорта и совместимость
    vehicle_type = models.CharField(
        _("Тип транспорта"),
        max_length=20,
        choices=VEHICLE_TYPES,
        default='universal',
        db_index=True
    )

    # Связи с брендами и моделями
    car_brand = models.ForeignKey(
        CarBrand,
        on_delete=models.SET_NULL,
        related_name='car_products',
        null=True,
        blank=True,
        verbose_name=_("Бренд авто")
    )
    car_models = models.ManyToManyField(
        CarModel,
        verbose_name=_("Модели авто"),
        related_name='products',
        blank=True
    )
    car_generations = models.ManyToManyField(
        CarGeneration,
        verbose_name=_("Поколения авто"),
        related_name='products',
        blank=True
    )

    truck_brand = models.ForeignKey(
        TruckBrand,
        on_delete=models.SET_NULL,
        related_name='truck_products',
        null=True,
        blank=True,
        verbose_name=_("Бренд грузовика")
    )
    truck_models = models.ManyToManyField(
        TruckModel,
        verbose_name=_("Модели грузовиков"),
        related_name='products',
        blank=True
    )
    truck_generations = models.ManyToManyField(
        TruckGeneration,
        verbose_name=_("Поколения грузовиков"),
        related_name='products',
        blank=True
    )

    moto_brand = models.ForeignKey(
        MotoBrand,
        on_delete=models.SET_NULL,
        related_name='moto_products',
        null=True,
        blank=True,
        verbose_name=_("Бренд мото")
    )
    moto_models = models.ManyToManyField(
        MotoModel,
        verbose_name=_("Модели мото"),
        related_name='products',
        blank=True
    )
    moto_generations = models.ManyToManyField(
        MotoGeneration,
        verbose_name=_("Поколения мото"),
        related_name='products',
        blank=True
    )

    special_brand = models.ForeignKey(
        SpecialBrand,
        on_delete=models.SET_NULL,
        related_name='special_products',
        null=True,
        blank=True,
        verbose_name=_("Бренд спецтехники")
    )
    special_models = models.ManyToManyField(
        SpecialModel,
        verbose_name=_("Модели спецтехники"),
        related_name='products',
        blank=True
    )
    special_generations = models.ManyToManyField(
        SpecialGeneration,
        verbose_name=_("Поколения спецтехники"),
        related_name='products',
        blank=True
    )
    
    part_subcategory = models.ForeignKey(
        'PartSubcategory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name="Подкатегория запчастей"
    )

    # Габариты
    weight = models.DecimalField(
        _("Вес (г)"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=False
    )
    length = models.DecimalField(
        _("Длина (мм)"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=False,
        help_text=_("Длина в миллиметрах")
    )
    width = models.DecimalField(
        _("Ширина (мм)"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=False,
        help_text=_("Ширина в миллиметрах")
    )
    height = models.DecimalField(
        _("Высота (мм)"),
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=False,
        help_text=_("Высота в миллиметрах")
    )
    under_order = models.BooleanField(
        _("Под заказ"),
        default=False,
        help_text=_("Товар доступен только под заказ")
    )
    country_of_origin = models.CharField(
        _("Страна производитель"),
        max_length=100,
        blank=True,
        default='',
        help_text=_("Страна, в которой произведён товар")
    )
    warranty = models.PositiveIntegerField(
        _("Гарантия (мес)"),
        null=True,
        blank=True
    )

    # Метаданные
    created_at = models.DateTimeField(
        _("Дата добавления"),
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        _("Дата обновления"),
        auto_now=True
    )
    views = models.PositiveIntegerField(
        _("Просмотры"),
        default=0
    )
    maintenance_type = models.CharField(
        _("Тип расходника ТО"),
        max_length=20,
        choices=MAINTENANCE_TYPES,
        null=True,
        blank=True,
        db_index=True
    )

    # Характеристики для масел
    viscosity = models.CharField(
        _("Вязкость масла"),
        max_length=20,
        blank=True,
        null=True,
        help_text="Например: 5W-30, 5W-40"
    )

    volume = models.DecimalField(
        _("Объем"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Объем в литрах"
    )

    # Для фильтров
    filter_type = models.CharField(
        _("Тип фильтра"),
        max_length=50,
        blank=True,
        null=True
    )

    # Для свечей
    spark_plug_type = models.CharField(
        _("Тип свечи"),
        max_length=50,
        blank=True,
        null=True
    )
    seller = models.ForeignKey(
        'sellers.Seller',
        on_delete=models.CASCADE,
        related_name='products',
        verbose_name=_("Продавец"),
        null=True,
        blank=True
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name=_("Теги"),
        related_name='products',
        blank=True,
        help_text=_("Ключевые слова для поиска и фильтрации")
    )

    # НОВЫЕ связи для модификаций
    car_modifications = models.ManyToManyField(
        'CarModification',
        verbose_name=_("Модификации авто"),
        related_name='products',
        blank=True
    )

    truck_modifications = models.ManyToManyField(
        'TruckModification',
        verbose_name=_("Модификации грузовиков"),
        related_name='products',
        blank=True
    )

    moto_modifications = models.ManyToManyField(
        'MotoModification',
        verbose_name=_("Модификации мото"),
        related_name='products',
        blank=True
    )

    special_modifications = models.ManyToManyField(
        'SpecialModification',
        verbose_name=_("Модификации спецтехники"),
        related_name='products',
        blank=True
    )

    class Meta:
        verbose_name = _("Товар")
        verbose_name_plural = _("Товары")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['part_number']),
            models.Index(fields=['price']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['is_new']),
            models.Index(fields=['product_type']),
        ]

    def get_specialized_category(self):
        """Возвращает специализированную категорию в зависимости от типа товара"""
        category_mapping = {
            'oil_chem': self.oil_chem_category,
            'maintenance': self.maintenance_category,
            'tire_wheel': self.tire_wheel_category,
            'tool': self.tool_category,
            'auto_electric': self.auto_electric_category,
        }
        return category_mapping.get(self.product_type)

    def get_specialized_brand(self):
        """Возвращает специализированный бренд в зависимости от типа товара"""
        brand_mapping = {
            'oil_chem': self.oil_chem_brand,
            'maintenance': self.maintenance_brand,
            'tire_wheel': self.tire_wheel_brand,
            'tool': self.tool_brand,
            'auto_electric': self.auto_electric_brand,
        }
        return brand_mapping.get(self.product_type)

    def get_brand(self):
        """Возвращает бренд в зависимости от типа транспорта или товара"""
        vehicle_brand = super().get_brand()
        if vehicle_brand:
            return vehicle_brand
        return self.get_specialized_brand()

    def get_models(self):
        """Возвращает список моделей в зависимости от типа транспорта"""
        model_mapping = {
            'car': self.car_models.all(),
            'truck': self.truck_models.all(),
            'moto': self.moto_models.all(),
            'special': self.special_models.all()
        }
        return model_mapping.get(self.vehicle_type, [])

    def get_generations(self):
        """Возвращает поколения в зависимости от типа транспорта"""
        generation_mapping = {
            'car': self.car_generations.all(),
            'truck': self.truck_generations.all(),
            'moto': self.moto_generations.all(),
            'special': self.special_generations.all()
        }
        return generation_mapping.get(self.vehicle_type, [])

    def get_discount(self):
        """Возвращает размер скидки в процентах, если есть старая цена"""
        if self.old_price and self.old_price > self.price:
            return int((1 - self.price / self.old_price) * 100)
        return 0

    def get_absolute_url(self):
        return reverse('shop:product_detail', kwargs={'slug': self.slug})

    @property
    def average_rating(self):
        """Средний рейтинг товара"""
        from django.db.models import Avg
        return self.reviews.filter(is_published=True).aggregate(Avg('rating'))['rating__avg'] or 0

    def get_average_rating(self):
        """Возвращает средний рейтинг товара (метод для совместимости с шаблонами)"""
        return self.average_rating

    @property
    def review_count(self):
        """Количество отзывов"""
        return self.reviews.filter(is_published=True).count()

    def get_published_reviews(self):
        """Возвращает queryset опубликованных отзывов"""
        return self.reviews.filter(is_published=True)

    # Рейтинг
    def get_rating_stars(self):
        """Возвращает HTML с звездами рейтинга"""
        rating = self.average_rating
        stars = []
        for i in range(1, 6):
            if i <= rating:
                stars.append('<i class="fas fa-star text-warning"></i>')
            elif i - 0.5 <= rating:
                stars.append('<i class="fas fa-star-half-alt text-warning"></i>')
            else:
                stars.append('<i class="far fa-star text-warning"></i>')
        return mark_safe(''.join(stars))

    def get_rating_stars_dict(self):
        """Возвращает словарь с информацией о звездах рейтинга"""
        rating = float(self.average_rating or 0)
        full_stars = int(rating)
        half_star = (rating - full_stars) >= 0.5
        empty_stars = 5 - full_stars - (1 if half_star else 0)

        return {
            'full_stars': full_stars,
            'half_star': half_star,
            'empty_stars': empty_stars,
            'rating': rating
        }

    def user_has_purchased(self, user):
        """
        Проверяет, купил ли пользователь этот товар (заказ оплачен и не отменен)
        """
        if not user or not user.is_authenticated:
            return False

        from orders.models import OrderItem
        return OrderItem.objects.filter(
            product=self,
            order__user=user,
            order__paid=True,
        ).exclude(
            order__status='canceled'
        ).exists()

    def get_all_images(self):
        """
        Возвращает список всех изображений товара (основное + дополнительные)
        Только изображения с реально существующими файлами и валидными URL
        """
        images = []

        # Добавляем основное изображение первым, если оно есть и файл загружен
        if self.image and self.image.name and self.image.name.strip():
            try:
                # Проверяем существование файла на диске
                if self.image.storage.exists(self.image.name):
                    url = self.image.url
                    # Строгая проверка: URL должен быть не пустым, не состоять только из пробелов,
                    # и быть валидным (начинаться с / или http)
                    url_clean = url.strip() if url else ''
                    if url_clean and len(url_clean) > 0 and (url_clean.startswith('/') or url_clean.startswith('http')):
                        images.append({
                            'url': url_clean,
                            'alt': self.name,
                            'is_main': True
                        })
            except (ValueError, AttributeError, Exception):
                # Если возникла ошибка при получении URL или проверке файла, пропускаем это изображение
                pass

        # Добавляем дополнительные изображения только если файл загружен и существует
        for img in self.images.all().exclude(image=''):
            # Проверяем, что поле image не пустое и файл действительно загружен
            if img.image and img.image.name and img.image.name.strip():
                try:
                    # Проверяем существование файла на диске
                    if img.image.storage.exists(img.image.name):
                        url = img.image.url
                        # Строгая проверка: URL должен быть не пустым, не состоять только из пробелов,
                        # и быть валидным (начинаться с / или http)
                        url_clean = url.strip() if url else ''
                        if url_clean and len(url_clean) > 0 and (
                                url_clean.startswith('/') or url_clean.startswith('http')):
                            images.append({
                                'url': url_clean,
                                'alt': img.alt_text or self.name,
                                'is_main': False
                            })
                except (ValueError, AttributeError, Exception):
                    # Если возникла ошибка при получении URL или проверке файла, пропускаем это изображение
                    pass

        return images

    def get_rating_distribution(self):
        distribution = {str(i): 0 for i in range(1, 6)}
        reviews = self.reviews.filter(is_published=True).values('rating').annotate(count=Count('rating'))
        for item in reviews:
            distribution[str(item['rating'])] = item['count']
        return distribution

    def get_rating_percentage(self):
        total = self.review_count
        if total == 0:
            return {str(i): 0 for i in range(1, 6)}

        distribution = self.get_rating_distribution()
        return {
            str(i): round((distribution[str(i)] / total) * 100)
            for i in range(1, 6)
        }

    def clean(self):
        super().clean()
        if self.vin:
            # Простая валидация VIN (можно расширить)
            if len(self.vin) not in (17, 20):
                raise ValidationError(
                    {'vin': _("VIN должен содержать 17 или 20 символов")}
                )
            if not all(c.isalnum() for c in self.vin):
                raise ValidationError(
                    {'vin': _("VIN может содержать только буквы и цифры")}
                )

    sale_end_date = models.DateTimeField(
        _("Дата окончания акции"),
        null=True,
        blank=True,
        help_text=_("Дата, до которой действует скидка")
    )

    @property
    def has_active_sale(self):
        """Проверяет, активна ли акция"""
        if not self.old_price or self.old_price <= self.price:
            return False
        if self.sale_end_date:
            return timezone.now() <= self.sale_end_date
        return True

    @property
    def time_until_sale_end(self):
        """Возвращает оставшееся время акции в секундах"""
        if self.sale_end_date and self.has_active_sale:
            return int((self.sale_end_date - timezone.now()).total_seconds())
        return None

    def get_compatibility_display(self):
        """Отображение совместимости для админки"""
        compatibilities = []
        if self.car_brand:
            compatibilities.append(f"{self.car_brand.name}")
        if self.car_models.exists():
            compatibilities.append(f"{self.car_models.count()} моделей")
        if self.car_generations.exists():
            compatibilities.append(f"{self.car_generations.count()} поколений")
        return ", ".join(compatibilities) if compatibilities else "Универсальный"

    get_compatibility_display.short_description = "Совместимость"

    # Методы для доступа к характеристикам шин и дисков
    @property
    def is_tire(self):
        """Проверяет, является ли товар шиной"""
        return self.product_type == 'tire_wheel' and self.tire_wheel_type == 'tire'

    @property
    def is_wheel(self):
        """Проверяет, является ли товар диском"""
        return self.product_type == 'tire_wheel' and self.tire_wheel_type == 'wheel'

    def get_tire_details(self):
        """Возвращает характеристики шины"""
        if hasattr(self, 'tire_details'):
            return self.tire_details
        return None

    def get_wheel_details(self):
        """Возвращает характеристики диска"""
        if hasattr(self, 'wheel_details'):
            return self.wheel_details
        return None

    def get_tire_wheel_specs_display(self):
        """Возвращает отображение спецификаций для списка товаров"""
        if self.is_tire and hasattr(self, 'tire_details'):
            return self.tire_details.get_size_display()
        elif self.is_wheel and hasattr(self, 'wheel_details'):
            return self.wheel_details.get_full_specs()
        return "-"

    def get_average_rating_display(self):
        """Возвращает средний рейтинг в формате X,X"""
        return f"{self.average_rating:.1f}".replace('.', ',')

    def get_rating_display(self, rating):
        """Форматирует рейтинг в формат X,0"""
        return f"{rating:.1f}".replace('.', ',')

    def generate_tags(self):
        """Автоматически генерирует теги на основе характеристик товара"""
        from django.utils.text import slugify

        tags_to_add = []

        # Тег по типу товара
        product_type_tag = f"{self.get_product_type_display()}".lower()
        tags_to_add.append(product_type_tag)

        # Тег по типу транспорта
        vehicle_type_tag = f"{self.get_vehicle_type_display()}".lower()
        tags_to_add.append(vehicle_type_tag)

        # Тег по производителю
        if self.manufacturer:
            manufacturer_tag = f"{self.manufacturer.name}".lower()
            tags_to_add.append(manufacturer_tag)

        # Тег по бренду авто
        if self.car_brand:
            brand_tag = f"{self.car_brand.name}".lower()
            tags_to_add.append(brand_tag)

        # Тег по модели авто
        for model in self.car_models.all()[:2]:
            model_tag = f"{model.name}".lower()
            tags_to_add.append(model_tag)

        # Тег по характеристикам
        if self.is_original:
            tags_to_add.append("оригинал")
        if self.is_new:
            tags_to_add.append("новинка")
        if self.old_price:
            tags_to_add.append("акция")
        if self.stock > 10:
            tags_to_add.append("вналичии")

        # Создаем или получаем теги
        for tag_name in set(tags_to_add):  # set для удаления дубликатов
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                defaults={'slug': slugify(tag_name)}
            )
            self.tags.add(tag)

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        should_generate_code = not self.internal_code
        self.normalized_part_number = normalize_article_number(self.part_number)

        # Сначала сохраняем объект, чтобы получить pk
        super().save(*args, **kwargs)

        # Генерируем внутренний код для новых и старых товаров, у которых его нет
        if should_generate_code and not self.internal_code and self.pk:
            Model = type(self)

            # Базовый детерминированный код от ID, чтобы было проще озвучивать по телефону
            base_code = f"P-{self.pk:06d}"
            code = base_code

            if Model.objects.filter(internal_code=code).exists():
                # Фолбэк на случай коллизии: генерируем случайный суффикс
                # Стараемся получить уникальный код за несколько попыток
                for _ in range(5):
                    random_code = f"P-{get_random_string(8).upper()}"
                    if not Model.objects.filter(internal_code=random_code).exists():
                        code = random_code
                        break
                else:
                    # Если вдруг все попытки неудачны, продолжаем генерировать до успеха
                    while True:
                        random_code = f"P-{get_random_string(10).upper()}"
                        if not Model.objects.filter(internal_code=random_code).exists():
                            code = random_code
                            break

            # Обновляем только поле internal_code в базе и в текущем экземпляре
            Model.objects.filter(pk=self.pk).update(internal_code=code)
            self.internal_code = code

    def get_dimensions_display(self):
        """Возвращает габариты в формате 'ДxШxВ мм'"""
        dimensions = []
        if self.length:
            dimensions.append(str(self.length))
        if self.width:
            dimensions.append(str(self.width))
        if self.height:
            dimensions.append(str(self.height))

        if dimensions:
            return f"{'×'.join(dimensions)} мм"
        return "-"

    get_dimensions_display.short_description = _("Габариты")

    def get_modifications(self):
        """Возвращает модификации в зависимости от типа транспорта"""
        modification_mapping = {
            'car': self.car_modifications.all(),
            'truck': self.truck_modifications.all(),
            'moto': self.moto_modifications.all(),
            'special': self.special_modifications.all()
        }
        return modification_mapping.get(self.vehicle_type, [])

    def get_compatibility_display(self):
        """Обновленный метод отображения совместимости"""
        compatibilities = []

        if self.car_brand:
            compatibilities.append(f"{self.car_brand.name}")
        if self.car_models.exists():
            compatibilities.append(f"{self.car_models.count()} моделей")
        if self.car_generations.exists():
            compatibilities.append(f"{self.car_generations.count()} поколений")
        if self.car_modifications.exists():
            compatibilities.append(f"{self.car_modifications.count()} модиф.")

        return ", ".join(compatibilities) if compatibilities else "Универсальный"

    get_compatibility_display.short_description = "Совместимость"


class ProductModeration(Product):
    """Proxy-модель для раздела модерации товаров в админке."""

    class Meta:
        proxy = True
        app_label = 'moderation'
        verbose_name = "Товар на модерации"
        verbose_name_plural = "Модерация товаров"


class ProductCrossReference(models.Model):
    RELATION_TYPES = [
        ('cross', 'Cross'),
        ('analog', 'Analog'),
        ('oem', 'OEM'),
        ('replacement', 'Replacement'),
    ]

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='cross_references'
    )
    article_number = models.CharField(max_length=100, db_index=True)
    normalized_article = models.CharField(
        max_length=100,
        blank=True,
        default='',
        db_index=True,
        editable=False
    )
    brand = models.CharField(max_length=100, blank=True, default='')
    relation_type = models.CharField(
        max_length=20,
        choices=RELATION_TYPES,
        default='cross',
        db_index=True
    )
    analog_product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='incoming_cross_references'
    )
    comment = models.TextField(blank=True, default='')
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Product cross reference"
        verbose_name_plural = "Product cross references"
        ordering = ['brand', 'article_number']
        unique_together = ('product', 'normalized_article', 'brand', 'relation_type')
        indexes = [
            models.Index(fields=['normalized_article', 'is_active']),
            models.Index(fields=['product', 'relation_type']),
            models.Index(fields=['analog_product', 'is_active']),
        ]

    def save(self, *args, **kwargs):
        self.normalized_article = normalize_article_number(self.article_number)
        super().save(*args, **kwargs)

    def __str__(self):
        brand = f"{self.brand} " if self.brand else ""
        return f"{self.product} -> {brand}{self.article_number}"


class ProductImage(models.Model):
    """
    Дополнительные изображения товара
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = models.ImageField(
        _("Изображение"),
        upload_to='products/additional/'
    )
    order = models.PositiveIntegerField(
        _("Порядок отображения"),
        default=0
    )
    alt_text = models.CharField(
        _("Альтернативный текст"),
        max_length=100,
        blank=True
    )

    class Meta:
        verbose_name = _("Изображение товара")
        verbose_name_plural = _("Изображения товаров")
        ordering = ['order']

    def __str__(self):
        return f"Изображение {self.id} для {self.product.name}"

    def get_absolute_url(self):
        return reverse('shop:product_detail', kwargs={'slug': self.slug})


class ProductAttribute(models.Model):
    """
    Атрибуты товара для фильтрации (цвет, материал и т.д.)
    """
    name = models.CharField(_("Название"), max_length=100)
    slug = models.SlugField(_("URL"), max_length=100, unique=True)
    description = models.TextField(_("Описание"), blank=True)
    is_filter = models.BooleanField(
        _("Использовать в фильтрации"),
        default=True
    )
    order = models.PositiveIntegerField(_("Порядок сортировки"), default=0)

    class Meta:
        verbose_name = _("Атрибут товара")
        verbose_name_plural = _("Атрибуты товаров")
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class ProductAttributeValue(models.Model):
    """
    Значения атрибутов товара
    """
    attribute = models.ForeignKey(
        ProductAttribute,
        on_delete=models.CASCADE,
        related_name='values',
        verbose_name=_("Атрибут")
    )
    value = models.CharField(_("Значение"), max_length=100)
    slug = models.SlugField(_("URL"), max_length=100)
    products = models.ManyToManyField(
        Product,
        through='ProductAttributeThrough',
        related_name='attributes',
        verbose_name=_("Товары")
    )

    class Meta:
        verbose_name = _("Значение атрибута")
        verbose_name_plural = _("Значения атрибутов")
        ordering = ['attribute__order', 'value']
        unique_together = ('attribute', 'slug')

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class ProductAttributeThrough(models.Model):
    """
    Промежуточная модель для связи товаров и значений атрибутов
    """
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    attribute_value = models.ForeignKey(ProductAttributeValue, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('product', 'attribute_value')
        verbose_name = _("Связь товара с атрибутом")
        verbose_name_plural = _("Связи товаров с атрибутами")

    def __str__(self):
        return f"{self.product.name} - {self.attribute_value}"


####################### Автохимия и масла ######################

class OilAndChemistryDetails(models.Model):
    """Характеристики для автохимии и масел"""
    OIL_TYPES = [
        ('engine', 'Моторное масло'),
        ('transmission', 'Трансмиссионное масло'),
        ('gear', 'Масло для КПП'),
        ('hydraulic', 'Гидравлическое масло'),
        ('brake', 'Тормозная жидкость'),
        ('coolant', 'Антифриз/Охлаждающая жидкость'),
        ('adblue', 'AdBlue'),
        ('grease', 'Смазка'),
        ('cleaner', 'Очиститель'),
        ('additive', 'Присадка'),
    ]

    SEASONS = [
        ('summer', 'Летнее'),
        ('winter', 'Зимнее'),
        ('all_season', 'Всесезонное'),
    ]

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='oil_chem_details'
    )

    oil_type = models.CharField(
        _("Тип масла/химии"),
        max_length=20,
        choices=OIL_TYPES,
        db_index=True
    )

    # Основные характеристики
    viscosity = models.CharField(
        _("Вязкость"),
        max_length=50,
        blank=True,
        help_text="5W-30, 5W-40, 75W-90 и т.д."
    )

    volume = models.DecimalField(
        _("Объем"),
        max_digits=6,
        decimal_places=2,
        help_text="Объем в литрах"
    )

    season = models.CharField(
        _("Сезонность"),
        max_length=15,
        choices=SEASONS,
        blank=True
    )

    # Спецификации и допуски
    api_spec = models.CharField(
        _("Спецификация API"),
        max_length=50,
        blank=True
    )

    acea_spec = models.CharField(
        _("Спецификация ACEA"),
        max_length=50,
        blank=True
    )

    oem_approvals = models.TextField(
        _("OEM допуски"),
        blank=True,
        help_text="MB 229.5, VW 502.00/505.00 и т.д."
    )

    # Технические характеристики
    base_type = models.CharField(
        _("Основа масла"),
        max_length=20,
        choices=[
            ('mineral', 'Минеральное'),
            ('synthetic', 'Синтетическое'),
            ('semi_synthetic', 'Полусинтетическое'),
        ],
        blank=True
    )

    flash_point = models.IntegerField(
        _("Температура вспышки, °C"),
        null=True,
        blank=True
    )

    pour_point = models.IntegerField(
        _("Температура застывания, °C"),
        null=True,
        blank=True
    )

    density = models.DecimalField(
        _("Плотность, г/см³"),
        max_digits=5,
        decimal_places=3,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("Характеристика автохимии/масел")
        verbose_name_plural = _("Характеристики автохимии/масел")

    def __str__(self):
        return f"Характеристики {self.product.name}"

    def get_main_specs(self):
        """Основные характеристики для отображения"""
        specs = []
        if self.viscosity:
            specs.append(f"Вязкость: {self.viscosity}")
        if self.volume:
            specs.append(f"Объем: {self.volume}л")
        if self.base_type:
            specs.append(f"Основа: {self.get_base_type_display()}")
        return ", ".join(specs)


################ Аксессуары ########################
class AccessoryCategory(models.Model):
    """Категории аксессуаров (чехлы, коврики, аудио, освещение и т.д.)"""
    name = models.CharField("Название", max_length=100)
    slug = models.SlugField("URL", unique=True, blank=True)
    icon = models.CharField("Иконка", max_length=50, blank=True, help_text="Название иконки из Bootstrap Icons")
    # Привязка к основной категории (например, "Автоаксессуары" в Category)
    main_category = models.ForeignKey(
        'Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Основная категория",
        related_name='accessory_categories'
    )
    parent = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name="Родительская категория",
        related_name='accessory_subcategories'
    )
    image = models.ImageField("Изображение", upload_to='accessory_categories/', blank=True, null=True)
    is_active = models.BooleanField("Активна", default=True)

    class Meta:
        verbose_name = "Категория аксессуаров"
        verbose_name_plural = "Категории аксессуаров"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AccessoryBrand(models.Model):
    """Бренды аксессуаров (например, JBL, CoverKing, Philips)"""
    name = models.CharField("Название", max_length=100)
    slug = models.SlugField("URL", unique=True, blank=True)
    logo = models.ImageField("Логотип", upload_to='accessory_brands/', blank=True, null=True)
    description = models.TextField("Описание", blank=True)
    year_founded = models.PositiveIntegerField("Год основания", null=True, blank=True)
    country = models.CharField("Страна", max_length=50, blank=True)
    is_active = models.BooleanField("Активный", default=True)

    class Meta:
        verbose_name = "Бренд аксессуаров"
        verbose_name_plural = "Бренды аксессуаров"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class AccessoryProduct(models.Model):
    """
    Характеристики для автомобильных аксессуаров.
    """
    # Типы аксессуаров
    ACCESSORY_TYPES = [
        ('care_chemicals', _('Автохимия и уход')),
        ('air_freshener', _('Ароматизаторы')),
        ('organizer', _('Органайзеры')),
        ('mats', _('Коврики')),
        ('covers', _('Чехлы')),
        ('steering_wheel_cover', _('Оплетки на руль')),
        ('pillows', _('Подушки и ортопеды')),
        ('glass_films', _('Автостекла и пленки')),
        ('mudguards', _('Брызговики')),
        ('deflectors', _('Дефлекторы')),
        ('luggage', _('Багажники и боксы')),
        ('holders', _('Крепления и держатели')),
        ('phone_holder', _('Телефонные держатели')),
        ('chargers', _('Зарядные устройства')),
        ('adapters', _('Переходники')),
        ('dvr', _('Видеорегистраторы')),
        ('rear_camera', _('Камеры заднего вида')),
        ('parking_sensors', _('Парктроники')),
        ('navigator', _('Навигаторы')),
        ('multimedia', _('Мультимедиа')),
        ('key_covers', _('Чехлы на ключ')),
        ('covers_tarps', _('Тенты и накрытия')),
        ('radiator_grilles', _('Сетки радиатора')),
        ('trunk_nets', _('Сетки в багажник')),
        ('engine_heater', _('Утеплители двигателя')),
        ('antennas', _('Антенны')),
        ('sun_shades', _('Отражатели / солнцезащитные шторки')),
        ('running_boards', _('Подножки и ступеньки')),
        ('containers', _('Канистры и емкости')),
        ('fire_extinguisher', _('Огнетушители')),
        ('first_aid_kit', _('Аптечки')),
        ('emergency_kit', _('Инструменты аварийного комплекта')),
        ('winches', _('Лебёдки и тросы')),
        ('other', _('Другое')),
    ]

    # Назначение
    PURPOSE_TYPES = [
        ('car', _('Для легковых авто')),
        ('truck', _('Для грузовых авто')),
        ('moto', _('Для мотоциклов')),
        ('atv', _('Для квадроциклов')),
        ('bus', _('Для автобусов')),
        ('special', _('Для спецтехники')),
        ('universal', _('Универсальный')),
    ]

    # Материалы
    MATERIAL_TYPES = [
        ('eco_leather', _('Эко-кожа')),
        ('genuine_leather', _('Натуральная кожа')),
        ('fabric', _('Ткань')),
        ('alcantara', _('Алькантара')),
        ('polyester', _('Полиэстер')),
        ('pvc', _('ПВХ')),
        ('rubber', _('Резина')),
        ('polyurethane', _('Полиуретан')),
        ('plastic', _('Пластик')),
        ('metal', _('Металл')),
        ('foam', _('Пенополиуретан')),
        ('silicone', _('Силикон')),
        ('neoprene', _('Неопрен')),
        ('other', _('Другой')),
    ]

    # Типы питания
    POWER_TYPES = [
        ('12v', '12V'),
        ('24v', '24V'),
        ('usb', 'USB'),
        ('usb_c', 'USB-C'),
        ('cigarette_lighter', _('Прикуриватель')),
        ('solar', _('Солнечная батарея')),
        ('none', _('Без питания')),
    ]

    # Типы крепления
    MOUNTING_TYPES = [
        ('suction', _('Присоска')),
        ('double_tape', _('Двусторонний скотч')),
        ('bolts', _('На болтах')),
        ('clips', _('На клипсах')),
        ('elastic', _('На резинках')),
        ('velcro', _('На липучке')),
        ('magnetic', _('С магнитом')),
        ('deflector_insert', _('Вставка в дефлектор')),
        ('cup_holder', _('В подстаканник')),
        ('vent_mount', _('На решетку воздуховода')),
        ('other', _('Другое')),
    ]

    # Комплектация
    KIT_TYPES = [
        ('single', _('Один предмет')),
        ('pair', _('Комплект (2 шт)')),
        ('set_4', _('Комплект (4 шт)')),
        ('kit', _('Набор')),
        ('with_case', _('С чехлом')),
        ('with_mount', _('С крепежом')),
        ('with_manual', _('С инструкцией')),
    ]

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='accessory_details',
        verbose_name=_("Товар")
    )

    # Основные характеристики
    accessory_type = models.CharField(
        _("Тип аксессуара"),
        max_length=30,
        choices=ACCESSORY_TYPES,
        db_index=True
    )
    purpose = models.CharField(
        _("Назначение"),
        max_length=20,
        choices=PURPOSE_TYPES,
        default='universal'
    )
    material = models.CharField(
        _("Материал"),
        max_length=20,
        choices=MATERIAL_TYPES,
        blank=True
    )
    color = models.CharField(
        _("Цвет"),
        max_length=50,
        blank=True
    )

    # Габариты и размеры
    size = models.CharField(
        _("Размер"),
        max_length=50,
        blank=True,
        help_text=_("S, M, L, XL или конкретные размеры")
    )
    length = models.DecimalField(
        _("Длина"),
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text=_("В см")
    )
    width = models.DecimalField(
        _("Ширина"),
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text=_("В см")
    )
    height = models.DecimalField(
        _("Высота"),
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text=_("В см")
    )
    weight = models.DecimalField(
        _("Вес"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("В кг")
    )
    volume = models.DecimalField(
        _("Объем"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("В литрах")
    )

    # Для электронных аксессуаров
    power_type = models.CharField(
        _("Тип питания"),
        max_length=20,
        choices=POWER_TYPES,
        blank=True
    )
    voltage = models.CharField(
        _("Напряжение"),
        max_length=50,
        blank=True
    )
    connection_type = models.CharField(
        _("Тип подключения"),
        max_length=100,
        blank=True
    )

    # Для мультимедиа устройств
    resolution = models.CharField(
        _("Разрешение видео"),
        max_length=50,
        blank=True,
        help_text=_("720p, 1080p, 2K, 4K")
    )
    viewing_angle = models.PositiveIntegerField(
        _("Угол обзора камеры"),
        null=True,
        blank=True,
        help_text=_("В градусах")
    )
    has_wifi = models.BooleanField(
        _("Wi-Fi"),
        default=False
    )
    has_bluetooth = models.BooleanField(
        _("Bluetooth"),
        default=False
    )
    has_gps = models.BooleanField(
        _("GPS"),
        default=False
    )
    has_night_vision = models.BooleanField(
        _("Ночное видение"),
        default=False
    )

    # Крепление и монтаж
    mounting_type = models.CharField(
        _("Тип крепления"),
        max_length=20,
        choices=MOUNTING_TYPES,
        blank=True
    )
    load_capacity = models.DecimalField(
        _("Грузоподъемность"),
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text=_("В кг")
    )

    # Защита и безопасность
    ip_rating = models.CharField(
        _("Степень защиты IP"),
        max_length=10,
        blank=True,
        help_text=_("IP54, IP65, IP67")
    )
    temperature_range = models.CharField(
        _("Температурный диапазон"),
        max_length=100,
        blank=True,
        help_text=_("Например: -30°C до +80°C")
    )
    uv_protection = models.BooleanField(
        _("УФ-защита"),
        default=False
    )
    anti_slip = models.BooleanField(
        _("Антискольжение"),
        default=False
    )
    fire_resistant = models.BooleanField(
        _("Огнестойкость"),
        default=False
    )

    # Комплектация
    kit_type = models.CharField(
        _("Комплектация"),
        max_length=20,
        choices=KIT_TYPES,
        blank=True
    )
    items_count = models.PositiveIntegerField(
        _("Количество предметов"),
        null=True,
        blank=True
    )
    includes_mount = models.BooleanField(
        _("Включает крепеж"),
        default=False
    )
    includes_cables = models.BooleanField(
        _("Включает кабели"),
        default=False
    )
    includes_manual = models.BooleanField(
        _("Включает инструкцию"),
        default=True
    )

    # Дополнительные характеристики
    compatibility_notes = models.TextField(
        _("Примечания по совместимости"),
        blank=True,
        help_text=_("Особенности установки и совместимости")
    )
    features = models.TextField(
        _("Особенности"),
        blank=True,
        help_text=_("Дополнительные функции и особенности")
    )
    installation_notes = models.TextField(
        _("Примечания по установке"),
        blank=True
    )
    country_of_origin = models.CharField(
        _("Страна производства"),
        max_length=100,
        blank=True
    )
    warranty_months = models.PositiveIntegerField(
        _("Гарантия (месяцев)"),
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("Характеристика аксессуара")
        verbose_name_plural = _("Характеристики аксессуаров")

    def __str__(self):
        return f"Характеристики аксессуара: {self.product.name}"

    def get_accessory_specs_display(self):
        """Возвращает основные спецификации для отображения в списке"""
        specs = []
        if self.accessory_type:
            specs.append(self.get_accessory_type_display())
        if self.material:
            specs.append(self.get_material_display())
        if self.color:
            specs.append(self.color)
        if self.size:
            specs.append(f"Размер: {self.size}")
        return " / ".join(specs) if specs else "-"

    def get_full_specs(self):
        """Возвращает полные характеристики для детальной страницы"""
        specs = []

        if self.accessory_type:
            specs.append(f"Тип: {self.get_accessory_type_display()}")
        if self.purpose:
            specs.append(f"Назначение: {self.get_purpose_display()}")
        if self.material:
            specs.append(f"Материал: {self.get_material_display()}")
        if self.color:
            specs.append(f"Цвет: {self.color}")

        # Габариты
        if self.length and self.width:
            specs.append(f"Размеры: {self.length}×{self.width}" +
                         (f"×{self.height}" if self.height else "") + " см")
        elif self.size:
            specs.append(f"Размер: {self.size}")

        # Электроника
        if self.power_type:
            specs.append(f"Питание: {self.get_power_type_display()}")
        if self.resolution:
            specs.append(f"Разрешение: {self.resolution}")
        if self.viewing_angle:
            specs.append(f"Угол обзора: {self.viewing_angle}°")

        # Крепление
        if self.mounting_type:
            specs.append(f"Крепление: {self.get_mounting_type_display()}")
        if self.load_capacity:
            specs.append(f"Грузоподъемность: {self.load_capacity} кг")

        # Защита
        if self.ip_rating:
            specs.append(f"Защита: {self.ip_rating}")
        if self.temperature_range:
            specs.append(f"Температура: {self.temperature_range}")

        # Комплектация
        if self.kit_type:
            specs.append(f"Комплектация: {self.get_kit_type_display()}")
        if self.items_count:
            specs.append(f"Количество: {self.items_count} шт")

        return specs


class BaseCategory(models.Model):
    """
    Абстрактная базовая модель для категорий товаров.
    Содержит общие поля для всех категорий.
    """
    name = models.CharField(_("Название"), max_length=100)
    slug = models.SlugField(_("URL"), max_length=100, unique=True, blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Родительская категория"),
        related_name='children'
    )
    description = models.TextField(_("Описание"), blank=True)
    image = models.ImageField(
        _("Изображение"),
        upload_to='categories/',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(_("Активна"), default=True)
    order = models.PositiveIntegerField(_("Порядок сортировки"), default=0)

    class Meta:
        abstract = True
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class BaseBrand(models.Model):
    """
    Абстрактная базовая модель для брендов.
    Содержит общие поля для всех брендов.
    """
    name = models.CharField(_("Название"), max_length=100)
    slug = models.SlugField(_("URL"), max_length=100, unique=True, blank=True)
    logo = models.ImageField(
        _("Логотип"),
        upload_to='brands/',
        blank=True,
        null=True
    )
    description = models.TextField(_("Описание"), blank=True)
    country = models.CharField(_("Страна"), max_length=50, blank=True)
    year_founded = models.PositiveIntegerField(
        _("Год основания"),
        null=True,
        blank=True,
        validators=[MinValueValidator(1800)]
    )
    is_active = models.BooleanField(_("Активен"), default=True)

    class Meta:
        abstract = True
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# Модели для автохимии и масел
class OilAndChemistryCategory(BaseCategory):
    """Категории автохимии и масел"""
    parent = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Родительская категория"),
        related_name='oil_chemistry_subcategories'
    )
    description = models.TextField(_("Описание"), blank=True)
    image = models.ImageField(
        _("Изображение"),
        upload_to='categories/oil_chem/',
        null=True,
        blank=True
    )
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        verbose_name = _("Категория автохимии и масел")
        verbose_name_plural = _("Категории автохимии и масел")


class OilAndChemistryBrand(BaseBrand):
    """Бренды автохимии и масел"""
    logo = models.ImageField(
        _("Логотип"),
        upload_to='brands/oil_chem/',
        blank=True,
        null=True
    )
    description = models.TextField(_("Описание"), blank=True)
    country = models.CharField(_("Страна"), max_length=50, blank=True)
    is_active = models.BooleanField(_("Активен"), default=True)
    categories = models.ManyToManyField(
        Category,
        related_name='oil_chemistry_brands'
    )

    class Meta:
        verbose_name = _("Бренд автохимии и масел")
        verbose_name_plural = _("Бренды автохимии и масел")


# Модели для технического обслуживания (ТО)
class MaintenanceCategory(BaseCategory):
    """
    Категории товаров для технического обслуживания.
    Примеры: Фильтры, Ремни ГРМ, Свечи зажигания, Тормозные колодки и т.д.
    """
    parent = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='maintenance_subcategories'  # Явное имя связи
    )

    class Meta:
        verbose_name = _("Категория ТО")
        verbose_name_plural = _("Категории ТО")


class MaintenanceBrand(BaseBrand):
    """
    Бренды товаров для технического обслуживания.
    Примеры: Bosch, Mann, NGK, Brembo и т.д.
    """
    categories = models.ManyToManyField(
        Category,
        verbose_name=_("Категории"),
        blank=True,
        related_name='maintenance_brands'
    )

    class Meta:
        verbose_name = _("Бренд ТО")
        verbose_name_plural = _("Бренды ТО")


# Модели для шин и дисков
class TireAndWheelCategory(BaseCategory):
    """
    Категории шин и дисков.
    Примеры: Летние шины, Зимние шины, Литые диски, Штампованные диски и т.д.
    """
    categories = models.ManyToManyField(
        Category,
        verbose_name=_("Категории"),
        blank=True,
        related_name='tire_wheel_subcategories'
    )

    class Meta:
        verbose_name = _("Категория шин и дисков")
        verbose_name_plural = _("Категории шин и дисков")


class TireAndWheelBrand(BaseBrand):
    """
    Бренды шин и дисков.
    Примеры: Michelin, Pirelli, BBS, Alutec и т.д.
    """
    categories = models.ManyToManyField(
        Category,
        verbose_name=_("Категории"),
        blank=True,
        related_name='tire_wheel_brands'
    )

    class Meta:
        verbose_name = _("Бренд шин и дисков")
        verbose_name_plural = _("Бренды шин и дисков")


# Модели для инструментов
class ToolCategory(BaseCategory):
    """
    Категории инструментов.
    Примеры: Наборы инструментов, Гидравлика, Электроинструмент, Измерительные инструменты и т.д.
    """
    categories = models.ManyToManyField(
        Category,
        verbose_name=_("Категории"),
        blank=True,
        related_name='tool_subcategories'
    )

    class Meta:
        verbose_name = _("Категория инструментов")
        verbose_name_plural = _("Категории инструментов")


class ToolBrand(BaseBrand):
    """
    Бренды инструментов.
    Примеры: Kraftool, Jonnesway, Stahlwille, Stanley и т.д.
    """
    categories = models.ManyToManyField(
        Category,
        verbose_name=_("Категории"),
        blank=True,
        related_name='tool_brands'
    )

    class Meta:
        verbose_name = _("Бренд инструментов")
        verbose_name_plural = _("Бренды инструментов")


class ToolProduct(models.Model):
    """
    Характеристики для инструментов.
    """
    # Основные характеристики
    TOOL_TYPES = [
        ('wrench', _('Ключи и головки')),
        ('screwdriver', _('Отвертки и биты')),
        ('kit', _('Наборы инструментов')),
        ('ratchet', _('Трещотки')),
        ('extension', _('Удлинители и адаптеры')),
        ('hex', _('Шестигранники')),
        ('torx', _('Звёздочки (TORX)')),
        ('socket', _('Головки торцевые')),
        ('spark_plug', _('Свечные ключи')),
        ('torque_wrench', _('Динамометрические ключи')),
        ('pliers', _('Клещи и пассатижи')),
        ('hammer', _('Молотки и кувалды')),
        ('jack', _('Домкраты')),
        ('wheel_wrench', _('Баллонные ключи')),
        ('compressor', _('Компрессоры')),
        ('pneumatic', _('Пневмоинструмент')),
        ('electric', _('Электроинструмент')),
        ('cordless', _('Аккумуляторный инструмент')),
        ('diagnostic', _('Диагностические сканеры')),
        ('pry_bar', _('Прочные лопатки/монтажки')),
        ('press', _('Гидравлические прессы')),
        ('pump', _('Насосы ручные')),
        ('puller', _('Съемники')),
        ('winch', _('Лебедки')),
        ('light', _('Фонари и лампы')),
        ('other', _('Другое')),
    ]

    PURPOSE_TYPES = [
        ('car', _('Для легковых авто')),
        ('truck', _('Для грузовых авто')),
        ('moto', _('Для мотоциклов')),
        ('atv', _('Для квадроциклов')),
        ('special', _('Для спецтехники')),
        ('universal', _('Универсальный')),
        ('body_repair', _('Кузовной ремонт')),
        ('locksmith', _('Слесарные работы')),
        ('brake_system', _('Тормозная система')),
        ('suspension', _('Подвеска и ходовая')),
        ('engine', _('Двигатель')),
        ('fuel_system', _('Топливная система')),
        ('electric', _('Электрика')),
        ('tire_service', _('Шиномонтаж')),
        ('diagnostic', _('Диагностика')),
    ]

    DRIVE_TYPES = [
        ('1_4', '1/4"'),
        ('3_8', '3/8"'),
        ('1_2', '1/2"'),
        ('3_4', '3/4"'),
        ('1', '1"'),
    ]

    POWER_TYPES = [
        ('battery', _('Аккумулятор')),
        ('electric', _('Сетевой (220В)')),
        ('pneumatic', _('Пневматический')),
        ('hydraulic', _('Гидравлический')),
        ('manual', _('Механический')),
    ]

    MATERIAL_TYPES = [
        ('cr_v', _('Хром-ванадий (Cr-V)')),
        ('cr_mo', _('Хром-молибден (Cr-Mo)')),
        ('steel', _('Сталь')),
        ('tool_steel', _('Инструментальная сталь')),
        ('carbon_steel', _('Углеродистая сталь')),
        ('plastic_steel', _('Пластик + сталь')),
    ]

    HANDLE_TYPES = [
        ('plastic', _('Пластиковая')),
        ('rubber', _('Резиновая')),
        ('metal', _('Металлическая')),
        ('rubberized', _('Прорезиненная')),
        ('non_slip', _('Антискользящая')),
    ]

    CASE_TYPES = [
        ('plastic', _('Пластиковый')),
        ('metal', _('Металлический')),
        ('fabric', _('Тканевый')),
        ('none', _('Без кейса')),
    ]

    JACK_TYPES = [
        ('rolling', _('Подкатной')),
        ('bottle', _('Бутылочный')),
        ('rhombic', _('Ромбовый')),
        ('pneumatic_hydraulic', _('Пневмогидравлический')),
    ]

    SCANNER_TYPES = [
        ('obd2', 'OBD2'),
        ('bluetooth_obd2', 'Bluetooth OBD2'),
        ('wifi_obd2', 'Wi-Fi OBD2'),
        ('professional', _('Профессиональный')),
        ('multi_brand', _('Мультимарочный')),
        ('dealer', _('Оригинальный дилерский')),
    ]

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='tool_details',
        verbose_name=_("Товар")
    )

    # Основные характеристики
    tool_type = models.CharField(
        _("Тип инструмента"),
        max_length=20,
        choices=TOOL_TYPES,
        db_index=True
    )
    purpose = models.CharField(
        _("Назначение"),
        max_length=20,
        choices=PURPOSE_TYPES,
        default='universal',
        db_index=True
    )
    size = models.CharField(
        _("Размер"),
        max_length=50,
        blank=True,
        help_text=_("Например: 10 мм, 13 мм, 1/2”")
    )
    drive_size = models.CharField(
        _("Посадочный квадрат"),
        max_length=10,
        choices=DRIVE_TYPES,
        blank=True
    )
    profile = models.CharField(
        _("Профиль/Количество граней"),
        max_length=50,
        blank=True,
        help_text=_("Например: 6 граней, 12 граней, TORX, HEX")
    )
    thread_type = models.CharField(
        _("Тип резьбы"),
        max_length=50,
        blank=True,
        help_text=_("Например: M8, M10, метрическая, дюймовая")
    )

    # Питание и мощность
    power_type = models.CharField(
        _("Тип питания"),
        max_length=20,
        choices=POWER_TYPES,
        blank=True
    )
    voltage = models.CharField(
        _("Напряжение"),
        max_length=20,
        blank=True,
        help_text=_("Например: 12V, 18V, 20V")
    )
    battery_capacity = models.CharField(
        _("Емкость аккумулятора"),
        max_length=20,
        blank=True,
        help_text=_("Например: 2 Ah, 4 Ah")
    )
    power = models.CharField(
        _("Мощность"),
        max_length=50,
        blank=True,
        help_text=_("Например: 300 Вт, 600 Вт")
    )
    torque = models.CharField(
        _("Крутящий момент"),
        max_length=50,
        blank=True,
        help_text=_("Например: 150 Н·м, 300 Н·м")
    )
    speed = models.CharField(
        _("Скорость вращения"),
        max_length=50,
        blank=True,
        help_text=_("Например: 0-800 об/мин")
    )

    # Материалы и конструкция
    material = models.CharField(
        _("Материал"),
        max_length=20,
        choices=MATERIAL_TYPES,
        blank=True
    )
    handle_type = models.CharField(
        _("Тип рукоятки"),
        max_length=20,
        choices=HANDLE_TYPES,
        blank=True
    )
    length = models.CharField(
        _("Длина"),
        max_length=50,
        blank=True,
        help_text=_("Например: 250 мм, 300 мм")
    )
    weight = models.DecimalField(
        _("Вес инструмента"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("Вес в кг")
    )
    max_load = models.CharField(
        _("Максимальная нагрузка"),
        max_length=50,
        blank=True,
        help_text=_("Например: 100 кг, 2 т")
    )

    # Для домкратов и шиномонтажного оборудования
    jack_type = models.CharField(
        _("Тип домкрата"),
        max_length=25,
        choices=JACK_TYPES,
        blank=True
    )
    lifting_capacity = models.CharField(
        _("Грузоподъемность"),
        max_length=50,
        blank=True,
        help_text=_("Например: 2 т, 5 т, 10 т")
    )
    min_height = models.DecimalField(
        _("Минимальная высота подхвата"),
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text=_("В мм")
    )
    max_lift = models.DecimalField(
        _("Максимальная высота подъема"),
        max_digits=6,
        decimal_places=1,
        null=True,
        blank=True,
        help_text=_("В мм")
    )

    # Для диагностического оборудования
    scanner_type = models.CharField(
        _("Тип сканера"),
        max_length=20,
        choices=SCANNER_TYPES,
        blank=True
    )
    supported_protocols = models.CharField(
        _("Поддерживаемые протоколы"),
        max_length=100,
        blank=True,
        help_text=_("Например: CAN, ISO 9141, KWP2000")
    )
    compatible_brands = models.TextField(
        _("Совместимые марки авто"),
        blank=True,
        help_text=_("Список совместимых марок автомобилей")
    )

    # Комплектация
    items_count = models.PositiveIntegerField(
        _("Количество предметов в наборе"),
        null=True,
        blank=True
    )
    case_type = models.CharField(
        _("Тип кейса"),
        max_length=20,
        choices=CASE_TYPES,
        blank=True
    )
    kit_contents = models.TextField(
        _("Состав набора"),
        blank=True,
        help_text=_("Что входит в набор")
    )

    # Дополнительные характеристики
    color = models.CharField(
        _("Цвет"),
        max_length=50,
        blank=True
    )
    warranty_months = models.PositiveIntegerField(
        _("Гарантия (месяцев)"),
        null=True,
        blank=True
    )
    features = models.TextField(
        _("Особенности"),
        blank=True,
        help_text=_("Дополнительные особенности: магнитная головка, антикоррозийное покрытие и т.д.")
    )
    country_of_origin = models.CharField(
        _("Страна производства"),
        max_length=100,
        blank=True
    )

    class Meta:
        verbose_name = _("Характеристика инструмента")
        verbose_name_plural = _("Характеристики инструментов")

    def __str__(self):
        return f"Характеристики инструмента: {self.product.name}"

    def get_tool_specs_display(self):
        """Возвращает основные спецификации для отображения в списке"""
        specs = []
        if self.tool_type:
            specs.append(self.get_tool_type_display())
        if self.size:
            specs.append(self.size)
        if self.drive_size:
            specs.append(self.get_drive_size_display())
        return " / ".join(specs) if specs else "-"

    def get_full_specs(self):
        """Возвращает полные характеристики для детальной страницы"""
        specs = []

        if self.tool_type:
            specs.append(f"Тип: {self.get_tool_type_display()}")
        if self.purpose:
            specs.append(f"Назначение: {self.get_purpose_display()}")
        if self.size:
            specs.append(f"Размер: {self.size}")
        if self.drive_size:
            specs.append(f"Посадочный квадрат: {self.get_drive_size_display()}")
        if self.profile:
            specs.append(f"Профиль: {self.profile}")
        if self.material:
            specs.append(f"Материал: {self.get_material_display()}")

        if self.power_type:
            specs.append(f"Питание: {self.get_power_type_display()}")
        if self.voltage:
            specs.append(f"Напряжение: {self.voltage}")
        if self.torque:
            specs.append(f"Крутящий момент: {self.torque}")

        if self.lifting_capacity:
            specs.append(f"Грузоподъемность: {self.lifting_capacity}")
        if self.min_height and self.max_lift:
            specs.append(f"Высота подъема: {self.min_height}-{self.max_lift} мм")

        if self.items_count:
            specs.append(f"Количество предметов: {self.items_count}")
        if self.warranty_months:
            specs.append(f"Гарантия: {self.warranty_months} мес.")

        return specs


################### Автоэлектрика ##################

class AutoElectricProduct(models.Model):
    """
    Характеристики для автоэлектрики.
    """
    # Типы электрооборудования
    ELECTRIC_TYPES = [
        ('battery', _('Аккумулятор')),
        ('generator', _('Генератор')),
        ('starter', _('Стартер')),
        ('ignition_coil', _('Катушка зажигания')),
        ('spark_plug', _('Свеча зажигания')),
        ('glow_plug', _('Свеча накаливания')),
        ('sensor', _('Датчик')),
        ('relay', _('Реле')),
        ('fuse', _('Предохранитель')),
        ('switch', _('Выключатель')),
        ('connector', _('Разъем')),
        ('wire', _('Провод')),
        ('bulb', _('Лампочка')),
        ('headlight', _('Фара')),
        ('tail_light', _('Фонарь задний')),
        ('indicator', _('Поворотник')),
        ('horn', _('Клаксон')),
        ('wiring_harness', _('Жгут проводов')),
        ('control_unit', _('Блок управления')),
        ('alternator', _('Альтернатор')),
        ('voltage_regulator', _('Регулятор напряжения')),
        ('solenoid', _('Соленоид')),
        ('motor', _('Электродвигатель')),
        ('heater', _('Нагреватель')),
        ('fan', _('Вентилятор')),
        ('other', _('Другое')),
    ]

    # Напряжение
    VOLTAGE_TYPES = [
        ('12v', '12V'),
        ('24v', '24V'),
        ('6v', '6V'),
        ('48v', '48V'),
        ('other', _('Другое')),
    ]

    # Полярность аккумулятора
    BATTERY_POLARITY = [
        ('direct', _('Прямая')),
        ('reverse', _('Обратная')),
        ('universal', _('Универсальная')),
    ]

    # Типы клемм аккумулятора
    TERMINAL_TYPES = [
        ('standard', _('Стандартные')),
        ('side', _('Боковые')),
        ('universal', _('Универсальные')),
    ]

    # Технологии аккумуляторов
    BATTERY_TECHNOLOGY = [
        ('lead_acid', _('Свинцово-кислотный')),
        ('agm', 'AGM'),
        ('gel', _('Гелевый')),
        ('efb', 'EFB'),
        ('calcium', _('Кальциевый')),
        ('hybrid', _('Гибридный')),
    ]

    # Классы мощности ламп
    BULB_TYPES = [
        ('halogen', _('Галогенная')),
        ('xenon', _('Ксеноновая')),
        ('led', _('Светодиодная')),
        ('incandescent', _('Лампа накаливания')),
    ]

    # Цоколи ламп
    BULB_BASE_TYPES = [
        ('h1', 'H1'),
        ('h3', 'H3'),
        ('h4', 'H4'),
        ('h7', 'H7'),
        ('h11', 'H11'),
        ('hb3', 'HB3'),
        ('hb4', 'HB4'),
        ('p21w', 'P21W'),
        ('w5w', 'W5W'),
        ('t10', 'T10'),
        ('ba15s', 'BA15S'),
        ('py21w', 'PY21W'),
        ('other', _('Другой')),
    ]

    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='auto_electric_details',
        verbose_name=_("Товар")
    )

    # Основные характеристики
    electric_type = models.CharField(
        _("Тип электрооборудования"),
        max_length=20,
        choices=ELECTRIC_TYPES,
        db_index=True
    )
    voltage = models.CharField(
        _("Напряжение"),
        max_length=10,
        choices=VOLTAGE_TYPES,
        default='12v'
    )
    current = models.DecimalField(
        _("Сила тока"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_("В Амперах (А)")
    )
    power = models.CharField(
        _("Мощность"),
        max_length=50,
        blank=True,
        help_text=_("Например: 60W, 100W")
    )
    resistance = models.CharField(
        _("Сопротивление"),
        max_length=50,
        blank=True,
        help_text=_("В Омах (Ω)")
    )

    # Характеристики для аккумуляторов
    capacity = models.PositiveIntegerField(
        _("Емкость аккумулятора"),
        null=True,
        blank=True,
        help_text=_("В Ач (Ампер-часах)")
    )
    cold_cranking_amps = models.PositiveIntegerField(
        _("Пусковой ток (CCA)"),
        null=True,
        blank=True,
        help_text=_("Ток холодной прокрутки")
    )
    battery_technology = models.CharField(
        _("Технология аккумулятора"),
        max_length=20,
        choices=BATTERY_TECHNOLOGY,
        blank=True
    )
    polarity = models.CharField(
        _("Полярность"),
        max_length=20,
        choices=BATTERY_POLARITY,
        blank=True
    )
    terminal_type = models.CharField(
        _("Тип клемм"),
        max_length=20,
        choices=TERMINAL_TYPES,
        blank=True
    )
    dimensions = models.CharField(
        _("Габариты (ДxШxВ)"),
        max_length=50,
        blank=True,
        help_text=_("В мм")
    )

    # Характеристики для генераторов и стартеров
    rotation_direction = models.CharField(
        _("Направление вращения"),
        max_length=50,
        blank=True,
        help_text=_("По часовой, против часовой")
    )
    rotation_speed = models.PositiveIntegerField(
        _("Скорость вращения"),
        null=True,
        blank=True,
        help_text=_("В об/мин")
    )
    number_of_teeth = models.PositiveIntegerField(
        _("Количество зубьев"),
        null=True,
        blank=True
    )
    bearing_type = models.CharField(
        _("Тип подшипника"),
        max_length=100,
        blank=True
    )

    # Характеристики для ламп
    bulb_type = models.CharField(
        _("Тип лампы"),
        max_length=20,
        choices=BULB_TYPES,
        blank=True
    )
    bulb_base = models.CharField(
        _("Тип цоколя"),
        max_length=20,
        choices=BULB_BASE_TYPES,
        blank=True
    )
    light_temperature = models.PositiveIntegerField(
        _("Цветовая температура"),
        null=True,
        blank=True,
        help_text=_("В Кельвинах (K)")
    )
    lumen = models.PositiveIntegerField(
        _("Световой поток"),
        null=True,
        blank=True,
        help_text=_("В Люменах (lm)")
    )
    beam_pattern = models.CharField(
        _("Тип пучка света"),
        max_length=50,
        blank=True,
        help_text=_("Ближний свет, дальний свет, противотуманный")
    )

    # Характеристики для датчиков
    sensor_type = models.CharField(
        _("Тип датчика"),
        max_length=100,
        blank=True,
        help_text=_("Датчик температуры, давления, положения и т.д.")
    )
    measurement_range = models.CharField(
        _("Диапазон измерений"),
        max_length=100,
        blank=True
    )
    output_signal = models.CharField(
        _("Выходной сигнал"),
        max_length=50,
        blank=True,
        help_text=_("Аналоговый, цифровой, PWM")
    )
    connection_type = models.CharField(
        _("Тип подключения"),
        max_length=100,
        blank=True,
        help_text=_("Разъем, клеммы, провода")
    )

    # Совместимость и установка
    oem_number = models.CharField(
        _("OEM номер"),
        max_length=100,
        blank=True,
        help_text=_("Оригинальный номер производителя")
    )
    connector_type = models.CharField(
        _("Тип разъема"),
        max_length=100,
        blank=True
    )
    pin_count = models.PositiveIntegerField(
        _("Количество контактов"),
        null=True,
        blank=True
    )
    wire_length = models.CharField(
        _("Длина провода"),
        max_length=50,
        blank=True,
        help_text=_("В метрах или мм")
    )
    wire_cross_section = models.CharField(
        _("Сечение провода"),
        max_length=50,
        blank=True,
        help_text=_("В мм²")
    )
    insulation_class = models.CharField(
        _("Класс изоляции"),
        max_length=50,
        blank=True
    )
    ip_rating = models.CharField(
        _("Степень защиты IP"),
        max_length=10,
        blank=True,
        help_text=_("Например: IP65, IP67")
    )

    # Дополнительные характеристики
    operating_temperature = models.CharField(
        _("Рабочая температура"),
        max_length=100,
        blank=True,
        help_text=_("Диапазон рабочих температур")
    )
    protection_features = models.TextField(
        _("Защитные функции"),
        blank=True,
        help_text=_("Защита от перегрузки, короткого замыкания и т.д.")
    )
    certification = models.CharField(
        _("Сертификация"),
        max_length=200,
        blank=True,
        help_text=_("Сертификаты качества и безопасности")
    )
    installation_notes = models.TextField(
        _("Примечания по установке"),
        blank=True
    )

    class Meta:
        verbose_name = _("Характеристика автоэлектрики")
        verbose_name_plural = _("Характеристики автоэлектрики")

    def __str__(self):
        return f"Характеристики автоэлектрики: {self.product.name}"

    def get_electric_specs_display(self):
        """Возвращает основные спецификации для отображения в списке"""
        specs = []
        if self.electric_type:
            specs.append(self.get_electric_type_display())
        if self.voltage:
            specs.append(self.get_voltage_display())
        if self.capacity:
            specs.append(f"{self.capacity}Ач")
        if self.cold_cranking_amps:
            specs.append(f"{self.cold_cranking_amps}CCA")
        if self.bulb_type:
            specs.append(self.get_bulb_type_display())
        if self.bulb_base:
            specs.append(self.get_bulb_base_display())
        return " / ".join(specs) if specs else "-"

    def get_full_specs(self):
        """Возвращает полные характеристики для детальной страницы"""
        specs = []

        if self.electric_type:
            specs.append(f"Тип: {self.get_electric_type_display()}")
        if self.voltage:
            specs.append(f"Напряжение: {self.get_voltage_display()}")
        if self.current:
            specs.append(f"Сила тока: {self.current} А")
        if self.power:
            specs.append(f"Мощность: {self.power}")

        # Специфичные для аккумуляторов
        if self.capacity:
            specs.append(f"Емкость: {self.capacity} Ач")
        if self.cold_cranking_amps:
            specs.append(f"Пусковой ток: {self.cold_cranking_amps} CCA")
        if self.battery_technology:
            specs.append(f"Технология: {self.get_battery_technology_display()}")
        if self.polarity:
            specs.append(f"Полярность: {self.get_polarity_display()}")

        # Для ламп
        if self.bulb_type:
            specs.append(f"Тип лампы: {self.get_bulb_type_display()}")
        if self.bulb_base:
            specs.append(f"Цоколь: {self.get_bulb_base_display()}")
        if self.light_temperature:
            specs.append(f"Цветовая температура: {self.light_temperature} K")
        if self.lumen:
            specs.append(f"Световой поток: {self.lumen} лм")

        # Для датчиков
        if self.sensor_type:
            specs.append(f"Тип датчика: {self.sensor_type}")
        if self.measurement_range:
            specs.append(f"Диапазон: {self.measurement_range}")

        # Общие
        if self.connector_type:
            specs.append(f"Разъем: {self.connector_type}")
        if self.ip_rating:
            specs.append(f"Защита: {self.ip_rating}")
        if self.operating_temperature:
            specs.append(f"Температура: {self.operating_temperature}")

        return specs


# Модели для автоэлектрики
class AutoElectricCategory(BaseCategory):
    """
    Категории автоэлектрики.
    Примеры: Аккумуляторы, Генераторы, Стартеры, Проводка и т.д.
    """
    categories = models.ManyToManyField(
        Category,
        verbose_name=_("Категории"),
        blank=True,
        related_name='auto_electric_subcategories'
    )

    class Meta:
        verbose_name = _("Категория автоэлектрики")
        verbose_name_plural = _("Категории автоэлектрики")


class AutoElectricBrand(BaseBrand):
    """
    Бренды автоэлектрики.
    Примеры: Varta, Bosch, Denso, Valeo и т.д.
    """
    categories = models.ManyToManyField(
        Category,
        verbose_name=_("Категории"),
        blank=True,
        related_name='auto_electric_brands'
    )

    class Meta:
        verbose_name = _("Бренд автоэлектрики")
        verbose_name_plural = _("Бренды автоэлектрики")


class PartSubcategory(models.Model):
    name = models.CharField("Название подкатегории", max_length=100)
    slug = models.SlugField("URL", unique=True)
    parent_category = models.ForeignKey(
        'Category',
        on_delete=models.CASCADE,
        related_name='part_subcategories',
        verbose_name="Основная категория"
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Родительская подкатегория"
    )

    class Meta:
        verbose_name = "Подкатегория запчастей"
        verbose_name_plural = "Подкатегории запчастей"
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_self_and_descendant_ids(self):
        """Возвращает id этой подкатегории и всех потомков (для фильтрации товаров)."""
        ids = [self.id]
        stack = [self.id]
        while stack:
            current_id = stack.pop()
            children = PartSubcategory.objects.filter(parent_id=current_id).values_list('id', flat=True)
            for cid in children:
                ids.append(cid)
                stack.append(cid)
        return ids


# Система отзывов


class Review(models.Model):
    product = models.ForeignKey(
        'shop.Product',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_("Товар")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Пользователь")
    )
    rating = models.PositiveSmallIntegerField(
        _("Оценка"),
        choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')],
        default=5
    )
    comment = models.TextField(
        _("Комментарий"),
        blank=True
    )
    created_at = models.DateTimeField(
        _("Дата создания"),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _("Дата обновления"),
        auto_now=True
    )
    is_published = models.BooleanField(
        _("Опубликован"),
        default=True
    )
    image = models.ImageField(upload_to='review_images/', blank=True, null=True)

    class Meta:
        verbose_name = _("Отзыв")
        verbose_name_plural = _("Отзывы")
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # Один пользователь - один отзыв на товар

    def __str__(self):
        return f"Отзыв на {self.product.name} от {self.user}"

    @property
    def helpful_yes(self):
        """Количество голосов 'полезно' для этого отзыва"""
        return self.feedback.filter(helpful=True).count()

    @property
    def helpful_no(self):
        """Количество голосов 'не полезно' для этого отзыва"""
        return self.feedback.filter(helpful=False).count()


class ReviewFeedback(models.Model):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    helpful = models.BooleanField()  # True - полезно, False - нет
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['review', 'user']


class ProductClick(models.Model):
    """Статистика кликов по товарам"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='clicks')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, db_index=True)
    ip_address = models.GenericIPAddressField()
    referrer = models.URLField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['product', 'timestamp']),
            models.Index(fields=['session_key', 'timestamp']),
        ]


class ProductView(models.Model):
    """Статистика просмотров товаров"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='view_stats')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    duration = models.PositiveIntegerField(default=0)  # Длительность просмотра в секундах

    class Meta:
        indexes = [
            models.Index(fields=['product', 'timestamp']),
        ]


class MaintenanceKit(models.Model):
    """Комплект для технического обслуживания"""
    name = models.CharField(_("Название комплекта"), max_length=200)
    description = models.TextField(_("Описание"), blank=True)
    vehicle_type = models.CharField(_("Тип транспорта"), max_length=20, choices=Product.VEHICLE_TYPES)
    car_brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE, null=True, blank=True)
    car_models = models.ManyToManyField(CarModel, blank=True)
    price = models.DecimalField(_("Цена комплекта"), max_digits=10, decimal_places=2)
    old_price = models.DecimalField(_("Старая цена"), max_digits=10, decimal_places=2, null=True, blank=True)
    products = models.ManyToManyField(Product, through='MaintenanceKitProduct')
    is_active = models.BooleanField(_("Активен"), default=True)
    image = models.ImageField(upload_to='maintenance_kits/', null=True, blank=True)
    created_at = models.DateTimeField(_("Дата создания"), auto_now_add=True, null=True, blank=True)

    def calculate_price(self):
        """Пересчет цены комплекта на основе товаров"""
        total = 0
        for kit_product in self.maintenancekitproduct_set.all():
            total += kit_product.product.price * kit_product.quantity
        self.price = total
        return total

    def get_absolute_url(self):
        return reverse('maintenance:kit_detail', kwargs={'pk': self.pk})

    def get_products_by_type(self):
        """Группировка товаров по типам"""
        products_by_type = {}
        for kit_product in self.maintenancekitproduct_set.all():
            if kit_product.product.maintenance_type not in products_by_type:
                products_by_type[kit_product.product.maintenance_type] = []
            products_by_type[kit_product.product.maintenance_type].append(kit_product)
        return products_by_type

    class Meta:
        verbose_name = _("Комплект ТО")
        verbose_name_plural = _("Комплекты ТО")


class MaintenanceKitProduct(models.Model):
    """Связь товаров с комплектами ТО"""
    kit = models.ForeignKey(MaintenanceKit, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(_("Количество"), default=1)
    is_required = models.BooleanField(_("Обязательный"), default=True)

    class Meta:
        unique_together = ['kit', 'product']


################### Модели для характеристик шин и дисков ##################

class TireDiameter(models.Model):
    """Диаметр шин"""
    value = models.PositiveIntegerField(_("Диаметр (дюймы)"))

    class Meta:
        verbose_name = _("Диаметр шины")
        verbose_name_plural = _("Диаметры шин")
        ordering = ['value']

    def __str__(self):
        return f"{self.value}″"


class TireSeasonality(models.Model):
    """Сезонность шин"""
    name = models.CharField(_("Название"), max_length=50)
    code = models.CharField(_("Код"), max_length=20, unique=True)

    class Meta:
        verbose_name = _("Сезонность шины")
        verbose_name_plural = _("Сезонности шин")

    def __str__(self):
        return self.name


class TireProfileWidth(models.Model):
    """Ширина профиля шин"""
    value = models.PositiveIntegerField(_("Ширина (мм)"))

    class Meta:
        verbose_name = _("Ширина профиля шины")
        verbose_name_plural = _("Ширины профилей шин")
        ordering = ['value']

    def __str__(self):
        return f"{self.value} мм"


class TireProfileHeight(models.Model):
    """Высота профиля шин"""
    value = models.PositiveIntegerField(_("Высота (%)"))

    class Meta:
        verbose_name = _("Высота профиля шины")
        verbose_name_plural = _("Высоты профилей шин")
        ordering = ['value']

    def __str__(self):
        return f"{self.value}%"


class TireLoadIndex(models.Model):
    """Индекс нагрузки шин"""
    value = models.CharField(_("Значение"), max_length=10, unique=True)
    description = models.CharField(_("Описание"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("Индекс нагрузки")
        verbose_name_plural = _("Индексы нагрузки")
        ordering = ['value']

    def __str__(self):
        return self.value


class TireSpeedIndex(models.Model):
    """Индекс скорости шин"""
    value = models.CharField(_("Значение"), max_length=5, unique=True)
    description = models.CharField(_("Описание"), max_length=100, blank=True)

    class Meta:
        verbose_name = _("Индекс скорости")
        verbose_name_plural = _("Индексы скорости")
        ordering = ['value']

    def __str__(self):
        return self.value


class WheelDiameter(models.Model):
    """Диаметр дисков"""
    value = models.PositiveIntegerField(_("Диаметр (дюймы)"))

    class Meta:
        verbose_name = _("Диаметр диска")
        verbose_name_plural = _("Диаметры дисков")
        ordering = ['value']

    def __str__(self):
        return f"{self.value}″"


class WheelWidth(models.Model):
    """Ширина дисков"""
    value = models.DecimalField(_("Ширина (дюймы)"), max_digits=3, decimal_places=1)

    class Meta:
        verbose_name = _("Ширина диска")
        verbose_name_plural = _("Ширины дисков")
        ordering = ['value']

    def __str__(self):
        return f"{self.value}″"


class WheelOffsetType(models.Model):
    """Тип вылета дисков"""
    name = models.CharField(_("Название"), max_length=50)
    code = models.CharField(_("Код"), max_length=20, unique=True)

    class Meta:
        verbose_name = _("Тип вылета диска")
        verbose_name_plural = _("Типы вылетов дисков")

    def __str__(self):
        return self.name


class WheelType(models.Model):
    """Тип дисков"""
    name = models.CharField(_("Название"), max_length=50)
    code = models.CharField(_("Код"), max_length=20, unique=True)

    class Meta:
        verbose_name = _("Тип диска")
        verbose_name_plural = _("Типы дисков")

    def __str__(self):
        return self.name


class WheelPCD(models.Model):
    """PCD (Pitch Circle Diameter)"""
    value = models.CharField(_("PCD"), max_length=50)

    class Meta:
        verbose_name = _("PCD диска")
        verbose_name_plural = _("PCD дисков")

    def __str__(self):
        return self.value


class WheelCenterBore(models.Model):
    """Диаметр центрального отверстия (DIA)"""
    value = models.DecimalField(_("DIA (мм)"), max_digits=5, decimal_places=1)

    class Meta:
        verbose_name = _("Диаметр центрального отверстия")
        verbose_name_plural = _("Диаметры центральных отверстий")
        ordering = ['value']

    def __str__(self):
        return f"{self.value} мм"


################### Основные модели шин и дисков ##################

class TireProduct(models.Model):
    """
    Характеристики шин
    """
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='tire_details',
        verbose_name=_("Товар")
    )

    # Основные характеристики (ForeignKey вместо прямых полей)
    diameter = models.ForeignKey(
        TireDiameter,
        on_delete=models.PROTECT,
        verbose_name=_("Диаметр")
    )
    seasonality = models.ForeignKey(
        TireSeasonality,
        on_delete=models.PROTECT,
        verbose_name=_("Сезонность")
    )
    profile_width = models.ForeignKey(
        TireProfileWidth,
        on_delete=models.PROTECT,
        verbose_name=_("Ширина профиля")
    )
    profile_height = models.ForeignKey(
        TireProfileHeight,
        on_delete=models.PROTECT,
        verbose_name=_("Высота профиля")
    )
    has_spikes = models.BooleanField(
        _("Шипы"),
        default=False
    )

    # Дополнительные характеристики
    load_index = models.ForeignKey(
        'TireLoadIndex',
        on_delete=models.SET_NULL,
        verbose_name=_("Индекс нагрузки"),
        blank=True,
        null=True,
    )
    speed_index = models.ForeignKey(
        'TireSpeedIndex',
        on_delete=models.SET_NULL,
        verbose_name=_("Индекс скорости"),
        blank=True,
        null=True,
    )
    run_flat = models.BooleanField(
        _("RunFlat технология"),
        default=False
    )

    # Методы для удобного отображения
    def get_size_display(self):
        """Отображает размер в стандартном формате"""
        return f"{self.profile_width.value}/{self.profile_height.value}R{self.diameter.value}"

    def get_full_name(self):
        """Полное название шины"""
        season_display = self.seasonality.name
        spikes_display = "шипованные" if self.has_spikes else "нешипованные"
        return f"{self.get_size_display()} {season_display} {spikes_display}"

    class Meta:
        verbose_name = _("Характеристика шины")
        verbose_name_plural = _("Характеристики шин")

    def __str__(self):
        return f"{self.get_size_display()} - {self.product.name}"


class WheelProduct(models.Model):
    """
    Характеристики дисков
    """
    product = models.OneToOneField(
        Product,
        on_delete=models.CASCADE,
        related_name='wheel_details',
        verbose_name=_("Товар")
    )

    # Основные характеристики (ForeignKey вместо прямых полей)
    diameter = models.ForeignKey(
        WheelDiameter,
        on_delete=models.PROTECT,
        verbose_name=_("Диаметр")
    )
    width = models.ForeignKey(
        WheelWidth,
        on_delete=models.PROTECT,
        verbose_name=_("Ширина")
    )
    offset_type = models.ForeignKey(
        WheelOffsetType,
        on_delete=models.PROTECT,
        verbose_name=_("Тип вылета")
    )
    offset_value = models.IntegerField(
        _("Значение вылета (ET)"),
        help_text=_("Например: 35, 40, 45")
    )
    wheel_type = models.ForeignKey(
        WheelType,
        on_delete=models.PROTECT,
        verbose_name=_("Тип диска")
    )

    # Технические параметры
    pcd = models.ForeignKey(
        WheelPCD,
        on_delete=models.PROTECT,
        verbose_name=_("PCD")
    )
    center_bore = models.ForeignKey(
        WheelCenterBore,
        on_delete=models.PROTECT,
        verbose_name=_("Диаметр центрального отверстия (DIA)")
    )

    # Дополнительные характеристики
    bolt_count = models.PositiveIntegerField(
        _("Количество болтов"),
        null=True,
        blank=True
    )
    bolt_spacing = models.DecimalField(
        _("Расстояние между болтами (мм)"),
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )

    def get_offset_display(self):
        """Отображает вылет в правильном формате"""
        return f"ET{self.offset_value} ({self.offset_type.name})"

    def get_full_specs(self):
        """Полные технические характеристики"""
        return f"{self.diameter.value}×{self.width.value} {self.get_offset_display()} PCD:{self.pcd.value} DIA:{self.center_bore.value}мм"

    class Meta:
        verbose_name = _("Характеристика диска")
        verbose_name_plural = _("Характеристики дисков")

    def __str__(self):
        return f"{self.diameter.value}×{self.width.value} - {self.product.name}"


# ==================== Бренды товаров ====================

class ProductBrand(BaseSlugModel):
    """
    Бренд товара (производитель запчасти/аксессуара).
    Отличается от CarBrand/TruckBrand — это бренд самого товара, а не транспортного средства.
    Примеры: Bosch, Gates, NGK, Philips, Castrol.
    """
    logo = models.ImageField(
        _("Логотип"),
        upload_to='product_brands/',
        blank=True,
        null=True
    )
    country = models.CharField(_("Страна"), max_length=100, blank=True)
    description = models.TextField(_("Описание"), blank=True)
    is_active = models.BooleanField(_("Активен"), default=True)
    categories = models.ManyToManyField(
        Category,
        through='ProductBrandCategoryRelation',
        verbose_name=_("Категории"),
        blank=True,
        related_name='product_brands'
    )

    class Meta:
        verbose_name = _("Бренд товара")
        verbose_name_plural = _("Бренды товаров")
        ordering = ['name']

    def get_absolute_url(self):
        return reverse('shop:product_brand_detail', kwargs={'slug': self.slug})


class ProductBrandCategoryRelation(models.Model):
    """Связь бренда товара с категорией/подкатегорией"""
    brand = models.ForeignKey(
        ProductBrand,
        on_delete=models.CASCADE,
        related_name='category_relations',
        verbose_name=_("Бренд")
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name='product_brand_relations',
        verbose_name=_("Категория")
    )
    is_active = models.BooleanField(_("Активна"), default=True)

    class Meta:
        unique_together = ('brand', 'category')
        verbose_name = _("Привязка бренда к категории")
        verbose_name_plural = _("Привязки брендов к категориям")

    def __str__(self):
        return f"{self.brand.name} → {self.category.name}"


class SiteSettings(models.Model):
    """Настройки сайта: контакты, реквизиты компании. Singleton — всегда одна запись."""
    company_name = models.CharField(_("Название компании"), max_length=255, default="LINKAVTO")
    inn = models.CharField(_("ИНН"), max_length=12, blank=True, default="")
    email = models.EmailField(_("Email"), blank=True, default="")
    phone = models.CharField(_("Телефон"), max_length=30, blank=True, default="")
    phone_display = models.CharField(
        _("Телефон (отображение)"), max_length=30, blank=True, default="",
        help_text=_("Например: +7 (999) 999-99-99")
    )

    class Meta:
        verbose_name = _("Настройки сайта")
        verbose_name_plural = _("Настройки сайта")

    def __str__(self):
        return "Настройки сайта"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class SiteDocument(models.Model):
    DOCUMENT_TYPES = [
        ('privacy', _('Политика конфиденциальности')),
        ('personal_data', _('Обработка персональных данных')),
        ('offer', _('Публичная оферта')),
        ('buyer_rules', _('Правила покупки')),
        ('seller_rules', _('Правила продажи')),
        ('tech_recommendations', _('Рекомендуемые технологии')),
        ('terms', _('Пользовательское соглашение')),
        ('return_policy', _('Условия возврата')),
    ]

    doc_type = models.CharField(
        _("Тип документа"), max_length=30, choices=DOCUMENT_TYPES, unique=True
    )
    title = models.CharField(_("Заголовок"), max_length=255)
    content = models.TextField(_("Содержание"), blank=True, default="")
    file = models.FileField(
        _("Файл документа"), upload_to="documents/", blank=True, null=True,
        help_text=_("PDF, DOC и т.д. Если загружен файл — на странице появится кнопка скачивания")
    )
    updated_at = models.DateTimeField(_("Обновлён"), auto_now=True)
    is_active = models.BooleanField(_("Активен"), default=True)

    class Meta:
        verbose_name = _("Документ сайта")
        verbose_name_plural = _("Документы сайта")
        ordering = ['doc_type']

    def __str__(self):
        return self.get_doc_type_display()


class CarouselSlide(models.Model):
    STATUS_CHOICES = [
        ('none', _('Без статуса')),
        ('ad', _('Реклама')),
    ]

    title = models.CharField(_("Название"), max_length=200)
    image = models.ImageField(_("Изображение"), upload_to='carousel/')
    url = models.CharField(_("Ссылка"), max_length=500, blank=True, default='',
                           help_text=_("URL для перехода при клике на слайд"))
    status = models.CharField(_("Статус"), max_length=10, choices=STATUS_CHOICES, default='none')
    is_active = models.BooleanField(_("Активен"), default=True)
    order = models.PositiveIntegerField(_("Порядок"), default=0)
    created_at = models.DateTimeField(_("Создан"), auto_now_add=True)

    class Meta:
        verbose_name = _("Слайд карусели")
        verbose_name_plural = _("Слайды карусели")
        ordering = ['order', 'created_at']

    def __str__(self):
        return self.title
