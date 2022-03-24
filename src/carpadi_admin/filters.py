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


class TradesFilterAdmin(filters.FilterSet):
    trade_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day_lte')
    trade_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day_gte')
    trade_date_range = filters.DateTimeFromToRangeFilter(field_name="created")

    share_percentage_lte = filters.NumberFilter(field_name="share_percentage", lookup_expr="lte")
    share_percentage_gte = filters.NumberFilter(field_name="share_percentage", lookup_expr="gte")

    merchant = filters.UUIDFilter(field_name="merchant")

    car = filters.UUIDFilter(field_name="car")
    # car = filters.UUIDFilter(field_name="car") Todo Filter on Car brand

    class Meta:
        model = Trade
        fields = ["created", "share_percentage", "merchant", "car"]


# class CarMerchantFilerAdmin(filters.FilterSet):
#     ...
