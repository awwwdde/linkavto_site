from django.contrib import admin
from django.db.models import Sum, F
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Order, OrderItem
from import_export import resources
from import_export.admin import ExportActionMixin
from django.contrib.admin import SimpleListFilter


class OrderResource(resources.ModelResource):
    class Meta:
        model = Order
        fields = ('id', 'name', 'email', 'phone', 'get_total_cost', 'status', 'created_at')
        export_order = fields


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    readonly_fields = ['product_link', 'price', 'quantity', 'get_cost']
    extra = 0
    classes = ['collapse']

    # Улучшенные подписи полей
    verbose_name = _('Позиция заказа')
    verbose_name_plural = _('Позиции заказа')

    def product_link(self, obj):
        url = reverse('admin:shop_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)

    product_link.short_description = _('Товар')

    def get_cost(self, obj):
        if obj and obj.price:
            return f"{obj.get_cost()} ₽"
        return "0 ₽"

    get_cost.short_description = _('Сумма')


class TotalCostFilter(SimpleListFilter):
    title = _('Сумма заказа')
    parameter_name = 'total_cost'

    def lookups(self, request, model_admin):
        return (
            ('0-5000', _('До 5 000 ₽')),
            ('5000-20000', _('5 000 - 20 000 ₽')),
            ('20000+', _('Более 20 000 ₽')),
        )

    def queryset(self, request, queryset):
        if self.value() == '0-5000':
            return queryset.filter(total__lte=5000)
        if self.value() == '5000-20000':
            return queryset.filter(total__gt=5000, total__lte=20000)
        if self.value() == '20000+':
            return queryset.filter(total__gt=20000)


@admin.register(Order)
class OrderAdmin(ExportActionMixin, admin.ModelAdmin):
    # Метаданные
    list_display = [
        'id', 'customer_info', 'created_short',
        'total_cost', 'payment_status', 'status_colored'
    ]
    list_filter = [
        'status', 'paid',
        ('created_at', admin.DateFieldListFilter),
        TotalCostFilter,
    ]
    resource_class = OrderResource
    search_fields = ['name', 'email', 'phone', 'id']
    inlines = [OrderItemInline]
    readonly_fields = ['created_at', 'updated_at', 'total_cost', 'order_items_list']
    actions = ['mark_as_paid', 'mark_as_shipped']
    list_select_related = ['user']
    autocomplete_fields = ['user']

    # Группировка полей в форме редактирования
    fieldsets = (
        (_('Клиент'), {
            'fields': ('user', ), # , 'customer_info', 'contact_details'
        }),
        (_('Доставка'), {
            'fields': ('address', 'comment'),
        }),
        (_('Статус заказа'), {
            'fields': ('paid', 'status', 'total_cost'),
        }),
        (_('Дополнительно'), {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'session_key'),
        }),
    )

    # Кастомные методы для отображения
    def customer_info(self, obj):
        return format_html(
            "{}<br>{}<br>{}",
            obj.name,
            obj.phone,
            obj.email
        )

    customer_info.short_description = _('Клиент')

    def created_short(self, obj):
        return obj.created_at.strftime("%d.%m.%Y %H:%M")

    created_short.short_description = _('Создан')
    created_short.admin_order_field = 'created_at'

    def total_cost(self, obj):
        return f"{obj.get_total_cost()} ₽"

    total_cost.short_description = _('Сумма')
    total_cost.admin_order_field = 'total'

    def payment_status(self, obj):
        return _("✅ Оплачен") if obj.paid else _("❌ Не оплачен")

    payment_status.short_description = _('Оплата')

    def status_colored(self, obj):
        colors = {
            'processing': 'blue',
            'shipped': 'orange',
            'delivered': 'green',
            'canceled': 'red'
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors[obj.status],
            obj.get_status_display()
        )

    status_colored.short_description = _('Статус')

    # Действия администратора
    @admin.action(description=_('Пометить как оплаченные'))
    def mark_as_paid(self, request, queryset):
        updated = queryset.update(paid=True)
        self.message_user(request, _(f"{updated} заказов помечено как оплаченные"))

    @admin.action(description=_('Пометить как отправленные'))
    def mark_as_shipped(self, request, queryset):
        updated = queryset.filter(paid=True).update(status='shipped')
        self.message_user(request, _(f"{updated} заказов отправлено"))

    # Дополнительные поля
    def order_items_list(self, obj):
        items = obj.items.select_related('product')
        return format_html("<br>".join(
            f"{item.product.name} - {item.quantity} × {item.price} ₽"
            for item in items
        ))

    order_items_list.short_description = _('Состав заказа')

    # Права доступа
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('orders.delete_order')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(status__in=['processing', 'shipped'])
        return qs

    class Media:
        css = {
            'all': ('css/admin/orders.css',)
        }