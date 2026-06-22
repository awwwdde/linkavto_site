from django.contrib import admin
from django.utils import timezone
from django.utils.safestring import mark_safe
from django import forms
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.db import models
from ckeditor_uploader.widgets import CKEditorUploadingWidget

from .models import (
    CarType, CarBrand, CarModel, CarGeneration,
    TruckType, TruckBrand, TruckModel, TruckGeneration,
    MotoType, MotoBrand, MotoModel, MotoGeneration,
    SpecialType, SpecialBrand, SpecialModel, SpecialGeneration,
    AccessoryCategory, AccessoryBrand,
    ManufacturerCategoryRelation,
    CarBrandTypeRelation, CarBrandCategoryRelation,
    TruckBrandTypeRelation, TruckBrandCategoryRelation,
    MotoBrandTypeRelation, MotoBrandCategoryRelation,
    SpecialBrandTypeRelation, SpecialBrandCategoryRelation,
    Category, Manufacturer, Product, ProductImage, PartSubcategory,
    ProductAttribute, ProductAttributeValue, OilAndChemistryCategory,
    OilAndChemistryBrand, MaintenanceCategory, MaintenanceBrand, TireAndWheelCategory, MaintenanceKit,
    TireAndWheelBrand, ToolCategory, ToolBrand, AutoElectricCategory, AutoElectricBrand, MaintenanceKitProduct,
    CategoryHierarchyModelChoiceField, ParentCategoryHierarchyModelChoiceField,
    CategoryHierarchySelect2Field, CategoryHierarchyMultipleSelect2Field, TireProduct, WheelProduct, TireDiameter,
    TireSeasonality, TireProfileWidth, TireProfileHeight, WheelDiameter, WheelWidth, WheelOffsetType, WheelType,
    WheelPCD, OilAndChemistryDetails, ToolProduct, AutoElectricProduct, AccessoryProduct,
    WheelCenterBore, Tag, SpecialModification, CarModification, MotoModification, TruckModification,
    ProductBrand, ProductBrandCategoryRelation,
    TireLoadIndex, TireSpeedIndex,
    CarouselSlide,
    SiteSettings, SiteDocument,
    CategoryRequest,
    ProductCrossReference,
)


class ImagePreviewMixin:
    """Миксин для отображения изображений категорий"""

    def get_image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" style="object-fit: contain;" />')
        return "-"

    get_image_preview.short_description = _("Изображение")


class LogoPreviewMixin:
    """Миксин для отображения логотипов брендов"""

    def get_logo_preview(self, obj):
        if obj.logo:
            return mark_safe(f'<img src="{obj.logo.url}" width="100" style="object-fit: contain;" />')
        return "-"

    get_logo_preview.short_description = _("Логотип")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'parent', 'show_in', 'is_active',
        'show_brands', 'order', 'brand_count', 'icon_preview'
    )
    list_filter = ('show_in', 'is_active', 'parent', 'show_brands')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('order', 'is_active')

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'parent', 'show_in', 'is_active', 'order')
        }),
        (_('Дополнительно'), {
            'fields': ('icon', 'image', 'description', 'show_brands')
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Для поля parent показываем иерархию категорий
        if db_field.name == "parent":
            # Исключаем текущую категорию и её потомков из возможных родителей
            # чтобы избежать циклических ссылок
            queryset = Category.objects.all()

            # Если редактируем существующую категорию, исключаем её и её потомков
            if request.resolver_match and request.resolver_match.kwargs.get('object_id'):
                current_id = request.resolver_match.kwargs['object_id']
                try:
                    current_category = Category.objects.get(pk=current_id)
                    # Находим всех потомков текущей категории
                    descendants = self.get_descendants(current_category)
                    exclude_ids = [current_category.id] + [desc.id for desc in descendants]
                    queryset = queryset.exclude(id__in=exclude_ids)
                except Category.DoesNotExist:
                    pass

            kwargs['queryset'] = queryset.select_related('parent', 'parent__parent')
            return ParentCategoryHierarchyModelChoiceField(
                queryset=kwargs['queryset'],
                required=False,  # parent может быть пустым
                label=db_field.verbose_name,
                empty_label="--- Корневая категория ---"
            )

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_descendants(self, category):
        """Рекурсивно получает всех потомков категории"""
        descendants = []
        children = Category.objects.filter(parent=category)
        for child in children:
            descendants.append(child)
            descendants.extend(self.get_descendants(child))
        return descendants

    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<i class="bi bi-{}" style="font-size: 18px;"></i>', obj.icon)
        return "-"

    icon_preview.short_description = _("Иконка")

    def brand_count(self, obj):
        """Показывает количество брендов, связанных с категорией, если show_brands=True"""
        if not obj.show_brands:
            return "-"

        if obj.show_in == 'cars':
            return obj.car_brands_list().count()
        elif obj.show_in == 'trucks':
            return obj.truck_brands_list().count()
        elif obj.show_in == 'moto':
            return obj.moto_brands_list().count()
        elif obj.show_in == 'special':
            return obj.special_brands_list().count()
        return "-"

    brand_count.short_description = _("Бренды")

    # Оптимизация запросов для списка категорий
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('parent', 'parent__parent')


@admin.register(Manufacturer)
class ManufacturerAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'is_active')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'country')
    readonly_fields = ('logo_preview',)

    def logo_preview(self, obj):
        if obj.logo:
            return mark_safe(f'<img src="{obj.logo.url}" width="100" />')
        return "-"

    logo_preview.short_description = _("Логотип")


class ProductBrandCategoryRelationInline(admin.TabularInline):
    model = ProductBrandCategoryRelation
    extra = 1
    fields = ('category', 'is_active')

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            kwargs['queryset'] = Category.objects.all().select_related('parent', 'parent__parent')
            return CategoryHierarchySelect2Field(
                queryset=kwargs['queryset'],
                required=not db_field.blank,
                label=db_field.verbose_name,
                empty_label="---------",
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(ProductBrand)
class ProductBrandAdmin(LogoPreviewMixin, admin.ModelAdmin):
    list_display = ('name', 'slug', 'country', 'is_active', 'get_logo_preview', 'product_count')
    list_filter = ('is_active', 'country')
    search_fields = ('name', 'slug', 'country')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)
    readonly_fields = ('get_logo_preview',)
    inlines = [ProductBrandCategoryRelationInline]

    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'is_active')
        }),
        (_('Детали'), {
            'fields': ('logo', 'get_logo_preview', 'country', 'description')
        }),
    )

    def product_count(self, obj):
        return obj.products.count()

    product_count.short_description = _("Кол-во товаров")


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'order', 'alt_text', 'get_image_preview')
    readonly_fields = ('get_image_preview',)

    def get_image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" />')
        return "-"

    get_image_preview.short_description = _("Превью")


class ProductAttributeInline(admin.TabularInline):
    model = Product.attributes.through
    extra = 1
    autocomplete_fields = ['ProductAttributeValue']
    verbose_name = _("Атрибут")
    verbose_name_plural = _("Атрибуты")


class ProductAttributeThroughInline(admin.TabularInline):
    model = Product.attributes.through
    extra = 1
    verbose_name = _("Атрибут")
    verbose_name_plural = _("Атрибуты")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'attributevalue':
            kwargs['queryset'] = ProductAttributeValue.objects.select_related('attribute')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ProductCrossReferenceInline(admin.TabularInline):
    model = ProductCrossReference
    fk_name = 'product'
    extra = 1
    fields = ('article_number', 'brand', 'relation_type', 'analog_product', 'is_active', 'comment')
    readonly_fields = ('normalized_article',)
    autocomplete_fields = ['analog_product']


