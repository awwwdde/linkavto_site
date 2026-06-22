from django.contrib import admin
from django.utils.html import format_html
from .models import Seller, SellerCategory
from .models import SellerFinanceProfile, Transaction, Payout, FinancialReport
from .models import ProductReview, ReviewMedia, ReviewReport, SellerReviewSummary
from django.utils import timezone


class SellerCategoryInline(admin.TabularInline):
    model = SellerCategory
    extra = 1
    verbose_name = "Категория товаров"
    verbose_name_plural = "Категории товаров"


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = [
        'company_name',
        'contact_person',
        'legal_form',
        'status_badge',
        'created_at',
        'approved_at'
    ]
    list_filter = ['status', 'legal_form', 'created_at', 'is_active']
    search_fields = [
        'company_name',
        'contact_person',
        'inn',
        'ogrn',
        'user__email'
    ]
    readonly_fields = ['created_at', 'updated_at']
    inlines = [SellerCategoryInline]
    actions = ['approve_sellers', 'reject_sellers']

    fieldsets = (
        ('Основная информация', {
            'fields': (
                'user',
                'contact_person',
                'phone',
                'status',
                'is_active'
            )
        }),
        ('Информация о компании', {
            'fields': (
                'company_name',
                'store_name',
                'legal_form',
                'inn',
                'ogrn',
                'legal_address',
                'actual_address'
            )
        }),
        ('Дополнительная информация', {
            'fields': (
                'product_info',
                'product_count',
                'api_data_text_display',
                'api_data'
            )
        }),
        ('Системная информация', {
            'fields': (
                'created_at',
                'updated_at',
                'approved_at',
                'notes'
            ),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['created_at', 'updated_at', 'api_data_text_display']

    def status_badge(self, obj):
        status_colors = {
            'pending': 'orange',
            'approved': 'green',
            'rejected': 'red',
            'suspended': 'gray'
        }
        return format_html(
            '<span style="padding: 5px 10px; border-radius: 15px; color: white; background-color: {};">{}</span>',
            status_colors.get(obj.status, 'gray'),
            obj.get_status_display()
        )

    status_badge.short_description = 'Статус'
    
    def api_data_text_display(self, obj):
        """Отображение данных из API ФНС в текстовом формате"""
        if not obj.api_data:
            return "Данные отсутствуют"
        
        # Если данные сохранены в формате {'text': '...'}
        if isinstance(obj.api_data, dict) and 'text' in obj.api_data:
            return format_html('<pre style="white-space: pre-wrap; max-height: 400px; overflow-y: auto;">{}</pre>', 
                             obj.api_data['text'])
        
        # Если данные в другом формате, пытаемся их отформатировать
        return format_html('<pre style="white-space: pre-wrap; max-height: 400px; overflow-y: auto;">{}</pre>', 
                          str(obj.api_data))
    
    api_data_text_display.short_description = 'Данные из API ФНС'

    def approve_sellers(self, request, queryset):
        updated = queryset.update(status='approved', approved_at=timezone.now())
        self.message_user(request, f'{updated} продавцов одобрено.')

    approve_sellers.short_description = "Одобрить выбранных продавцов"

    def reject_sellers(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} продавцов отклонено.')

    reject_sellers.short_description = "Отклонить выбранных продавцов"


@admin.register(SellerCategory)
class SellerCategoryAdmin(admin.ModelAdmin):
    list_display = ['seller', 'category', 'created_at']
    list_filter = ['category', 'created_at']
    search_fields = ['seller__company_name', 'category__name']


@admin.register(SellerFinanceProfile)
class SellerFinanceProfileAdmin(admin.ModelAdmin):
    list_display = ['seller', 'balance', 'hold_amount', 'available_balance']
    search_fields = ['seller__company_name']


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['seller', 'transaction_type', 'amount', 'status', 'transaction_date']
    list_filter = ['transaction_type', 'status', 'transaction_date']
    search_fields = ['seller__company_name', 'reference_id']


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ['seller', 'amount', 'status', 'requested_at']
    list_filter = ['status', 'payout_method']
    search_fields = ['seller__company_name']


@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ['seller', 'report_type', 'period_start', 'period_end', 'net_profit']
    list_filter = ['report_type']
    search_fields = ['seller__company_name']


# Отзывы

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'status', 'created_at', 'has_seller_response']
    list_filter = ['status', 'rating', 'created_at', 'is_verified_purchase']
    search_fields = ['product__name', 'user__username', 'comment']
    readonly_fields = ['created_at', 'updated_at']

    def has_seller_response(self, obj):
        return bool(obj.seller_response)

    has_seller_response.boolean = True
    has_seller_response.short_description = 'Есть ответ'


@admin.register(ReviewMedia)
class ReviewMediaAdmin(admin.ModelAdmin):
    list_display = ['review', 'media_type', 'uploaded_at', 'is_approved']
    list_filter = ['media_type', 'is_approved']


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ['review', 'report_type', 'status', 'created_at']
    list_filter = ['report_type', 'status']
    actions = ['mark_as_reviewed']


@admin.register(SellerReviewSummary)
class SellerReviewSummaryAdmin(admin.ModelAdmin):
    list_display = ['seller', 'total_reviews', 'average_rating', 'response_rate']
    readonly_fields = ['last_calculated']
