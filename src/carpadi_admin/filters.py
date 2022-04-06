from django_filters import rest_framework as filters

from src.models.models import Transaction, Wallet, Trade


class TransactionsFilterAdmin(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr='lte')

    transaction_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day_lte')
    transaction_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day_gte')
    transaction_date_range = filters.DateTimeFromToRangeFilter(field_name="created")

    class Meta:
        model = Transaction
        fields = ['wallet', 'amount', 'created']
        ref_name = "transactions_admin_serializer"


class WalletFilterAdmin(filters.FilterSet):
    min_balance = filters.NumberFilter(field_name="balance", lookup_expr='gte')
    max_balance = filters.NumberFilter(field_name="balance", lookup_expr='lte')
    balance_range = filters.NumericRangeFilter(field_name="balance")

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


# class CarMerchantFilerAdmin(filters.FilterSet):
#     ...

class TradeFilterAdmin(filters.FilterSet):
    min_sale_price = filters.NumberFilter(field_name="min_sale_price", lookup_expr='gte')
    max_sale_price = filters.NumberFilter(field_name="max_sale_price", lookup_expr='lte')
    sales_price_range = filters.NumericRangeFilter(field_name="max_sale_price")

    created_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day_lte')
    created_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day_gte')
    created_date_range = filters.DateTimeFromToRangeFilter(field_name="created")

    updated_date_lte = filters.DateTimeFilter(field_name="modified", lookup_expr='day_lte')
    updated_date_gte = filters.DateTimeFilter(field_name="modified", lookup_expr='day_gte')
    updated_date_range = filters.DateTimeFromToRangeFilter(field_name="modified")

    class Meta:
        model = Trade
        fields = ['created', 'modified', 'min_sale_price', 'max_sale_price']