# Объявляем кастомные фильтры ВНЕ класса ProductAdmin
class VINFilter(admin.SimpleListFilter):
    title = _('Наличие VIN')
    parameter_name = 'has_vin'

    def lookups(self, request, model_admin):
        return (
            ('yes', _('Есть VIN')),
            ('no', _('Нет VIN')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(vin__isnull=True).exclude(vin='')
        if self.value() == 'no':
            return queryset.filter(Q(vin__isnull=True) | Q(vin=''))


class MaintenanceTypeFilter(admin.SimpleListFilter):
    title = _('Тип расходника ТО')
    parameter_name = 'maintenance_type'

    def lookups(self, request, model_admin):
        return Product.MAINTENANCE_TYPES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(maintenance_type=self.value())
        return queryset


class ViscosityFilter(admin.SimpleListFilter):
    title = _('Вязкость масла')
    parameter_name = 'viscosity'

    def lookups(self, request, model_admin):
        viscosities = Product.objects.filter(
            maintenance_type='engine_oil',
            viscosity__isnull=False
        ).values_list('viscosity', flat=True).distinct()
        return [(v, v) for v in viscosities if v]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(viscosity=self.value())
        return queryset


######################### Для характеристики Шин и Дисков ###########################
# Фильтры
class TireDiameterFilter(admin.SimpleListFilter):
    title = _('Диаметр шин')
    parameter_name = 'tire_diameter'

    def lookups(self, request, model_admin):
        return [
            (16, '16″'), (17, '17″'), (18, '18″'),
            (19, '19″'), (20, '20″'), (21, '21″'), (22, '22″')
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                tire_details__diameter=self.value(),
                product_type='tire_wheel'
            )
        return queryset


class WheelDiameterFilter(admin.SimpleListFilter):
    title = _('Диаметр дисков')
    parameter_name = 'wheel_diameter'

    def lookups(self, request, model_admin):
        return [
            (15, '15″'), (16, '16″'), (17, '17″'),
            (18, '18″'), (19, '19″'), (20, '20″')
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                wheel_details__diameter=self.value(),
                product_type='tire_wheel'
            )
        return queryset


class TireProductInline(admin.StackedInline):
    model = TireProduct
    extra = 1
    max_num = 1
    show_change_link = True
    fieldsets = (
        (_("Основные характеристики"), {
            'fields': (
                ('diameter', 'seasonality'),
                ('profile_width', 'profile_height'),
                'has_spikes'
            )
        }),
        (_("Дополнительные характеристики"), {
            'fields': (
                'load_index',
                'speed_index',
                'run_flat'
            )
        })
    )


class WheelProductInline(admin.StackedInline):
    model = WheelProduct
    extra = 1
    max_num = 1
    show_change_link = True
    fieldsets = (
        (_("Основные характеристики"), {
            'fields': (
                ('diameter', 'width'),
                ('offset_type', 'offset_value'),
                'wheel_type'
            )
        }),
        (_("Технические параметры"), {
            'fields': (
                'pcd',
                'center_bore',
                ('bolt_count', 'bolt_spacing')
            )
        })
    )


#  Для характеристик шин
@admin.register(TireDiameter)
class TireDiameterAdmin(admin.ModelAdmin):
    list_display = ('value',)
    search_fields = ('value',)


@admin.register(TireSeasonality)
class TireSeasonalityAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(TireProfileWidth)
class TireProfileWidthAdmin(admin.ModelAdmin):
    list_display = ('value',)
    search_fields = ('value',)


@admin.register(TireProfileHeight)
class TireProfileHeightAdmin(admin.ModelAdmin):
    list_display = ('value',)
    search_fields = ('value',)


@admin.register(TireLoadIndex)
class TireLoadIndexAdmin(admin.ModelAdmin):
    list_display = ('value', 'description')
    search_fields = ('value', 'description')


@admin.register(TireSpeedIndex)
class TireSpeedIndexAdmin(admin.ModelAdmin):
    list_display = ('value', 'description')
    search_fields = ('value', 'description')


# Админки для характеристик дисков
@admin.register(WheelDiameter)
class WheelDiameterAdmin(admin.ModelAdmin):
    list_display = ('value',)
    search_fields = ('value',)


@admin.register(WheelWidth)
class WheelWidthAdmin(admin.ModelAdmin):
    list_display = ('value',)
    search_fields = ('value',)


@admin.register(WheelOffsetType)
class WheelOffsetTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(WheelType)
class WheelTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')


@admin.register(WheelPCD)
class WheelPCDAdmin(admin.ModelAdmin):
    list_display = ('value',)
    search_fields = ('value',)


@admin.register(WheelCenterBore)
class WheelCenterBoreAdmin(admin.ModelAdmin):
    list_display = ('value',)
    search_fields = ('value',)


####################### Автохимия и масла ######################
class OilAndChemistryInline(admin.StackedInline):
    model = OilAndChemistryDetails
    extra = 1
    fieldsets = (
        (None, {
            'fields': (
                'oil_type', 'viscosity', 'volume', 'season', 'base_type'
            )
        }),
        (_("Спецификации и допуски"), {
            'classes': ('collapse',),
            'fields': ('api_spec', 'acea_spec', 'oem_approvals')
        }),
        (_("Технические характеристики"), {
            'classes': ('collapse',),
            'fields': ('flash_point', 'pour_point', 'density')
        }),
    )


####################### Инструмаенты  ######################
class ToolProductInline(admin.StackedInline):
    """
    Inline для характеристик инструментов в админке товара.
    """
    model = ToolProduct
    extra = 0
    classes = ('collapse',)

    fieldsets = (
        (_("Основные характеристики"), {
            'fields': (
                'tool_type', 'purpose', 'size', 'drive_size',
                'profile', 'thread_type', 'material', 'handle_type'
            )
        }),
        (_("Питание и мощность"), {
            'fields': (
                'power_type', 'voltage', 'battery_capacity',
                'power', 'torque', 'speed'
            )
        }),
        (_("Габариты и нагрузка"), {
            'fields': (
                'length', 'weight', 'max_load'
            )
        }),
        (_("Для домкратов и шиномонтажа"), {
            'fields': (
                'jack_type', 'lifting_capacity',
                'min_height', 'max_lift'
            )
        }),
        (_("Для диагностического оборудования"), {
            'fields': (
                'scanner_type', 'supported_protocols', 'compatible_brands'
            )
        }),
        (_("Комплектация"), {
            'fields': (
                'items_count', 'case_type', 'kit_contents'
            )
        }),
        (_("Дополнительно"), {
            'fields': (
                'color', 'warranty_months', 'country_of_origin', 'features'
            )
        }),
    )

    def get_max_num(self, request, obj=None, **kwargs):
        return 1

    def get_min_num(self, request, obj=None, **kwargs):
        return 0


####################### Автоэлектрика  ######################

class AutoElectricProductInline(admin.StackedInline):
    """
    Inline для характеристик автоэлектрики в админке товара.
    """
    model = AutoElectricProduct
    extra = 0
    classes = ('collapse',)

    fieldsets = (
        (_("Основные характеристики"), {
            'fields': (
                'electric_type', 'voltage', 'current', 'power', 'resistance'
            )
        }),
        (_("Характеристики аккумуляторов"), {
            'classes': ('collapse',),
            'fields': (
                'capacity', 'cold_cranking_amps', 'battery_technology',
                'polarity', 'terminal_type', 'dimensions'
            )
        }),
        (_("Характеристики генераторов и стартеров"), {
            'classes': ('collapse',),
            'fields': (
                'rotation_direction', 'rotation_speed',
                'number_of_teeth', 'bearing_type'
            )
        }),
        (_("Характеристики ламп"), {
            'classes': ('collapse',),
            'fields': (
                'bulb_type', 'bulb_base', 'light_temperature',
                'lumen', 'beam_pattern'
            )
        }),
        (_("Характеристики датчиков"), {
            'classes': ('collapse',),
            'fields': (
                'sensor_type', 'measurement_range', 'output_signal'
            )
        }),
        (_("Подключение и монтаж"), {
            'fields': (
                'oem_number', 'connector_type', 'pin_count',
                'wire_length', 'wire_cross_section'
            )
        }),
        (_("Защита и безопасность"), {
            'fields': (
                'insulation_class', 'ip_rating', 'operating_temperature',
                'protection_features', 'certification'
            )
        }),
        (_("Дополнительно"), {
            'fields': ('installation_notes',)
        }),
    )

    def get_max_num(self, request, obj=None, **kwargs):
        return 1

    def get_min_num(self, request, obj=None, **kwargs):
        return 0


######################## Акссуары ###############################
class AccessoryProductInline(admin.StackedInline):
    """
    Inline для характеристик аксессуаров в админке товара.
    """
    model = AccessoryProduct
    extra = 0
    classes = ('collapse',)

    fieldsets = (
        (_("Основные характеристики"), {
            'fields': (
                'accessory_type', 'purpose', 'material', 'color'
            )
        }),
        (_("Габариты и размеры"), {
            'fields': (
                'size', 'length', 'width', 'height', 'weight', 'volume'
            )
        }),
        (_("Электроника и подключение"), {
            'classes': ('collapse',),
            'fields': (
                'power_type', 'voltage', 'connection_type',
                'resolution', 'viewing_angle'
            )
        }),
        (_("Беспроводные технологии"), {
            'classes': ('collapse',),
            'fields': (
                'has_wifi', 'has_bluetooth', 'has_gps', 'has_night_vision'
            )
        }),
        (_("Крепление и монтаж"), {
            'fields': (
                'mounting_type', 'load_capacity'
            )
        }),
        (_("Защита и безопасность"), {
            'fields': (
                'ip_rating', 'temperature_range', 'uv_protection',
                'anti_slip', 'fire_resistant'
            )
        }),
        (_("Комплектация"), {
            'fields': (
                'kit_type', 'items_count', 'includes_mount',
                'includes_cables', 'includes_manual'
            )
        }),
        (_("Дополнительно"), {
            'fields': (
                'compatibility_notes', 'features', 'installation_notes',
                'country_of_origin', 'warranty_months'
            )
        }),
    )

    def get_max_num(self, request, obj=None, **kwargs):
        return 1

    def get_min_num(self, request, obj=None, **kwargs):
        return 0


class TagFilter(SimpleListFilter):
    title = 'Теги'
    parameter_name = 'tags'

    def lookups(self, request, model_admin):
        # Получаем самые популярные теги
        popular_tags = Tag.objects.filter(
            is_active=True
        ).annotate(
            product_count=models.Count('products')
        ).order_by('-product_count')[:20]

        return [(tag.slug, f"#{tag.name} ({tag.product_count})") for tag in popular_tags]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(tags__slug=self.value())
        return queryset


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color_display', 'product_count', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'product_count_display')
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'color', 'is_active')
        }),
        ('Статистика', {
            'classes': ('collapse',),
            'fields': ('product_count_display', 'created_at')
        }),
    )

    def color_display(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; '
            'border-radius: 3px; border: 1px solid #ddd;"></div>',
            obj.color
        )

    color_display.short_description = 'Цвет'

    def product_count(self, obj):
        return obj.products.count()

    product_count.short_description = 'Товаров'

    def product_count_display(self, obj):
        count = obj.products.count()
        return format_html(
            '<span style="font-size: 1.2rem; font-weight: bold; color: {};">{}</span> товаров',
            '#28a745' if count > 0 else '#6c757d',
            count
        )

    product_count_display.short_description = 'Количество товаров'

    actions = ['activate_tags', 'deactivate_tags']

    def activate_tags(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f"Активировано {updated} тегов")

    activate_tags.short_description = "Активировать выбранные теги"

    def deactivate_tags(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f"Деактивировано {updated} тегов")

    deactivate_tags.short_description = "Деактивировать выбранные теги"


######################## Продукт ###############################

