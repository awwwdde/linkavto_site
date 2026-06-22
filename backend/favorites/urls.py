from django.urls import path
from . import views

app_name = 'favorites'

urlpatterns = [
    path('list/', views.favorites_list, name='list'),
    path('toggle/<int:product_id>/', views.toggle_favorites, name='toggle'),
    path('sync/', views.sync_favorites, name='sync'),
    path('ids/', views.get_favorite_ids, name='ids'),
    path('favorites/toggle/<int:product_id>/', views.toggle_favorites, name='toggle_favorites'),
    path('status/', views.favorites_status, name='status'),
    path('get_favorite_ids/', views.get_favorite_ids, name='get_favorite_ids'),
    path('count/', views.favorite_count, name='count'),

]

