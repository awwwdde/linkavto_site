from django.urls import path

from . import views

app_name = 'api'

urlpatterns = [
    path('home/', views.home, name='home'),
    path('categories/', views.categories, name='categories'),
    path('products/', views.product_list, name='product-list'),
    path('products/<slug:slug>/', views.product_detail, name='product-detail'),
    path('cart/', views.cart_detail, name='cart-detail'),
    path('cart/add/<int:product_id>/', views.cart_add, name='cart-add'),
    path('cart/remove/<int:product_id>/', views.cart_remove, name='cart-remove'),
    path('cart/clear/', views.cart_clear, name='cart-clear'),
]