class ProductAdminForm(forms.ModelForm):
    description = forms.CharField(
        widget=CKEditorUploadingWidget(),
        required=False,
        label=_("Описание"),
    )
    short_description = forms.CharField(
        widget=CKEditorUploadingWidget(),
        required=False,
        label=_("Краткое описание"),
    )

    class Meta:
        model = Product
        fields = '__all__'
        widgets = {
            'viscosity': forms.Select(choices=[
                ('5W-30', '5W-30'), ('5W-40', '5W-40'), ('0W-20', '0W-20'),
                ('10W-40', '10W-40'), ('15W-40', '15W-40')
            ]),
            'volume': forms.NumberInput(attrs={'step': '0.1', 'min': '0.1'}),
            # Совместимость — простые мультиселекты для каскадной фильтрации через JS
            'car_models': forms.SelectMultiple(attrs={'size': '8'}),
            'car_generations': forms.SelectMultiple(attrs={'size': '8'}),
            'car_modifications': forms.SelectMultiple(attrs={'size': '8'}),
            'truck_models': forms.SelectMultiple(attrs={'size': '8'}),
            'truck_generations': forms.SelectMultiple(attrs={'size': '8'}),
            'truck_modifications': forms.SelectMultiple(attrs={'size': '8'}),
            'moto_models': forms.SelectMultiple(attrs={'size': '8'}),
            'moto_generations': forms.SelectMultiple(attrs={'size': '8'}),
            'moto_modifications': forms.SelectMultiple(attrs={'size': '8'}),
            'special_models': forms.SelectMultiple(attrs={'size': '8'}),
            'special_generations': forms.SelectMultiple(attrs={'size': '8'}),
            'special_modifications': forms.SelectMultiple(attrs={'size': '8'}),
        }


