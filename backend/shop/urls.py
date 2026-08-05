from django.urls import path
from . import views

app_name = 'shop'  # Добавляем пространство имен для URL

urlpatterns = [
    # Основные URL магазина
    path('', views.index, name='index'),
    path('search/', views.search_view, name='search'),

    # URL для категорий
    path('categories/', views.category_list, name='category_list'),
    path('category/<slug:slug>/', views.category_view, name='category'),

    # URL для товаров
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    # API для заказов и платежей
    path('api/order/create/', views.create_order, name='create_order'),
    path('api/payment/process/', views.process_payment, name='process_payment'),
    path('api/payment/status/<int:order_id>/', views.payment_status, name='payment_status'),

    # ===== Легковые автомобили =====
    path('cars/', views.cars_main, name='cars_main'),
    path('cars/brands/', views.car_brands, name='car_brands'),
    path('cars/brands/<slug:brand_slug>/', views.car_models, name='car_models'),
    path('cars/all-brands/<slug:category_slug>/', views.all_brands_category, name='all_brands_category'),

    # ===== Грузовики =====
    path('trucks/', views.TruckBrandListView.as_view(), name='truck_brand_list'),
    path('trucks/brands/<slug:slug>/', views.TruckBrandDetailView.as_view(), name='truck_brand_detail'),
    path('trucks/models/<slug:slug>/', views.TruckModelDetailView.as_view(), name='truck_model_detail'),
    path('trucks/generations/<slug:slug>/',
         views.TruckGenerationDetailView.as_view(),
         name='truck_generation_detail'),
    path('trucks/types/<slug:type_slug>/', views.truck_type_list, name='truck_type_list'),
    path('trucks/<slug:brand_slug>/category/<slug:category_slug>/',
         views.truck_category_parts,
         name='truck_category_parts'),

    # ===== Мототехника =====
    path('moto/', views.MotoBrandListView.as_view(), name='moto_brand_list'),
    path('moto/brands/<slug:slug>/', views.MotoBrandDetailView.as_view(), name='moto_brand_detail'),
    path('moto/models/<slug:slug>/', views.MotoModelDetailView.as_view(), name='moto_model_detail'),
    path('moto/categories/', views.moto_category_tree, name='moto_category_tree'),
    path('moto/categories/<slug:category_slug>/', views.moto_category_detail, name='moto_category_detail'),
    path('moto/category/<slug:category_slug>/brands/',
         views.MotoBrandListView.as_view(),
         name='moto_brands_by_category'),

    # ===== Спецтехника =====
    path('special/', views.SpecialBrandListView.as_view(), name='special_brand_list'),
    path('special/brands/<slug:slug>/', views.SpecialBrandDetailView.as_view(), name='special_brand_detail'),
    path('special/models/<slug:slug>/', views.SpecialModelDetailView.as_view(), name='special_model_detail'),
    path('special/types/', views.SpecialTypeListView.as_view(), name='special_type_list'),
    path('special/types/<slug:slug>/', views.SpecialTypeDetailView.as_view(), name='special_type_detail'),

    # ===== Аксессуары =====
    path('accessories/', views.AccessoryCategoryListView.as_view(), name='accessory_category_list'),
    path('accessories/brands/', views.AccessoryBrandListView.as_view(), name='accessory_brand_list'),

    # ===== Универсальные URL для брендов и товаров =====
    path('brands/<slug:brand_slug>/', views.brand_products, name='brand_products'),
    path('brands/<slug:brand_slug>/models/', views.brand_models, name='brand_models'),
    path('brands/<slug:brand_slug>/<slug:category_slug>/',
         views.brand_category_products,
         name='brand_category'),
    path('categories/avtohimiya-i-masla/', views.oil_chemistry_products, name='oil_chemistry_products'),
    path('brands/<slug:brand_slug>/', views.brand_products, name='brand_products'),
    path('brands/car/<slug:brand_slug>/', views.brand_products, name='car_brand_products'),
    path('brands/truck/<slug:brand_slug>/', views.brand_products, name='truck_brand_products'),
    path('brands/moto/<slug:brand_slug>/', views.brand_products, name='moto_brand_products'),
    path('brands/special/<slug:brand_slug>/', views.brand_products, name='special_brand_products'),

    # Отзывы
    path('product/<slug:product_slug>/review/', views.add_review, name='add_review'),
    path('review/<int:review_id>/helpful/', views.review_helpful_vote, name='review_helpful_vote'),

    # Документы и соглашения
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('personal-data/', views.personal_data, name='personal_data'),
    path('public-offer/', views.public_offer, name='public_offer'),
    path('buyer-rules/', views.buyer_rules, name='buyer_rules'),
    path('seller-rules/', views.seller_rules, name='seller_rules'),
    path('tech-recommendations/', views.tech_recommendations, name='tech_recommendations'),
    path('about/', views.about, name='about'),
    path('help/', views.help, name='help'),
    path('return-policy/', views.return_policy, name='return_policy'),



    path('new-products/', views.new_products, name='new_products'),
    path('sale-products/', views.sale_products, name='sale_products'),
    path('popular-products/', views.popular_products, name='popular_products'),
    path('track/click/', views.track_product_click, name='track_click'),
    #    path('track/cart-add/', views.track_cart_add, name='track_cart_add'),
    path('category/dlya-to/<str:vehicle_type>/<slug:brand_slug>/<slug:model_slug>/', views.select_generation,
         name='maintenance_select_generation'),

    path('category/dlya-to/<str:vehicle_type>/<slug:brand_slug>/<slug:model_slug>/<slug:generation_slug>/',
         views.maintenance_for_vehicle, name='maintenance_for_vehicle'),
    path('category/dlya-to/<str:vehicle_type>/', views.select_brand, name='maintenance_select_brand'),
    path('category/dlya-to/<str:vehicle_type>/<slug:brand_slug>/', views.select_model, name='maintenance_select_model'),
    path('category/dlya-to/<str:vehicle_type>/<slug:brand_slug>/<slug:model_slug>/<slug:generation_slug>/',
         views.maintenance_for_vehicle, name='maintenance_for_vehicle'),
    path('maintenance/selection/', views.maintenance_selection, name='maintenance_selection'),
    path('maintenance/<str:vehicle_type>/<str:brand_slug>/<str:model_slug>/years/', views.select_year,
         name='maintenance_select_year'),
    path('to/<str:vehicle_type>/<slug:brand_slug>/<slug:model_slug>/generations/',
         views.select_generation, name='select_generation'),

    path('slider-captcha/', views.slider_captcha_view, name='slider_captcha_view'),
    path('verify-slider-captcha/', views.verify_slider_captcha, name='verify_slider_captcha'),

    path('tag/<slug:slug>/', views.tag_detail, name='tag_detail'),

    # Путь: Марка → Модель → Поколение → Модификация
    path('<str:vehicle_type>/<slug:brand_slug>/<slug:model_slug>/<slug:generation_slug>/modifications/',
         views.select_modification, name='select_modification'),

    # Путь для выбора модификации (без товаров)
    path('<str:vehicle_type>/<slug:brand_slug>/<slug:model_slug>/<slug:generation_slug>/modifications/',
         views.select_modification, name='select_modification'),

    # Путь с модификацией - должен идти ДО общего пути
    path(
        'maintenance/<str:vehicle_type>/<slug:brand_slug>/<slug:model_slug>/<slug:generation_slug>/<slug:modification_slug>/',
        views.for_vehicle, name='for_vehicle_with_modification'),

    # Общий путь для for_vehicle - должен идти ПОСЛЕ всех специфичных
    path('maintenance/<str:vehicle_type>/<slug:brand_slug>/<slug:model_slug>/',
         views.for_vehicle, name='for_vehicle_without_generation'),

    path('maintenance/<str:vehicle_type>/<slug:brand_slug>/<slug:model_slug>/<slug:generation_slug>/',
         views.for_vehicle, name='for_vehicle'),
    path('set_preloader_shown/', views.set_preloader_shown, name='set_preloader_shown'),
    path('api/category-children/<slug:slug>/', views.category_children_api, name='category_children_api'),
]
