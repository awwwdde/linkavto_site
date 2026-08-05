from django.urls import path
from . import views
from .services import validate_vin_view, validate_license_plate_view

app_name = 'garage'

urlpatterns = [
    # Основные страницы
    path('', views.garage_list, name='list'),
    path('add/', views.vehicle_add, name='add'),
    path('<int:vehicle_id>/', views.vehicle_detail, name='detail'),
    path('<int:vehicle_id>/edit/', views.vehicle_edit, name='edit'),
    path('<int:vehicle_id>/delete/', views.vehicle_delete, name='delete'),
    path('<int:vehicle_id>/update-image/', views.vehicle_update_image, name='update_image'),
    path('<int:vehicle_id>/products/', views.vehicle_products, name='vehicle_products'),
    
    # API для валидации
    path('api/validate-vin/', validate_vin_view, name='validate_vin'),
    path('api/validate-plate/', validate_license_plate_view, name='validate_license_plate'),
    
    # API для получения данных автомобилей
    path('api/brands/', views.get_brands, name='get_brands'),
    path('api/models/', views.get_models, name='get_models'),
    path('api/generations/', views.get_generations, name='get_generations'),
    path('api/modifications/', views.get_modifications, name='get_modifications'),
]
