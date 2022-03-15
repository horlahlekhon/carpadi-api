from django_filters import rest_framework as filters

from src.models.models import Transactions, Wallet


class TransactionsFilterAdmin(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr='lte')

    transaction_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day_lte')
    transaction_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day_gte')
    transaction_date_range = filters.DateTimeFromToRangeFilter(field_name="created")

    class Meta:
        model = Transactions
        fields = ['wallet', 'amount', 'created']


class WalletFilterAdmin(filters.FilterSet):
    min_balance = filters.NumberFilter(field_name="balance", lookup_expr='gte')
    max_balance = filters.NumberFilter(field_name="balance", lookup_expr='lte')

    created_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day_lte')
    created_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day_gte')
    created_date_range = filters.DateTimeFromToRangeFilter(field_name="created")

    updated_date_lte = filters.DateTimeFilter(field_name="modified", lookup_expr='day_lte')
    updated_date_gte = filters.DateTimeFilter(field_name="modified", lookup_expr='day_gte')
    updated_date_range = filters.DateTimeFromToRangeFilter(field_name="modified")

    merchant = filters.UUIDFilter(field_name="merchant")

    class Meta:
        model = Wallet
        fields = ['created', 'modified', 'balance', 'merchant']
