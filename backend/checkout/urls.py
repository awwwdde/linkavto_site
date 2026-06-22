from django.urls import path
from . import views

urlpatterns = [
    path('', checkout_view, name='checkout'),
    path('payment/', payment_view, name='payment'),
]
