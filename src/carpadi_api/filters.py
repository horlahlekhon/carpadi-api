from django_filters import rest_framework as filters

from src.models.models import Transactions

class TransactionsFilter(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr='lte')
    transaction_date_lte = filters.DateTimeFilter(field_name="ts_created", lookup_expr='lte')
    transaction_date_gte = filters.DateTimeFilter(field_name="ts_created", lookup_expr='gte')
    transaction_date_range = filters.DateTimeFromToRangeFilter(field_name="ts_created", lookup_expr='gte')

    class Meta:
        model = Transactions
        fields = ['wallet', 'amount', 'ts_created']
