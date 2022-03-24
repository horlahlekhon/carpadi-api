from dataclasses import fields
from django_filters import rest_framework as filters

from src.models.models import Transaction, Car, Trade


class TransactionsFilter(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr='lte')
    transaction_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day_lte')
    transaction_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day_gte')
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

class TradesFilter(filters.FilterSet):
    trade_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day_lte')
    trade_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day_gte')
    trade_date_range = filters.DateTimeFromToRangeFilter(field_name="created")
    share_percentage_lte = filters.NumberFilter(field_name="share_percentage", lookup_expr="lte")
    share_percentage_gte = filters.NumberFilter(field_name="share_percentage", lookup_expr="gte")

    class Meta:
        model = Trade
        fields = ["created", "share_percentage"]