@admin.register(ProductCrossReference)
class ProductCrossReferenceAdmin(admin.ModelAdmin):
    list_display = ('article_number', 'brand', 'relation_type', 'product', 'analog_product', 'is_active')
    list_filter = ('relation_type', 'brand', 'is_active')
    search_fields = (
        'article_number', 'normalized_article', 'brand',
        'product__name', 'product__part_number',
        'analog_product__name', 'analog_product__part_number',
    )
    autocomplete_fields = ['product', 'analog_product']
    readonly_fields = ('normalized_article', 'created_at', 'updated_at')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    change_form_template = 'admin/shop/product/change_form.html'

    class Media:
        js = (
            'admin/js/jquery.init.js',
            'admin/js/vendor/select2/select2.full.min.js',
            'admin/js/category_select2_init.js',
            'admin/js/product_compatibility.js',
            'admin/js/product_type_visibility.js',
        )
        css = {
            'all': (
                'admin/css/vendor/select2/select2.min.css',
                'admin/css/autocomplete.css',
                'admin/css/product_compatibility.css',
            )
        }

    # ------------------------ LISTS & SEARCH -----------------------------
    list_display = (
        'name', 'part_number', 'internal_code', 'vin', 'product_type', 'tire_wheel_type', 'maintenance_type',
        'category', 'get_part_subcategory', 'get_brand_display', 'seller',
        'moderation_status_badge', 'moderated_by', 'moderated_at',
        'price', 'stock_status', 'is_active', 'get_tire_wheel_specs', 'get_oil_chem_specs', 'get_tool_specs',
        'get_auto_electric_specs', 'get_accessory_specs', 'get_tags_display', 'get_dimensions_display',
        'get_modifications_display',
    )

    list_filter = (
        'product_type', 'tire_wheel_type', 'maintenance_type', 'category', 'part_subcategory',
        'seller', 'seller__status', 'moderation_status', 'is_active', 'vehicle_type', 'is_original', 'is_featured', 'is_new', 'tags',
        VINFilter, MaintenanceTypeFilter, ViscosityFilter, TagFilter,
    )

    search_fields = (
        'name', 'part_number', 'normalized_part_number', 'internal_code', 'vin',
        'description', 'seller__company_name', 'tags__name',
        'cross_references__article_number', 'cross_references__normalized_article',
    )
    prepopulated_fields = {'slug': ('name',)}

    # ----------------------------- INLINES --------------------------------
    inlines = [
        ProductImageInline,
        ProductAttributeThroughInline,
        ProductCrossReferenceInline,
        TireProductInline,
        WheelProductInline,
    ]

    # --------------------------- READ‑ONLY --------------------------------
    readonly_fields = (
        'created_at', 'updated_at', 'image_preview',
        'stock_status', 'discount_percent', 'get_compatibility_display', 'get_tool_info', 'get_auto_electric_info',
        'get_accessory_info', 'get_tags_info', 'get_dimensions_display',

    )

    # --------------------------- FIELDSETS --------------------------------
    fieldsets = (
        (_("Основная информация"), {
            'fields': (
                'name', 'slug', 'part_number', 'vin', 'product_type', 'tire_wheel_type',
                'maintenance_type', 'description', 'short_description', 'is_active'
            )
        }),
        (_("Цена и наличие"), {
            'fields': (
                'price', 'old_price', 'discount_percent',
                'stock', 'stock_status', 'warranty', 'sale_end_date'
            )
        }),
        (_("Продавец и категории"), {
            'fields': (
                'seller', 'category', 'extra_categories', 'part_subcategory', 'manufacturer', 'product_brand', 'vehicle_type'
            )
        }),
        (_("Теги/Ключевые слова"), {
            'classes': ('collapse',),
            'fields': ('tags', 'get_tags_info')
        }),
        (_("Специализированные категории"), {
            'classes': ('collapse',),
            'fields': (
                ('oil_chem_category', 'oil_chem_brand'),
                ('maintenance_category', 'maintenance_brand'),
                ('tire_wheel_category', 'tire_wheel_brand'),
                ('tool_category', 'tool_brand'),
                ('auto_electric_category', 'auto_electric_brand'),
            )
        }),
        (_("Характеристики для ТО"), {
            'classes': ('collapse',),
            'fields': (
                'viscosity', 'volume', 'filter_type', 'spark_plug_type'
            )
        }),
        (_("Совместимость"), {
            'classes': ('compat-custom-fieldset',),
            'fields': (
                'car_brand', 'car_models', 'car_generations', 'car_modifications',
                'truck_brand', 'truck_models', 'truck_generations', 'truck_modifications',
                'moto_brand', 'moto_models', 'moto_generations', 'moto_modifications',
                'special_brand', 'special_models', 'special_generations', 'special_modifications',
            ),
        }),
        (_("Габариты"), {
            'fields': (
                'weight',
                ('length', 'width', 'height'),
                'under_order',
                'country_of_origin',
                'is_original',
                'is_featured',
                'is_new'
            )
        }),
        (_("Изображения"), {
            'fields': ('image', 'image_preview')
        }),
        (_("Модерация"), {
            'classes': ('collapse',),
            'fields': ('moderation_status', 'moderation_notes', 'moderated_by', 'moderated_at')
        }),
        (_("Метаданные"), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'views')
        }),
    )

    # -------------------------- DISPLAY HELPERS ---------------------------
    def get_image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="200" />')
        return "-"

    get_image_preview.short_description = _("Превью изображения")

    def get_brand_display(self, obj):
        brand_mapping = {
            'oil_chem': obj.oil_chem_brand,
            'maintenance': obj.maintenance_brand,
            'tire_wheel': obj.tire_wheel_brand,
            'tool': obj.tool_brand,
            'auto_electric': obj.auto_electric_brand,
            'car': obj.car_brand,
            'truck': obj.truck_brand,
            'moto': obj.moto_brand,
            'special': obj.special_brand,
        }

        if obj.product_type in brand_mapping:
            brand = brand_mapping[obj.product_type]
        else:
            brand = brand_mapping.get(obj.vehicle_type)

        return brand.name if brand else "-"

    get_brand_display.short_description = _("Бренд")

    def stock_status(self, obj):
        if obj.stock == 0:
            return format_html('<span style="color: red;">{}</span>', _("Нет в наличии"))
        elif obj.stock < 5:
            return format_html('<span style="color: orange;">{}: {}</span>', _("Осталось"), obj.stock)
        return format_html('<span style="color: green;">{}</span>', _("В наличии"))

    stock_status.short_description = _("Наличие")

    def discount_percent(self, obj):
        """
        Read-only field for admin.

        Important: on the "add" form `obj` exists, but `price/old_price` may be None,
        so this method must be defensive to avoid 500s in Django admin rendering.
        """
        if not obj:
            return "-"

        price = getattr(obj, "price", None)
        old_price = getattr(obj, "old_price", None)

        # Nothing to compare yet (e.g. add form, or incomplete data)
        if price is None or old_price is None:
            return "-"

        try:
            if old_price > price:
                get_discount = getattr(obj, "get_discount", None)
                if callable(get_discount):
                    return f"{get_discount()}%"
                return "-"  # fallback, should not happen
        except TypeError:
            # Guard against unexpected types (e.g. string/None) in DB
            return "-"

        return "-"

    discount_percent.short_description = _("Скидка")

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="200" />')
        return "-"

    image_preview.short_description = _("Превью изображения")

    def get_part_subcategory(self, obj):
        return obj.part_subcategory.name if obj.part_subcategory else "-"

    get_part_subcategory.short_description = _("Подкатегория")

    def get_compatibility_display(self, obj):
        """Отображение совместимости в read-only поле"""
        compatibilities = []
        if obj.car_brand:
            compatibilities.append(f"{obj.car_brand.name}")
        if obj.car_models.exists():
            compatibilities.append(f"{obj.car_models.count()} моделей")
        if obj.car_generations.exists():
            compatibilities.append(f"{obj.car_generations.count()} поколений")
        return ", ".join(compatibilities) if compatibilities else "Универсальный"

    get_compatibility_display.short_description = _("Совместимость")

    def get_tire_wheel_info(self, obj):
        """Отображает информацию о шине/диске в read-only поле"""
        if obj.product_type == 'tire_wheel':
            if obj.tire_wheel_type == 'tire' and hasattr(obj, 'tire_details'):
                tire = obj.tire_details
                return format_html(
                    '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
                    '<strong>Шина:</strong> {}<br>'
                    '<strong>Размер:</strong> {}<br>'
                    '<strong>Сезонность:</strong> {}<br>'
                    '<strong>Шипы:</strong> {}<br>'
                    '<strong>Индексы:</strong> {}/{}'
                    '</div>',
                    tire.get_size_display(),
                    f"{tire.profile_width.value}/{tire.profile_height.value}R{tire.diameter.value}",
                    tire.seasonality.name,
                    "Да" if tire.has_spikes else "Нет",
                    tire.load_index or "-",
                    tire.speed_index or "-"
                )
            elif obj.tire_wheel_type == 'wheel' and hasattr(obj, 'wheel_details'):
                wheel = obj.wheel_details
                return format_html(
                    '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
                    '<strong>Диск:</strong> {}<br>'
                    '<strong>Размер:</strong> {}<br>'
                    '<strong>Тип:</strong> {}<br>'
                    '<strong>Вылет:</strong> {}<br>'
                    '<strong>PCD:</strong> {}<br>'
                    '<strong>DIA:</strong> {} мм'
                    '</div>',
                    wheel.get_full_specs(),
                    f"{wheel.diameter.value}×{wheel.width.value}",
                    wheel.wheel_type.name,
                    f"ET{wheel.offset_value} ({wheel.offset_type.name})",
                    wheel.pcd.value,
                    wheel.center_bore.value
                )
        return format_html('<div style="color: #6c757d;">Не указано</div>')

    get_tire_wheel_info.short_description = _("Характеристики шины/диска")

    def get_tire_wheel_specs(self, obj):
        """Отображает спецификации шин/дисков в списке товаров"""
        if obj.product_type == 'tire_wheel':
            if obj.tire_wheel_type == 'tire' and hasattr(obj, 'tire_details'):
                return obj.tire_details.get_size_display()
            elif obj.tire_wheel_type == 'wheel' and hasattr(obj, 'wheel_details'):
                return obj.wheel_details.get_full_specs()
        return "-"

    get_tire_wheel_specs.short_description = _("Спецификации")

    def get_oil_chem_info(self, obj):
        """Отображает информацию об автохимии в read-only поле"""
        if obj.product_type == 'oil_chem' and hasattr(obj, 'oil_chem_details'):
            oil = obj.oil_chem_details
            return format_html(
                '<div style="background: #f8f9fa; padding: 10px; border-radius: 5px;">'
                '<strong>Тип:</strong> {}<br>'
                '<strong>Вязкость:</strong> {}<br>'
                '<strong>Объем:</strong> {} л<br>'
                '<strong>Основа:</strong> {}<br>'
                '<strong>Сезонность:</strong> {}'
                '</div>',
                oil.get_oil_type_display(),
                oil.viscosity or "-",
                oil.volume,
                oil.get_base_type_display() if oil.base_type else "-",
                oil.get_season_display() if oil.season else "-"
            )
        return format_html('<div style="color: #6c757d;">Не указано</div>')

    get_oil_chem_info.short_description = _("Характеристики автохимии")

    def get_oil_chem_specs(self, obj):
        """Отображает спецификации автохимии в списке товаров"""
        if obj.product_type == 'oil_chem' and hasattr(obj, 'oil_chem_details'):
            oil = obj.oil_chem_details
            specs = []
            if oil.viscosity:
                specs.append(oil.viscosity)
            if oil.volume:
                specs.append(f"{oil.volume}л")
            return " / ".join(specs) if specs else "-"
        return "-"

    get_oil_chem_specs.short_description = _("Спецификации автохимии")

    def get_tool_info(self, obj):
        """Отображает полную информацию об инструменте в read-only поле"""
        if obj.product_type == 'tool' and hasattr(obj, 'tool_details'):
            tool = obj.tool_details
            specs_html = []

            # Основные характеристики
            if tool.tool_type:
                specs_html.append(f"<strong>Тип инструмента:</strong> {tool.get_tool_type_display()}")
            if tool.purpose:
                specs_html.append(f"<strong>Назначение:</strong> {tool.get_purpose_display()}")
            if tool.size:
                specs_html.append(f"<strong>Размер:</strong> {tool.size}")
            if tool.drive_size:
                specs_html.append(f"<strong>Посадочный квадрат:</strong> {tool.get_drive_size_display()}")

            # Материалы
            if tool.material:
                specs_html.append(f"<strong>Материал:</strong> {tool.get_material_display()}")
            if tool.handle_type:
                specs_html.append(f"<strong>Рукоятка:</strong> {tool.get_handle_type_display()}")

            # Питание и мощность
            if tool.power_type:
                specs_html.append(f"<strong>Питание:</strong> {tool.get_power_type_display()}")
            if tool.voltage:
                specs_html.append(f"<strong>Напряжение:</strong> {tool.voltage}")
            if tool.torque:
                specs_html.append(f"<strong>Крутящий момент:</strong> {tool.torque}")

            # Для домкратов
            if tool.jack_type:
                specs_html.append(f"<strong>Тип домкрата:</strong> {tool.get_jack_type_display()}")
            if tool.lifting_capacity:
                specs_html.append(f"<strong>Грузоподъемность:</strong> {tool.lifting_capacity}")

            # Комплектация
            if tool.items_count:
                specs_html.append(f"<strong>Количество предметов:</strong> {tool.items_count}")
            if tool.warranty_months:
                specs_html.append(f"<strong>Гарантия:</strong> {tool.warranty_months} мес.")

            if specs_html:
                return format_html(
                    '<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff;">' +
                    '<h4 style="margin-top: 0; color: #007bff;">📋 Характеристики инструмента</h4>' +
                    '<br>'.join(specs_html) +
                    '</div>'
                )

        return format_html(
            '<div style="color: #6c757d; font-style: italic;">Характеристики инструмента не указаны</div>')

    get_tool_info.short_description = _("Характеристики инструмента")

    def get_tool_specs(self, obj):
        """Отображает спецификации инструментов в списке товаров"""
        if obj.product_type == 'tool' and hasattr(obj, 'tool_details'):
            return obj.tool_details.get_tool_specs_display()
        return "-"

    get_tool_specs.short_description = _("Спецификации инструмента")

    def get_auto_electric_specs(self, obj):
        """Отображает спецификации автоэлектрики в списке товаров"""
        if obj.product_type == 'auto_electric' and hasattr(obj, 'auto_electric_details'):
            return obj.auto_electric_details.get_electric_specs_display()
        return "-"

    get_auto_electric_specs.short_description = _("Спецификации автоэлектрики")

    def get_auto_electric_info(self, obj):
        """Отображает полную информацию об автоэлектрике в read-only поле"""
        if obj.product_type == 'auto_electric' and hasattr(obj, 'auto_electric_details'):
            electric = obj.auto_electric_details
            specs_html = []

            # Основные характеристики
            if electric.electric_type:
                specs_html.append(f"<strong>Тип оборудования:</strong> {electric.get_electric_type_display()}")
            if electric.voltage:
                specs_html.append(f"<strong>Напряжение:</strong> {electric.get_voltage_display()}")
            if electric.current:
                specs_html.append(f"<strong>Сила тока:</strong> {electric.current} А")
            if electric.power:
                specs_html.append(f"<strong>Мощность:</strong> {electric.power}")

            # Характеристики аккумуляторов
            if electric.capacity:
                specs_html.append(f"<strong>Емкость:</strong> {electric.capacity} Ач")
            if electric.cold_cranking_amps:
                specs_html.append(f"<strong>Пусковой ток:</strong> {electric.cold_cranking_amps} CCA")
            if electric.battery_technology:
                specs_html.append(
                    f"<strong>Технология аккумулятора:</strong> {electric.get_battery_technology_display()}")
            if electric.polarity:
                specs_html.append(f"<strong>Полярность:</strong> {electric.get_polarity_display()}")

            # Характеристики ламп
            if electric.bulb_type:
                specs_html.append(f"<strong>Тип лампы:</strong> {electric.get_bulb_type_display()}")
            if electric.bulb_base:
                specs_html.append(f"<strong>Цоколь:</strong> {electric.get_bulb_base_display()}")
            if electric.light_temperature:
                specs_html.append(f"<strong>Цветовая температура:</strong> {electric.light_temperature} K")
            if electric.lumen:
                specs_html.append(f"<strong>Световой поток:</strong> {electric.lumen} лм")

            # Характеристики датчиков
            if electric.sensor_type:
                specs_html.append(f"<strong>Тип датчика:</strong> {electric.sensor_type}")
            if electric.measurement_range:
                specs_html.append(f"<strong>Диапазон измерений:</strong> {electric.measurement_range}")

            # Подключение и защита
            if electric.connector_type:
                specs_html.append(f"<strong>Тип разъема:</strong> {electric.connector_type}")
            if electric.ip_rating:
                specs_html.append(f"<strong>Степень защиты:</strong> {electric.ip_rating}")
            if electric.operating_temperature:
                specs_html.append(f"<strong>Рабочая температура:</strong> {electric.operating_temperature}")

            if specs_html:
                return format_html(
                    '<div style="background: #f0f8ff; padding: 15px; border-radius: 5px; border-left: 4px solid #17a2b8;">' +
                    '<h4 style="margin-top: 0; color: #17a2b8;">⚡ Характеристики автоэлектрики</h4>' +
                    '<br>'.join(specs_html) +
                    '</div>'
                )

        return format_html(
            '<div style="color: #6c757d; font-style: italic;">Характеристики автоэлектрики не указаны</div>')

    get_auto_electric_info.short_description = _("Характеристики автоэлектрики")

    def get_accessory_specs(self, obj):
        """Отображает спецификации аксессуаров в списке товаров"""
        if obj.product_type == 'accessory' and hasattr(obj, 'accessory_details'):
            return obj.accessory_details.get_accessory_specs_display()
        return "-"

    get_accessory_specs.short_description = _("Спецификации аксессуара")

    def get_accessory_info(self, obj):
        """Отображает полную информацию об аксессуаре в read-only поле"""
        if obj.product_type == 'accessory' and hasattr(obj, 'accessory_details'):
            accessory = obj.accessory_details
            specs_html = []

            # Основные характеристики
            if accessory.accessory_type:
                specs_html.append(f"<strong>Тип аксессуара:</strong> {accessory.get_accessory_type_display()}")
            if accessory.purpose:
                specs_html.append(f"<strong>Назначение:</strong> {accessory.get_purpose_display()}")
            if accessory.material:
                specs_html.append(f"<strong>Материал:</strong> {accessory.get_material_display()}")
            if accessory.color:
                specs_html.append(f"<strong>Цвет:</strong> {accessory.color}")

            # Габариты
            if accessory.length and accessory.width:
                size_text = f"<strong>Размеры:</strong> {accessory.length}×{accessory.width}"
                if accessory.height:
                    size_text += f"×{accessory.height}"
                size_text += " см"
                specs_html.append(size_text)
            elif accessory.size:
                specs_html.append(f"<strong>Размер:</strong> {accessory.size}")

            # Электроника
            if accessory.power_type:
                specs_html.append(f"<strong>Питание:</strong> {accessory.get_power_type_display()}")
            if accessory.resolution:
                specs_html.append(f"<strong>Разрешение:</strong> {accessory.resolution}")
            if accessory.viewing_angle:
                specs_html.append(f"<strong>Угол обзора:</strong> {accessory.viewing_angle}°")

            # Беспроводные технологии
            tech_features = []
            if accessory.has_wifi:
                tech_features.append("Wi-Fi")
            if accessory.has_bluetooth:
                tech_features.append("Bluetooth")
            if accessory.has_gps:
                tech_features.append("GPS")
            if accessory.has_night_vision:
                tech_features.append("Ночное видение")
            if tech_features:
                specs_html.append(f"<strong>Технологии:</strong> {', '.join(tech_features)}")

            # Крепление
            if accessory.mounting_type:
                specs_html.append(f"<strong>Крепление:</strong> {accessory.get_mounting_type_display()}")
            if accessory.load_capacity:
                specs_html.append(f"<strong>Грузоподъемность:</strong> {accessory.load_capacity} кг")

            # Защита
            protection_features = []
            if accessory.ip_rating:
                protection_features.append(f"IP{accessory.ip_rating}")
            if accessory.uv_protection:
                protection_features.append("УФ-защита")
            if accessory.anti_slip:
                protection_features.append("Антискольжение")
            if accessory.fire_resistant:
                protection_features.append("Огнестойкость")
            if protection_features:
                specs_html.append(f"<strong>Защита:</strong> {', '.join(protection_features)}")
            if accessory.temperature_range:
                specs_html.append(f"<strong>Температурный диапазон:</strong> {accessory.temperature_range}")

            # Комплектация
            if accessory.kit_type:
                specs_html.append(f"<strong>Комплектация:</strong> {accessory.get_kit_type_display()}")
            if accessory.items_count:
                specs_html.append(f"<strong>Количество предметов:</strong> {accessory.items_count} шт")

            if specs_html:
                return format_html(
                    '<div style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">' +
                    '<h4 style="margin-top: 0; color: #856404;">🎁 Характеристики аксессуара</h4>' +
                    '<br>'.join(specs_html) +
                    '</div>'
                )

        return format_html(
            '<div style="color: #6c757d; font-style: italic;">Характеристики аксессуара не указаны</div>')

    get_accessory_info.short_description = _("Характеристики аксессуара")

    # -------------------------- FIELDSETS HOOK ----------------------------
    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)

        # Скрываем специализированные категории, если они не нужны
        if obj and obj.product_type not in ['oil_chem', 'maintenance', 'tire_wheel', 'tool', 'auto_electric']:
            fieldsets = [fs for fs in fieldsets if fs[0] != _("Специализированные категории")]

        # Скрываем характеристики ТО если это не ТО товар
        if obj and obj.product_type != 'maintenance':
            fieldsets = [fs for fs in fieldsets if fs[0] != _("Характеристики для ТО")]

        # Скрываем старые поля вязкости и объема для автохимии
        if obj and obj.product_type == 'oil_chem':
            fieldsets = [fs for fs in fieldsets if fs[0] != _("Характеристики для ТО")]

        # Показываем только соответствующие характеристики для шин/дисков
        if obj and obj.product_type == 'tire_wheel':
            if obj.tire_wheel_type == 'tire':
                # Скрываем характеристики дисков
                fieldsets = [fs for fs in fieldsets if fs[0] != _("Характеристики дисков")]
            elif obj.tire_wheel_type == 'wheel':
                # Скрываем характеристики шин
                fieldsets = [fs for fs in fieldsets if fs[0] != _("Характеристики шин")]
        else:
            # Скрываем все характеристики шин и дисков для других типов товаров
            fieldsets = [fs for fs in fieldsets if fs[0] not in [_("Характеристики шин"), _("Характеристики дисков")]]

            # Показываем характеристики инструментов только для товаров типа 'tool'
        if obj and obj.product_type == 'tool':
            # Добавляем поле с информацией об инструменте
            pass  # Поле уже добавлено в readonly_fields
        else:
            # Убираем поле с информацией об инструменте из отображения
            pass

            # Показываем характеристики автоэлектрики только для товаров типа 'auto_electric'
        if obj and obj.product_type == 'auto_electric':
            # Поле уже добавлено в readonly_fields
            pass
        else:
            # Убираем поле с информацией об автоэлектрике из отображения
            pass
        # Показываем характеристики аксессуаров только для товаров типа 'accessory'
        if obj and obj.product_type == 'accessory':
            # Поле уже добавлено в readonly_fields
            pass
        else:
            # Убираем поле с информацией об аксессуаре из отображения
            pass

        return fieldsets

    # -------------------------- FORM CUSTOMIZATION ------------------------
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)

        # Динамически меняем виджеты для полей ТО
        if obj and obj.product_type == 'maintenance':
            if obj.maintenance_type == 'engine_oil':
                form.base_fields['viscosity'].widget.attrs.update({
                    'placeholder': '5W-30, 5W-40, 0W-20...'
                })
            elif obj.maintenance_type in ['oil_filter', 'air_filter', 'fuel_filter', 'cabin_filter']:
                form.base_fields['filter_type'].widget.attrs.update({
                    'placeholder': 'Тип фильтра...'
                })
            elif obj.maintenance_type == 'spark_plug':
                form.base_fields['spark_plug_type'].widget.attrs.update({
                    'placeholder': 'Тип свечи...'
                })

        return form

    # -------------------------- QUERY OPTIMISATION ------------------------
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'seller', 'category', 'part_subcategory', 'manufacturer', 'product_brand',
            'oil_chem_category', 'oil_chem_brand',
            'maintenance_category', 'maintenance_brand',
            'tire_wheel_category', 'tire_wheel_brand',
            'tool_category', 'tool_brand',
            'auto_electric_category', 'auto_electric_brand',
            'car_brand', 'truck_brand', 'moto_brand', 'category__parent__parent', 'special_brand',
            'auto_electric_details', 'accessory_details'
        ).prefetch_related(
            'car_models', 'car_generations',
            'truck_models', 'truck_generations',
            'moto_models', 'moto_generations',
            'special_models', 'special_generations',
            'images', 'attributes'
        )

    # -------------------------- CUSTOM ACTIONS ----------------------------
    actions = [
        'make_featured', 'update_prices', 'create_maintenance_kits', 'assign_to_seller',
        'approve_products', 'reject_products', 'request_revision',
    ]

    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f"{updated} товаров отмечены как рекомендуемые")

    make_featured.short_description = _("Сделать рекомендуемыми")

    def update_prices(self, request, queryset):
        updated = 0
        for product in queryset:
            if product.old_price:
                product.price = product.old_price * Decimal('0.9')  # 10% скидка
                product.save()
                updated += 1
        self.message_user(request, f"Цены обновлены для {updated} товаров")

    update_prices.short_description = _("Обновить цены со скидкой")

    def create_maintenance_kits(self, request, queryset):
        maintenance_products = queryset.filter(product_type='maintenance')

        if not maintenance_products.exists():
            self.message_user(request, "Нет товаров для ТО среди выбранных", level='error')
            return

        # Здесь можно добавить логику создания комплектов
        self.message_user(request, f"Готово к созданию комплектов из {maintenance_products.count()} товаров")

    create_maintenance_kits.short_description = _("Создать комплекты ТО")

    def assign_to_seller(self, request, queryset):
        """Действие для назначения продавца товарам"""
        from sellers.models import Seller

        # Получаем всех активных продавцов
        sellers = Seller.objects.filter(is_active=True, status='approved')

        if not sellers.exists():
            self.message_user(request, "Нет активных продавцов в системе", level='error')
            return

        # Простой пример - назначаем первого попавшегося продавца
        # В реальном приложении можно сделать форму выбора
        seller = sellers.first()
        updated = queryset.update(seller=seller)
        self.message_user(request, f"{updated} товаров назначены продавцу {seller.company_name}")

    assign_to_seller.short_description = _("Назначить продавца")

    def approve_products(self, request, queryset):
        now = timezone.now()
        count = queryset.update(
            moderation_status='approved',
            is_active=True,
            moderated_by=request.user,
            moderated_at=now
        )
        self.message_user(request, _("Одобрено товаров: %(count)s") % {'count': count})

    approve_products.short_description = _("Одобрить выбранные товары")

    def reject_products(self, request, queryset):
        now = timezone.now()
        count = queryset.update(
            moderation_status='rejected',
            is_active=False,
            moderated_by=request.user,
            moderated_at=now
        )
        self.message_user(request, _("Отклонено товаров: %(count)s. Укажите причину в карточке товара (Замечания модератора).") % {'count': count})

    reject_products.short_description = _("Отклонить выбранные товары")

    def request_revision(self, request, queryset):
        now = timezone.now()
        count = queryset.update(
            moderation_status='revision',
            is_active=False,
            moderated_by=request.user,
            moderated_at=now
        )
        self.message_user(request, _("Возвращено на доработку: %(count)s товаров.") % {'count': count})

    request_revision.short_description = _("Вернуть на доработку")

    # -------------------------- SAVE HANDLING ----------------------------
    def save_model(self, request, obj, form, change):
        # Автоматическая установка maintenance_type для товаров ТО
        if obj.product_type == 'maintenance' and not obj.maintenance_type:
            obj.maintenance_type = 'other'

        super().save_model(request, obj, form, change)

    # -------------------------- LIST DISPLAY FORMATTING -------------------

    def seller_display(self, obj):
        if obj.seller:
            return format_html(
                '<span title="{}">{}</span>',
                obj.seller.contact_person,
                obj.seller.company_name
            )
        return "-"

    seller_display.short_description = _("Продавец")

    def moderation_status_badge(self, obj):
        if not obj:
            return "-"
        status = getattr(obj, 'moderation_status', None) or 'pending'
        labels = {
            'draft': _('Черновик'),
            'pending': _('На проверке'),
            'approved': _('Одобрен'),
            'rejected': _('Отклонен'),
            'suspended': _('Приостановлен'),
            'revision': _('Требует правок'),
        }
        text = labels.get(status, status)
        colors = {
            'draft': '#6c757d',
            'pending': '#ffc107',
            'approved': '#28a745',
            'rejected': '#dc3545',
            'suspended': '#6c757d',
            'revision': '#17a2b8',
        }
        color = colors.get(status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.85rem;">{}</span>',
            color, text
        )

    moderation_status_badge.short_description = _("Модерация")

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "category":
            kwargs['queryset'] = Category.objects.all().select_related('parent', 'parent__parent')
            return CategoryHierarchySelect2Field(
                queryset=kwargs['queryset'],
                required=not db_field.blank,
                label=db_field.verbose_name,
                empty_label="---------",
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "extra_categories":
            kwargs['queryset'] = Category.objects.all().select_related('parent', 'parent__parent')
            return CategoryHierarchyMultipleSelect2Field(
                queryset=kwargs['queryset'],
                required=False,
                label=db_field.verbose_name,
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

        # -------------------------- DISPLAY HELPERS ---------------------------

    def get_tags_display(self, obj):
        """Отображение тегов в списке товаров"""
        tags = obj.tags.all()[:3]  # Показываем только первые 3 тега
        if tags:
            tags_html = []
            for tag in tags:
                tags_html.append(
                    f'<span style="background-color: {tag.color}20; '
                    f'color: {tag.color}; padding: 2px 8px; border-radius: 12px; '
                    f'border: 1px solid {tag.color}30; font-size: 0.85rem; margin-right: 4px;">'
                    f'#{tag.name}</span>'
                )
            return mark_safe(' '.join(tags_html))
        return "-"

    get_tags_display.short_description = _("Теги")

    def get_tags_info(self, obj):
        """Отображение всех тегов в read-only поле"""
        tags = obj.tags.all()
        if tags:
            tags_html = []
            for tag in tags:
                tags_html.append(
                    f'<span style="background-color: {tag.color}20; '
                    f'color: {tag.color}; padding: 4px 12px; border-radius: 16px; '
                    f'border: 1px solid {tag.color}30; font-size: 0.9rem; margin: 4px; '
                    f'display: inline-block;">'
                    f'#{tag.name} ({tag.products.count()})</span>'
                )
            return mark_safe(
                '<div style="background: #f8f9fa; padding: 15px; border-radius: 5px; '
                'margin-top: 10px;">' +
                '<h4 style="margin-top: 0; color: #495057; font-size: 1rem;">📌 Теги товара</h4>' +
                '<div style="margin-top: 10px;">' +
                ''.join(tags_html) +
                '</div></div>'
            )
        return mark_safe(
            '<div style="color: #6c757d; font-style: italic; padding: 10px;">'
            'Теги для этого товара не указаны. Добавьте теги для улучшения поиска.'
            '</div>'
        )

    get_tags_info.short_description = _("Текущие теги")

    def get_modifications_display(self, obj):
        """Отображает модификации в списке товаров"""
        modifications = []

        if obj.vehicle_type == 'car' and obj.car_modifications.exists():
            mod_names = obj.car_modifications.all()[:3]
            modifications.extend([mod.name for mod in mod_names])
            if obj.car_modifications.count() > 3:
                modifications.append(f"+{obj.car_modifications.count() - 3}")

        elif obj.vehicle_type == 'truck' and obj.truck_modifications.exists():
            mod_names = obj.truck_modifications.all()[:3]
            modifications.extend([mod.name for mod in mod_names])
            if obj.truck_modifications.count() > 3:
                modifications.append(f"+{obj.truck_modifications.count() - 3}")

        elif obj.vehicle_type == 'moto' and obj.moto_modifications.exists():
            mod_names = obj.moto_modifications.all()[:3]
            modifications.extend([mod.name for mod in mod_names])
            if obj.moto_modifications.count() > 3:
                modifications.append(f"+{obj.moto_modifications.count() - 3}")

        elif obj.vehicle_type == 'special' and obj.special_modifications.exists():
            mod_names = obj.special_modifications.all()[:3]
            modifications.extend([mod.name for mod in mod_names])
            if obj.special_modifications.count() > 3:
                modifications.append(f"+{obj.special_modifications.count() - 3}")

        if modifications:
            return format_html('<span style="color: #6c757d; font-size: 0.9em;">{}</span>',
                               ', '.join(modifications))
        return "-"

    get_modifications_display.short_description = _("Модификации")


@admin.register(CategoryRequest)
class CategoryRequestAdmin(admin.ModelAdmin):
    """Модерация заявок продавцов на добавление новых категорий."""

    list_display = ('name', 'seller_link', 'parent_category', 'status_badge', 'created_at', 'reviewed_by')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'seller__company_name', 'seller__contact_person')
    ordering = ('-created_at',)
    actions = ['action_approve', 'action_reject']

    fieldsets = (
        (_('Заявка'), {
            'fields': ('seller', 'name', 'parent_category', 'description', 'created_at'),
        }),
        (_('Решение модератора'), {
            'fields': ('status', 'moderator_comment', 'created_category', 'reviewed_at', 'reviewed_by'),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            # Новая запись — всё редактируемо
            return ('created_at', 'reviewed_at', 'reviewed_by')
        # Существующая — данные заявки только для чтения, решение модератора редактируемо
        return ('seller', 'name', 'parent_category', 'description', 'created_at', 'reviewed_at', 'reviewed_by')

    def seller_link(self, obj):
        return format_html('<a href="/admin/sellers/seller/{}/change/">{}</a>',
                           obj.seller_id, obj.seller)
    seller_link.short_description = _('Продавец')

    def status_badge(self, obj):
        colors = {'pending': '#ffc107', 'approved': '#28a745', 'rejected': '#dc3545'}
        labels = {'pending': 'На проверке', 'approved': 'Одобрена', 'rejected': 'Отклонена'}
        color = colors.get(obj.status, '#6c757d')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background:{};color:white;padding:2px 10px;border-radius:4px;'
            'font-size:0.85rem;white-space:nowrap">{}</span>',
            color, label,
        )
    status_badge.short_description = _('Статус')

    @admin.action(description=_('Одобрить выбранные заявки'))
    def action_approve(self, request, queryset):
        now = timezone.now()
        count = queryset.filter(status='pending').update(
            status='approved', reviewed_by=request.user, reviewed_at=now,
        )
        self.message_user(request, _(f'Одобрено заявок: {count}'))

    @admin.action(description=_('Отклонить выбранные заявки'))
    def action_reject(self, request, queryset):
        now = timezone.now()
        count = queryset.filter(status='pending').update(
            status='rejected', reviewed_by=request.user, reviewed_at=now,
        )
        self.message_user(request, _(f'Отклонено заявок: {count}'))


# Brand Type Relation Inlines
class CarBrandTypeRelationInline(admin.TabularInline):
    model = CarBrandTypeRelation
    extra = 1


class BrandCategoryRelationInlineBase(admin.TabularInline):
    extra = 1

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'category':
            kwargs['queryset'] = Category.objects.all().select_related('parent', 'parent__parent')
            return CategoryHierarchySelect2Field(
                queryset=kwargs['queryset'],
                required=not db_field.blank,
                label=db_field.verbose_name,
                empty_label="---------",
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class CarBrandCategoryRelationInline(BrandCategoryRelationInlineBase):
    model = CarBrandCategoryRelation


class TruckBrandTypeRelationInline(admin.TabularInline):
    model = TruckBrandTypeRelation
    extra = 1


class TruckBrandCategoryRelationInline(BrandCategoryRelationInlineBase):
    model = TruckBrandCategoryRelation


class MotoBrandTypeRelationInline(admin.TabularInline):
    model = MotoBrandTypeRelation
    extra = 1


class MotoBrandCategoryRelationInline(BrandCategoryRelationInlineBase):
    model = MotoBrandCategoryRelation


class SpecialBrandTypeRelationInline(admin.TabularInline):
    model = SpecialBrandTypeRelation
    extra = 1


class SpecialBrandCategoryRelationInline(BrandCategoryRelationInlineBase):
    model = SpecialBrandCategoryRelation


# Vehicle Brands Admin
class BrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'year_founded', 'is_active', 'get_logo_preview')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'country', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_logo_preview',)
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'logo', 'get_logo_preview', 'is_active')
        }),
        (_("Информация"), {
            'fields': ('description', 'year_founded', 'country')
        }),
    )

    def get_logo_preview(self, obj):
        if obj.logo:
            return mark_safe(f'<img src="{obj.logo.url}" width="100" />')
        return "-"

    get_logo_preview.short_description = _("Логотип")


