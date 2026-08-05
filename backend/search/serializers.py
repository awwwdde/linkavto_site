from rest_framework import serializers
from .models import SearchQuery


class SearchHistorySerializer(serializers.ModelSerializer):
    display_query = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()

    class Meta:
        model = SearchQuery
        fields = ['id', 'query', 'display_query', 'created_at', 'is_vin_search', 'can_delete']
        read_only_fields = fields

    def get_display_query(self, obj):
        return obj.display_query

    def get_can_delete(self, obj):
        # Всегда можно удалять свои запросы
        return True
