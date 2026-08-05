from django.urls import path
from . import views

app_name = 'cart'  # Это критически важно для namespace

urlpatterns = [
    path('add/<int:product_id>/', views.cart_add, name='cart_add'),
    path('remove/<int:product_id>/', views.cart_remove, name='cart_remove'),
    path('', views.cart_detail, name='cart_detail'),
    path('decrease/<int:product_id>/', views.cart_decrease, name='cart_decrease'),
    path('clear/', views.cart_clear, name='cart_clear'),
    path('update/<int:product_id>/', views.cart_update, name='cart_update'),
    path('get_cart_items/', views.get_cart_items, name='get_cart_items'),
    path('count/', views.cart_count, name='cart_count'),


]





