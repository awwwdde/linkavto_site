from django.urls import path
from . import views


app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('success/<int:order_id>/', views.order_success, name='order_success'),  # Добавляем параметр
    path('fail/<int:order_id>/', views.payment_fail, name='payment_fail'),  # Добавляем маршрут для неудачной оплаты
    path('my-orders/', views.my_orders, name='my_orders'),
    path('my-orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('my-orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('api/orders/count/', views.get_orders_count, name='get_orders_count'),
    path('api/payment/tbank/notify/', views.tbank_notify, name='tbank_notify'),  # Добавляем маршрут для уведомлений

]
