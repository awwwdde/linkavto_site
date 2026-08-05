from django.urls import path
from . import views

app_name = 'sellers'

urlpatterns = [
    path('become-seller/', views.become_seller, name='become_seller'),
    path('seller-login/', views.seller_login, name='seller_login'),
    path('seller-registration/', views.seller_registration, name='seller_registration'),
    path('seller-dashboard/', views.seller_dashboard, name='seller_dashboard'),

    # Публичная витрина продавца (для покупателей)
    path('store/<int:seller_id>/', views.seller_storefront, name='storefront'),

    # API endpoints
    path('api/send-verification-code/', views.send_verification_code, name='send_verification_code'),
    path('api/verify-code/', views.verify_code, name='verify_code'),
    path('api/seller-login/', views.seller_login_with_code, name='seller_login_with_code'),
    path('api/search-company/', views.search_company_by_inn, name='search_company_by_inn'),
    path('api/categories/', views.get_categories_json, name='get_categories_json'),
    path('api/suggest-category/', views.suggest_category, name='suggest_category'),

    # API endpoints для добавления товара
    path('api/categories/<int:category_id>/children/', views.get_category_children, name='get_category_children'),
    path('api/vin-info/', views.get_vin_info, name='get_vin_info'),
    path('api/vehicle-brands/', views.get_vehicle_brands, name='get_vehicle_brands'),
    path('api/vehicle-models/', views.get_vehicle_models, name='get_vehicle_models'),
    path('api/vehicle-generations/', views.get_vehicle_generations, name='get_vehicle_generations'),
    path('api/vehicle-modifications/', views.get_vehicle_modifications, name='get_vehicle_modifications'),


    path('dashboard/', views.seller_dashboard, name='dashboard'),
    path('products/', views.seller_products, name='products'),
    path('orders/', views.seller_orders, name='orders'),
    path('analytics/', views.seller_analytics, name='analytics'),
    path('delivery/', views.seller_delivery, name='delivery'),
    path('finances/', views.seller_finances, name='finances'),
    path('reviews/', views.seller_reviews, name='reviews'),
    path('settings/', views.seller_settings, name='settings'),
    path('help/', views.seller_help, name='help'),

    # Действия с товарами
    path('products/add/', views.product_add, name='product_add'),
    path('products/<int:product_id>/edit/', views.product_edit, name='product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
    path('products/bulk-action/', views.product_bulk_action, name='product_bulk_action'),
    path('products/<int:product_id>/duplicate/', views.product_duplicate, name='product_duplicate'),
    path('products/import/', views.product_import, name='product_import'),
    path('products/export/', views.product_export, name='product_export'),

    # Заказы
    path('orders/', views.seller_orders, name='orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('orders/bulk-action/', views.bulk_order_action, name='order_bulk_action'),
    path('orders/export/', views.orders_export, name='orders_export'),
    path('orders/analytics/', views.orders_analytics, name='orders_analytics'),

    # Аналитика
    path('advanced-analytics/', views.SellerAdvancedAnalyticsView.as_view(), name='advanced_analytics'),
    path('analytics/data/', views.AnalyticsDataView.as_view(), name='analytics_data'),
    path('analytics/run-algorithm/', views.RunMLAlgorithmView.as_view(), name='run_algorithm'),

    # Финансы
    path('finances/', views.FinanceDashboardView.as_view(), name='finances'),
    path('finances/transactions/', views.TransactionListView.as_view(), name='finance_transactions'),
    path('finances/payout-request/', views.PayoutRequestView.as_view(), name='payout_request'),
    path('finances/reports/', views.FinancialReportsView.as_view(), name='financial_reports'),
    path('finances/generate-report/', views.GenerateReportView.as_view(), name='generate_report'),
    path('finances/reports/', views.FinancialReportsView.as_view(), name='financial_reports'),
    path('finances/reports/generate/', views.GenerateReportView.as_view(), name='generate_report'),
    path('finances/reports/<int:report_id>/download/', views.DownloadReportView.as_view(), name='download_report'),
    path('finances/reports/<int:report_id>/details/', views.ReportDetailsView.as_view(), name='report_details'),
    path('finances/reports/<int:report_id>/delete/', views.DeleteReportView.as_view(), name='delete_report'),

    # Отзывы
    path('reviews/', views.ReviewsDashboardView.as_view(), name='reviews'),
    path('reviews/list/', views.ReviewsListView.as_view(), name='reviews_list'),
    path('reviews/analytics/', views.ReviewsAnalyticsView.as_view(), name='reviews_analytics'),
    path('reviews/<int:review_id>/response/', views.ReviewResponseView.as_view(), name='review_response'),
    path('reviews/<int:review_id>/report/', views.ReviewReportView.as_view(), name='review_report'),

    # Настройки
    path('settings/', views.SellerSettingsView.as_view(), name='settings'),
    path('settings/update/', views.UpdateSettingsView.as_view(), name='update_settings'),
    path('settings/integrations/update/', views.UpdateIntegrationsView.as_view(), name='update_integrations'),
    path('settings/generate-api-key/', views.GenerateApiKeyView.as_view(), name='generate_api_key'),
    path('settings/notifications/<int:notification_id>/read/', views.MarkNotificationReadView.as_view(),
         name='mark_notification_read'),
    path('settings/notifications/clear-all/', views.ClearAllNotificationsView.as_view(),
         name='clear_all_notifications'),

    # Профиль
    path('profile/', views.SellerProfileView.as_view(), name='profile'),
    path('profile/update-contact-data/', views.UpdateContactDataView.as_view(), name='update_contact_data'),
]