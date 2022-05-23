from django_filters import rest_framework as filters

from src.models.models import Activity, Disbursement, Transaction, Car, Trade


class TransactionsFilter(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr='lte')
    transaction_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day__lte')
    transaction_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day__gte')
    transaction_date_range = filters.DateTimeFromToRangeFilter(field_name="created")

    class Meta:
        model = Transaction
        fields = ['amount', 'created']


class CarsFilter(filters.FilterSet):
    status = filters.ChoiceFilter(field_name="status", lookup_expr="iexact")
    brand__name = filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Car
        fields = ["status", "brand__name"]


class DisbursementFilter(filters.FilterSet):
    disbursement_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day__lte')
    disbursement_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day__gte')
    disbursement_date_range = filters.DateTimeFromToRangeFilter(field_name="created")
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr='lte')

    class Meta:
        model = Disbursement
        fields = ["created", "amount"]


class ActivityFilter(filters.FilterSet):
    activity_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day__gt')
    activity_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day__gte')
    activity_date_range = filters.DateTimeFromToRangeFilter(field_name="created")
    activity_type = filters.CharFilter(field_name="activity_type", lookup_expr='iexact')

    class Meta:
        model = Activity
        fields = ["created", "activity_type"]


class TradeFilter(filters.FilterSet):
    make = filters.CharFilter(field_name="car__information__make", lookup_expr='iexact')

    class Meta:
        model = Trade
        fields = ['created', 'trade_status', 'make']

