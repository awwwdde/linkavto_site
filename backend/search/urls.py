from django.urls import path
from . import views
from .views import SearchHistoryAPIView


app_name = 'search'

urlpatterns = [
    path('', views.search_view, name='search'),
    path('autocomplete/', views.autocomplete_view, name='autocomplete'),
    path('search/clear_history/', views.clear_search_history, name='clear_search_history'),
    path('api/search/history/', SearchHistoryAPIView.as_view(), name='search-history-api'),
    path('api/history/', views.SearchHistoryAPIView.as_view(), name='api_history'),
    path('api/save_selection/', views.save_search_selection, name='save_search_selection'),
    path('delete_query/<int:query_id>/', views.delete_search_query, name='delete_search_query'),
    path('clear_history/', views.clear_search_history, name='clear_search_history'),

]