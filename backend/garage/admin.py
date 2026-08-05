from django.contrib import admin
from django.utils.html import format_html
from .models import Vehicle, VehicleNote
from .forms import VehicleAdminForm


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    form = VehicleAdminForm
    
    list_display = ['get_display_name_admin', 'user', 'get_brand_display', 'get_model_display', 'vin', 'license_plate', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['vin', 'license_plate', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'get_current_data']
    
    fieldsets = (
        ('Владелец', {
            'fields': ('user',)
        }),
        ('Пользовательская информация', {
            'fields': ('custom_image', 'is_active')
        }),
        ('Выбор транспорта', {
            'fields': (
                'vehicle_type',
                'brand_choice',
                'model_choice',
                'generation_choice',
                'modification_choice',
            ),
            'description': 'Выберите тип транспорта, затем марку, модель, поколение и модификацию'
        }),
        ('Скрытые поля (автозаполнение)', {
            'fields': (
                'brand_content_type', 'brand_object_id',
                'model_content_type', 'model_object_id',
                'generation_content_type', 'generation_object_id',
                'modification_content_type', 'modification_object_id',
            ),
            'classes': ('collapse',)
        }),
        ('Идентификация', {
            'fields': ('vin', 'license_plate', 'year')
        }),
        ('Метаданные', {
            'fields': ('created_at', 'updated_at', 'get_current_data'),
            'classes': ('collapse',)
        }),
    )
    
    class Media:
        js = ('admin/js/jquery.init.js', 'admin/js/garage_vehicle_admin.js',)
        css = {
            'all': ('admin/css/garage_vehicle_admin.css',)
        }
    
    def get_display_name_admin(self, obj):
        return obj.get_display_name()
    get_display_name_admin.short_description = 'Название'

    def get_brand_display(self, obj):
        """Отображение марки"""
        if obj.brand:
            return format_html('<strong>{}</strong>', str(obj.brand))
        return '-'
    get_brand_display.short_description = 'Марка'
    
    def get_model_display(self, obj):
        """Отображение модели"""
        if obj.vehicle_model:
            return format_html('<strong>{}</strong>', str(obj.vehicle_model))
        return '-'
    get_model_display.short_description = 'Модель'
    
    def get_current_data(self, obj):
        """Показывает текущие выбранные данные"""
        if not obj.pk:
            return '-'
        
        data = []
        if obj.brand:
            data.append(f"<strong>Марка:</strong> {obj.brand}")
        if obj.vehicle_model:
            data.append(f"<strong>Модель:</strong> {obj.vehicle_model}")
        if obj.generation:
            data.append(f"<strong>Поколение:</strong> {obj.generation}")
        if obj.modification:
            data.append(f"<strong>Модификация:</strong> {obj.modification}")
        
        if data:
            return format_html('<br>'.join(data))
        return 'Данные не заполнены'
    
    get_current_data.short_description = 'Текущие данные'


@admin.register(VehicleNote)
class VehicleNoteAdmin(admin.ModelAdmin):
    list_display = ['title', 'vehicle', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title', 'content', 'vehicle__vin', 'vehicle__license_plate']
    readonly_fields = ['created_at', 'updated_at']
