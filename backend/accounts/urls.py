# accounts/urls.py
from django.urls import path
from . import views
from .views import logout_view

app_name = 'accounts'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_edit, name='profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('history/', views.order_history, name='order_history'),
    path('logout/', logout_view, name='logout'),
    path('send-password-code/', views.send_password_code, name='send_password_code'),
    path('verify-password-code/', views.verify_password_code, name='verify_password_code'),
    path('set-new-password/', views.set_new_password, name='set_new_password'),
    path('authenticate/', views.authenticate_user, name='authenticate'),
    path('register/', views.register_user, name='register'),
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('password_reset/', views.password_reset_request, name='password_reset_request'),
    path('verify_reset_code/', views.verify_reset_code, name='verify_reset_code'),
    path('password_reset_complete/', views.password_reset_complete, name='password_reset_complete'),
    path('addresses/', views.get_addresses, name='get_addresses'),
    path('get_addresses_count/', views.get_addresses_count, name='get_addresses_count'),
    path('save_address/', views.save_address, name='save_address'),
    path('save_address_to_session/', views.save_address_to_session, name='save_address_to_session'),
    path('get_address_from_session/', views.get_address_from_session, name='get_address_from_session'),
    path('delete_address_from_session/', views.delete_address_from_session, name='delete_address_from_session'),
    path('set_default_address/<int:address_id>/', views.set_default_address, name='set_default_address'),
    path('delete_address/<int:address_id>/', views.delete_address, name='delete_address'),
    path('get_selected_address/', views.get_selected_address, name='get_selected_address'),
    path('save_selected_address/', views.save_selected_address, name='save_selected_address'),
    path('delete_avatar/', views.delete_avatar, name='delete_avatar'),
    path('upload_profile_photo/', views.upload_profile_photo, name='upload_profile_photo'),
    path('get-default-address/', views.get_default_address, name='get_default_address'),
    path('my-reviews/', views.my_reviews, name='my_reviews'),
    path('delete-review/<int:review_id>/', views.delete_review, name='delete_review'),
    path('send_verification_code/', views.send_verification_code, name='send_verification_code'),
    path('verify_code_login/', views.verify_code_and_login, name='verify_code_login'),
    path('register_with_code/', views.register_with_code, name='register_with_code'),
    path('reviews/edit/<int:review_id>/', views.edit_review, name='edit_review'),
    # API для пунктов выдачи
    path('api/pickup-points/', views.get_pickup_points, name='get_pickup_points'),
    path('api/pickup-points/<str:provider>/<str:code>/', views.get_pickup_point_details, name='get_pickup_point_details'),

]
