from django_filters import rest_framework as filters

from src.models.models import Notifications


class NotificationsFilter(filters.FilterSet):
    user = filters.CharFilter(field_name="user", lookup_expr='iexact')
    read = filters.BooleanFilter(field_name="read", lookup_expr='exact')

    class Meta:
        model = Notifications
        fields = ('is_read', 'is_active', 'notice_type', 'title')
