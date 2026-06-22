from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Address
from shop.models import Review


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'full_address', 'is_default', 'created_at')
    list_filter = ('is_default', 'created_at')
    search_fields = ('user__username', 'full_address', 'postal_code')
    raw_id_fields = ('user',)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_published', 'created_at', 'has_image')
    list_filter = ('rating', 'is_published', 'created_at')
    search_fields = ('product__name', 'user__username', 'comment')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('is_published',)
    raw_id_fields = ('product', 'user')
    date_hierarchy = 'created_at'

    fieldsets = (
        (None, {
            'fields': ('product', 'user', 'rating', 'is_published')
        }),
        (_('Содержание'), {
            'fields': ('comment', 'image')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def has_image(self, obj):
        return bool(obj.image)

    has_image.boolean = True
    has_image.short_description = _('Есть фото')