@admin.register(CarBrand)
class CarBrandAdmin(BrandAdmin):
    inlines = [CarBrandTypeRelationInline, CarBrandCategoryRelationInline]


@admin.register(TruckBrand)
class TruckBrandAdmin(BrandAdmin):
    inlines = [TruckBrandTypeRelationInline, TruckBrandCategoryRelationInline]


@admin.register(MotoBrand)
class MotoBrandAdmin(BrandAdmin):
    inlines = [MotoBrandTypeRelationInline, MotoBrandCategoryRelationInline]


@admin.register(SpecialBrand)
class SpecialBrandAdmin(BrandAdmin):
    inlines = [SpecialBrandTypeRelationInline, SpecialBrandCategoryRelationInline]


# Vehicle Types Admin (должны быть зарегистрированы до ModelAdmin из-за autocomplete_fields)
class VehicleTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'is_active')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)


@admin.register(CarType)
class CarTypeAdmin(VehicleTypeAdmin):
    pass


@admin.register(TruckType)
class TruckTypeAdmin(VehicleTypeAdmin):
    pass


@admin.register(MotoType)
class MotoTypeAdmin(VehicleTypeAdmin):
    pass


@admin.register(SpecialType)
class SpecialTypeAdmin(VehicleTypeAdmin):
    pass


