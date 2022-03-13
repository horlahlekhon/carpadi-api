from django_filters import rest_framework as filters

from src.models.models import Transactions, Car


class TransactionsFilter(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr='lte')
    transaction_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day_lte')
    transaction_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day_gte')
    transaction_date_range = filters.DateTimeFromToRangeFilter(field_name="created")

    class Meta:
        model = Transactions
        fields = ['amount', 'created']


class CarsFilter(filters.FilterSet):
    status = filters.ChoiceFilter(field_name="status", lookup_expr="iexact")
    brand__name = filters.CharFilter(lookup_expr="iexact")

    class Meta:
        model = Car
        fields = ["status", "brand__name"]
