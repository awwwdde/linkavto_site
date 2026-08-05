from django.contrib import admin
from .models import SearchQuery


@admin.register(SearchQuery)
class SearchQueryAdmin(admin.ModelAdmin):
    list_display = ('query', 'results_count', 'user', 'created_at')
    list_filter = ('is_autocomplete', 'created_at')
    search_fields = ('query', 'user__username')
    date_hierarchy = 'created_at'