# Vehicle Models Admin
class ModelAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'type', 'year_range', 'is_active', 'get_image_preview')
    list_filter = ('brand', 'type', 'is_active')
    search_fields = ('name', 'brand__name')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_image_preview',)
    autocomplete_fields = ['brand', 'type']

    def get_image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" />')
        return "-"

    get_image_preview.short_description = _("Изображение")

    def year_range(self, obj):
        return f"{obj.year_start}-{obj.year_end or _('н.в.')}"

    year_range.short_description = _("Годы выпуска")


@admin.register(CarModel)
class CarModelAdmin(ModelAdmin):
    list_display = ('name', 'brand', 'type', 'is_active', 'get_image_preview')
    list_filter = ('brand', 'type', 'is_active')
    search_fields = ('name', 'brand__name')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_image_preview',)

    def get_image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" />')
        return "-"

    get_image_preview.short_description = _("Изображение")


@admin.register(TruckModel)
class TruckModelAdmin(ModelAdmin):
    pass


@admin.register(MotoModel)
class MotoModelAdmin(ModelAdmin):
    pass


@admin.register(SpecialModel)
class SpecialModelAdmin(ModelAdmin):
    pass


# Vehicle Generations Admin
class GenerationAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_with_brand', 'year_range', 'is_active', 'get_image_preview')
    list_filter = ('model__brand', 'is_active')
    search_fields = ('name', 'model__name', 'model__brand__name')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_image_preview',)
    autocomplete_fields = ['model']

    def get_image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="100" />')
        return "-"

    get_image_preview.short_description = _("Изображение")

    def model_with_brand(self, obj):
        return f"{obj.model.brand.name} {obj.model.name}"

    model_with_brand.short_description = _("Модель")

    def year_range(self, obj):
        return f"{obj.year_start}-{obj.year_end or _('н.в.')}"

    year_range.short_description = _("Годы выпуска")


