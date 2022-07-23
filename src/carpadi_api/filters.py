from django_filters import rest_framework as filters

from src.models.models import Activity, Disbursement, Transaction, Car, Trade, TransactionStatus, TransactionKinds, \
    TransactionTypes, ActivityTypes, TradeUnit, TradeStates, TransactionPin


class TransactionsFilter(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr='lte')
    transaction_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day__lte')
    transaction_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day__gte')
    transaction_date_range = filters.DateTimeFromToRangeFilter(field_name="created")
    kind = filters.ChoiceFilter(field_name="transaction_kind", lookup_expr='iexact', choices=TransactionKinds.choices)
    status = filters.ChoiceFilter(field_name="transaction_status", lookup_expr='iexact',
                                  choices=TransactionStatus.choices)
    type = filters.ChoiceFilter(field_name="transaction_type", lookup_expr='iexact', choices=TransactionTypes.choices)
    reference = filters.CharFilter(field_name="transaction_reference", lookup_expr='iexact')

    class Meta:
        model = Transaction
        fields = ['amount', 'created', 'kind', 'status', 'type', 'reference']


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
    type = filters.ChoiceFilter(field_name="activity_type",
                                lookup_expr='iexact', choices=ActivityTypes.choices)

    class Meta:
        model = Activity
        fields = ["created", "type"]


class TradeFilter(filters.FilterSet):
    make = filters.CharFilter(field_name="car__information__make", lookup_expr='iexact')

    class Meta:
        model = Trade
        fields = ['created', 'trade_status', 'make']


class TradeUnitFilter(filters.FilterSet):
    make = filters.CharFilter(field_name="trade__car__information__make", lookup_expr='iexact')
    trade = filters.CharFilter(field_name="trade__id", lookup_expr='iexact')
    status = filters.ChoiceFilter(field_name="trade__trade_status", lookup_expr='iexact', choices=TradeStates.choices)
    slots_quantity_gte = filters.NumberFilter(field_name="slots_quantity", lookup_expr='slots_quantity__gte')
    slots_quantity_lte = filters.NumberFilter(field_name="slots_quantity", lookup_expr='slots_quantity__lte')
    merchant = filters.CharFilter(field_name="merchant__id", lookup_expr="iexact")

    class Meta:
        model = TradeUnit
        fields = ['trade', ]


class TransactionPinFilter(filters.FilterSet):
    pin = filters.CharFilter(field_name="pin", lookup_expr='iexact')
    serial_number = filters.CharFilter(field_name="device_serial_number", lookup_expr='iexact')

    class Meta:
        model = TransactionPin
        fields = [ 'pin']