@admin.register(CarGeneration)
class CarGenerationAdmin(GenerationAdmin):
    pass


@admin.register(TruckGeneration)
class TruckGenerationAdmin(GenerationAdmin):
    list_display = GenerationAdmin.list_display + ('load_capacity',)


@admin.register(MotoGeneration)
class MotoGenerationAdmin(GenerationAdmin):
    list_display = GenerationAdmin.list_display + ('engine_volume', 'engine_power')


@admin.register(SpecialGeneration)
class SpecialGenerationAdmin(GenerationAdmin):
    list_display = GenerationAdmin.list_display + ('weight', 'power')


# Vehicle Type Relations Admin
class BrandTypeRelationAdmin(admin.ModelAdmin):
    list_display = ('brand', 'type', 'is_main')
    list_filter = ('brand', 'type', 'is_main')
    search_fields = ('brand__name', 'type__name')


@admin.register(CarBrandTypeRelation)
class CarBrandTypeRelationAdmin(BrandTypeRelationAdmin):
    pass


@admin.register(TruckBrandTypeRelation)
class TruckBrandTypeRelationAdmin(BrandTypeRelationAdmin):
    pass


@admin.register(MotoBrandTypeRelation)
class MotoBrandTypeRelationAdmin(BrandTypeRelationAdmin):
    pass


@admin.register(SpecialBrandTypeRelation)
class SpecialBrandTypeRelationAdmin(BrandTypeRelationAdmin):
    pass


# Brand Category Relations Admin
class BrandCategoryRelationAdmin(admin.ModelAdmin):
    list_display = ('brand', 'category', 'is_main')
    list_filter = ('brand', 'category', 'is_main')
    search_fields = ('brand__name', 'category__name')
    autocomplete_fields = ['brand', 'category']


@admin.register(CarBrandCategoryRelation)
class CarBrandCategoryRelationAdmin(BrandCategoryRelationAdmin):
    pass


@admin.register(TruckBrandCategoryRelation)
class TruckBrandCategoryRelationAdmin(BrandCategoryRelationAdmin):
    pass


@admin.register(MotoBrandCategoryRelation)
class MotoBrandCategoryRelationAdmin(BrandCategoryRelationAdmin):
    pass


@admin.register(SpecialBrandCategoryRelation)
class SpecialBrandCategoryRelationAdmin(BrandCategoryRelationAdmin):
    pass


# Accessories Admin
@admin.register(AccessoryCategory)
class AccessoryCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent', 'main_category', 'is_active')
    list_filter = ('is_active', 'parent', 'main_category')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['parent', 'main_category']


@admin.register(AccessoryBrand)
class AccessoryBrandAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'year_founded', 'is_active', 'get_logo_preview')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'country')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_logo_preview',)

    def get_logo_preview(self, obj):
        if obj.logo:
            return mark_safe(f'<img src="{obj.logo.url}" width="100" />')
        return "-"

    get_logo_preview.short_description = _("Логотип")


# Product Attributes Admin
class AttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1
    prepopulated_fields = {'slug': ('value',)}


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_filter', 'order')
    list_filter = ('is_filter',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_filter', 'order')
    inlines = [AttributeValueInline]


@admin.register(ProductAttributeValue)
class ProductAttributeValueAdmin(admin.ModelAdmin):
    list_display = ('attribute', 'value', 'slug')
    list_filter = ('attribute',)
    search_fields = ('value', 'attribute__name')
    prepopulated_fields = {'slug': ('value',)}
    autocomplete_fields = ['attribute']


# Модели и поколения автомобилей (пример для CarModel, аналогично для других)
class GenerationInline(admin.StackedInline):
    model = CarGeneration
    extra = 1
    fields = ('name', 'slug', 'year_from', 'year_to', 'image', 'is_active')


# Manufacturer Category Relations
@admin.register(ManufacturerCategoryRelation)
class ManufacturerCategoryRelationAdmin(admin.ModelAdmin):
    list_display = ('manufacturer', 'category', 'is_main')
    list_filter = ('manufacturer', 'category', 'is_main')
    search_fields = ('manufacturer__name', 'category__name')
    autocomplete_fields = ['manufacturer', 'category']


# Категории и бренды автохимии
@admin.register(OilAndChemistryCategory)
class OilAndChemistryCategoryAdmin(admin.ModelAdmin, ImagePreviewMixin):
    list_display = ('name', 'parent', 'is_active', 'get_image_preview')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_image_preview',)


@admin.register(OilAndChemistryBrand)
class OilAndChemistryBrandAdmin(admin.ModelAdmin, LogoPreviewMixin):
    list_display = ('name', 'country', 'is_active', 'get_logo_preview')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'country')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_logo_preview',)


# Категории и бренды ТО (аналогично для других категорий)
@admin.register(MaintenanceCategory)
class MaintenanceCategoryAdmin(admin.ModelAdmin, ImagePreviewMixin):
    list_display = ('name', 'parent', 'is_active', 'get_image_preview')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_image_preview',)


@admin.register(MaintenanceBrand)
class MaintenanceBrandAdmin(admin.ModelAdmin, LogoPreviewMixin):
    list_display = ('name', 'country', 'is_active', 'get_logo_preview')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'country')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_logo_preview',)


@admin.register(TireAndWheelCategory)
class TireAndWheelCategoryAdmin(admin.ModelAdmin, ImagePreviewMixin):
    list_display = ('name', 'parent', 'is_active', 'get_image_preview')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_image_preview',)


@admin.register(TireAndWheelBrand)
class TireAndWheelBrandAdmin(admin.ModelAdmin, LogoPreviewMixin):
    list_display = ('name', 'country', 'is_active', 'get_logo_preview')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'country')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_logo_preview',)


# Категории и бренды инструментов
@admin.register(ToolCategory)
class ToolCategoryAdmin(admin.ModelAdmin, ImagePreviewMixin):
    list_display = ('name', 'parent', 'is_active', 'get_image_preview')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_image_preview',)


@admin.register(ToolBrand)
class ToolBrandAdmin(admin.ModelAdmin, LogoPreviewMixin):
    list_display = ('name', 'country', 'is_active', 'get_logo_preview')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'country')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_logo_preview',)


# Категории и бренды автоэлектрики
@admin.register(AutoElectricCategory)
class AutoElectricCategoryAdmin(admin.ModelAdmin, ImagePreviewMixin):
    list_display = ('name', 'parent', 'is_active', 'get_image_preview')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_image_preview',)


@admin.register(AutoElectricBrand)
class AutoElectricBrandAdmin(admin.ModelAdmin, LogoPreviewMixin):
    list_display = ('name', 'country', 'is_active', 'get_logo_preview')
    list_filter = ('country', 'is_active')
    search_fields = ('name', 'country')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('get_logo_preview',)


@admin.register(PartSubcategory)
class PartSubcategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'parent_category', 'parent')
    list_filter = ('parent_category', 'parent')
    search_fields = ('name', 'slug')
    prepopulated_fields = {"slug": ("name",)}
    raw_id_fields = ('parent',)


class MaintenanceKitProductInline(admin.TabularInline):
    model = MaintenanceKitProduct
    extra = 1
    autocomplete_fields = ['product']


@admin.register(MaintenanceKit)
class MaintenanceKitAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'vehicle_type', 'get_car_brand', 'price',
        'old_price', 'is_active', 'product_count'
    ]
    list_filter = ['vehicle_type', 'is_active', 'car_brand']
    search_fields = ['name', 'description']
    filter_horizontal = ['car_models']
    inlines = [MaintenanceKitProductInline]
    readonly_fields = ['created_at']

    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'description', 'image')
        }),
        ('Цены', {
            'fields': ('price', 'old_price')
        }),
        ('Совместимость', {
            'fields': ('vehicle_type', 'car_brand', 'car_models')
        }),
        ('Статус', {
            'fields': ('is_active',)
        })
    )

    def get_car_brand(self, obj):
        return obj.car_brand.name if obj.car_brand else 'Универсальный'

    get_car_brand.short_description = 'Бренд авто'

    def product_count(self, obj):
        return obj.products.count()

    product_count.short_description = 'Кол-во товаров'

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        # Автоматически пересчитываем цену комплекта при изменении состава
        if change:
            form.instance.calculate_price()
            form.instance.save()


@admin.register(MaintenanceKitProduct)
class MaintenanceKitProductAdmin(admin.ModelAdmin):
    list_display = ['kit', 'product', 'quantity', 'is_required']
    list_filter = ['kit', 'is_required']
    search_fields = ['kit__name', 'product__name']


class MaintenanceTypeFilter(admin.SimpleListFilter):
    title = 'Тип расходника ТО'
    parameter_name = 'maintenance_type'

    def lookups(self, request, model_admin):
        return Product.MAINTENANCE_TYPES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(maintenance_type=self.value())
        return queryset


class ViscosityFilter(admin.SimpleListFilter):
    title = 'Вязкость масла'
    parameter_name = 'viscosity'

    def lookups(self, request, model_admin):
        viscosities = Product.objects.filter(
            maintenance_type='engine_oil',
            viscosity__isnull=False
        ).values_list('viscosity', flat=True).distinct()
        return [(v, v) for v in viscosities if v]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(viscosity=self.value())
        return queryset


@admin.register(CarModification)
class CarModificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'generation', 'engine_type', 'power', 'transmission')
    list_filter = ('generation__model__brand', 'generation__model', 'generation', 'engine_type', 'transmission')
    search_fields = ('name', 'generation__name', 'generation__model__name')
    autocomplete_fields = ['generation']

    fieldsets = (
        (_("Основная информация"), {
            'fields': ('generation', 'name', 'slug')
        }),
        (_("Технические характеристики"), {
            'fields': ('engine_type', 'engine_volume', 'power', 'transmission', 'drive_type', 'body_type')
        }),
    )


@admin.register(TruckModification)
class TruckModificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'generation', 'engine_type', 'engine_power')
    list_filter = ('generation__model__brand', 'generation__model', 'generation')
    autocomplete_fields = ['generation']


@admin.register(MotoModification)
class MotoModificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'generation', 'version_type')
    list_filter = ('generation__model__brand', 'generation__model', 'generation', 'version_type')
    autocomplete_fields = ['generation']


@admin.register(SpecialModification)
class SpecialModificationAdmin(admin.ModelAdmin):
    list_display = ('name', 'generation', 'equipment_level')
    list_filter = ('generation__model__brand', 'generation__model', 'generation', 'equipment_level')
    autocomplete_fields = ['generation']


# ============================================================================
# Скрытие неиспользуемых моделей из админки
# ============================================================================
# Эти модели не используются (0 записей), но могут понадобиться в будущем
# Чтобы показать их снова, закомментируйте соответствующие строки

# Аксессуары (не используются)
try:
    admin.site.unregister(AccessoryCategory)
    admin.site.unregister(AccessoryBrand)
except admin.sites.NotRegistered:
    pass

# Инструменты (не используются)
try:
    admin.site.unregister(ToolCategory)
    admin.site.unregister(ToolBrand)
except admin.sites.NotRegistered:
    pass

# Автоэлектрика (не используется)
try:
    admin.site.unregister(AutoElectricCategory)
    admin.site.unregister(AutoElectricBrand)
except admin.sites.NotRegistered:
    pass

# Шины и диски — характеристики зарегистрированы для поддержки кнопки "+" в inline

# Автохимия и масла (не используются)
try:
    admin.site.unregister(OilAndChemistryCategory)
    admin.site.unregister(OilAndChemistryBrand)
except admin.sites.NotRegistered:
    pass

# Для ТО (не используются)
try:
    admin.site.unregister(MaintenanceCategory)
    admin.site.unregister(MaintenanceBrand)
    admin.site.unregister(MaintenanceKit)
    admin.site.unregister(MaintenanceKitProduct)
except admin.sites.NotRegistered:
    pass

# Связи брендов с категориями (не используются активно)
try:
    admin.site.unregister(CarBrandTypeRelation)
    admin.site.unregister(TruckBrandTypeRelation)
    admin.site.unregister(MotoBrandTypeRelation)
    admin.site.unregister(SpecialBrandTypeRelation)
    admin.site.unregister(CarBrandCategoryRelation)
    admin.site.unregister(TruckBrandCategoryRelation)
    admin.site.unregister(MotoBrandCategoryRelation)
    admin.site.unregister(SpecialBrandCategoryRelation)
    admin.site.unregister(ManufacturerCategoryRelation)
except admin.sites.NotRegistered:
    pass

# Типы транспорта (CarType, TruckType, MotoType, SpecialType) должны оставаться
# зарегистрированными — на них ссылаются autocomplete_fields в CarModelAdmin,
# TruckModelAdmin, MotoModelAdmin, SpecialModelAdmin.

# Производители (не используются)
try:
    admin.site.unregister(Manufacturer)
except admin.sites.NotRegistered:
    pass

# Атрибуты товаров (не используются)
try:
    admin.site.unregister(ProductAttribute)
    admin.site.unregister(ProductAttributeValue)
except admin.sites.NotRegistered:
    pass

# Подкатегории запчастей (не используются)
try:
    admin.site.unregister(PartSubcategory)
except admin.sites.NotRegistered:
    pass


@admin.register(CarouselSlide)
class CarouselSlideAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'is_active', 'order', 'image_preview', 'created_at')
    list_editable = ('is_active', 'order', 'status')
    list_filter = ('is_active', 'status')
    search_fields = ('title',)
    ordering = ('order', 'created_at')
    fields = ('title', 'image', 'image_preview', 'url', 'status', 'is_active', 'order')
    readonly_fields = ('image_preview',)

    def image_preview(self, obj):
        if obj.image:
            return mark_safe(f'<img src="{obj.image.url}" width="160" style="object-fit: cover; border-radius: 6px;" />')
        return "—"
    image_preview.short_description = _("Предпросмотр")


class SiteDocumentAdminForm(forms.ModelForm):
    content = forms.CharField(
        label=_("Содержание"),
        widget=CKEditorUploadingWidget(),
        required=True,
    )

    class Meta:
        model = SiteDocument
        fields = '__all__'


@admin.register(SiteDocument)
class SiteDocumentAdmin(admin.ModelAdmin):
    form = SiteDocumentAdminForm
    list_display = ('get_doc_type_display', 'title', 'has_file', 'is_active', 'updated_at')
    list_editable = ('is_active',)
    list_filter = ('is_active', 'doc_type')
    search_fields = ('title',)
    readonly_fields = ('updated_at', 'file_preview')
    ordering = ('doc_type',)

    fieldsets = (
        (None, {
            'fields': ('doc_type', 'title', 'is_active', 'updated_at'),
        }),
        (_("Файл документа"), {
            'fields': ('file', 'file_preview'),
            'description': _("Загрузите PDF или другой файл. На странице документа появится кнопка скачивания."),
        }),
        (_("Содержание документа (HTML)"), {
            'fields': ('content',),
            'description': _("Можно заполнить вместо файла или дополнительно к нему."),
        }),
    )

    def get_doc_type_display(self, obj):
        return obj.get_doc_type_display()
    get_doc_type_display.short_description = _("Тип документа")
    get_doc_type_display.admin_order_field = 'doc_type'

    def has_file(self, obj):
        if obj.file:
            return mark_safe(f'<a href="{obj.file.url}" target="_blank">📎 {obj.file.name.split("/")[-1]}</a>')
        return "—"
    has_file.short_description = _("Файл")

    def file_preview(self, obj):
        if not obj.file:
            return "—"
        name = obj.file.name.split("/")[-1]
        url = obj.file.url
        if name.lower().endswith(".pdf"):
            return mark_safe(
                f'<a href="{url}" target="_blank" class="button">📄 Открыть PDF: {name}</a>'
            )
        return mark_safe(f'<a href="{url}" target="_blank">⬇ Скачать: {name}</a>')
    file_preview.short_description = _("Текущий файл")


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        (_("Реквизиты компании"), {
            'fields': ('company_name', 'inn'),
        }),
        (_("Контакты"), {
            'fields': ('email', 'phone', 'phone_display'),
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        obj, _ = SiteSettings.objects.get_or_create(pk=1)
        return self.changeform_view(request, str(obj.pk), extra_context=extra_context)
