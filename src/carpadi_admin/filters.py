from django.db.models import QuerySet, F, Q
from django_filters import rest_framework as filters

from src.models.models import (
    Transaction,
    Wallet,
    Trade,
    Disbursement,
    Activity,
    SpareParts,
    CarProduct,
    CarFeature,
    VehicleInfo,
    TradeStates,
    CarMerchant, UserStatusFilterChoices, TradeUnit,
)


class TransactionsFilterAdmin(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr='lte')

    transaction_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day__lte')
    transaction_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day__gte')
    transaction_date_range = filters.DateTimeFromToRangeFilter(field_name="created")

    class Meta:
        model = Transaction
        fields = ['wallet', 'amount', 'created']
        ref_name = "transactions_admin_serializer"


class WalletFilterAdmin(filters.FilterSet):
    min_balance = filters.NumberFilter(field_name="balance", lookup_expr='gte')
    max_balance = filters.NumberFilter(field_name="balance", lookup_expr='lte')
    balance_range = filters.NumericRangeFilter(field_name="balance")

    created_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day__lte')
    created_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day__gte')
    created_date_range = filters.DateTimeFromToRangeFilter(field_name="created")

    updated_date_lte = filters.DateTimeFilter(field_name="modified", lookup_expr='day__lte')
    updated_date_gte = filters.DateTimeFilter(field_name="modified", lookup_expr='day__gte')
    updated_date_range = filters.DateTimeFromToRangeFilter(field_name="modified")

    merchant = filters.UUIDFilter(field_name="merchant")

    class Meta:
        model = Wallet
        fields = ['created', 'modified', 'balance', 'merchant']


class DisbursementFilterAdmin(filters.FilterSet):
    disbursement_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day__lte')
    disbursement_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day__gte')
    disbursement_date_range = filters.DateTimeFromToRangeFilter(field_name="created")

    min_disbursement = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_disbursement = filters.NumberFilter(field_name="amount", lookup_expr='lte')
    disbursement_range = filters.NumericRangeFilter(field_name="amount")

    trade_unit = filters.UUIDFilter(field_name="trade_unit__trade")

    class Meta:
        model = Disbursement
        fields = ["created", "amount", "trade_unit__trade"]


class ActivityFilterAdmin(filters.FilterSet):
    activity_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day__lte')
    activity_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day__gte')
    activity_date_range = filters.DateTimeFromToRangeFilter(field_name="created")

    actvity_type = filters.CharFilter(field_name="actvity_type")

    class Meta:
        model = Activity
        fields = ["created", "activity_type"]


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

    trade_status = filters.ChoiceFilter(field_name="trade_status", lookup_expr='iexact', choices=TradeStates.choices)

    class Meta:
        model = Trade
        fields = ['created', 'modified', 'min_sale_price', 'max_sale_price']


class SparePartsFilter(filters.FilterSet):
    car_brand = filters.CharFilter(field_name="car_brand")

    class Meta:
        model = SpareParts
        fields = ["car_brand"]


class VehicleInfoFilter(filters.FilterSet):
    class Meta:
        model = VehicleInfo
        fields = ["transmission", "car_type", "fuel_type", 'make', 'model', 'year']


class CarMerchantFilter(filters.FilterSet):
    trading_status = filters.ChoiceFilter(method="trading_status_filter", choices=UserStatusFilterChoices.choices)

    def trading_status_filter(self, queryset, name, value):
        merchants: QuerySet = TradeUnit.objects\
            .filter(merchant__user__is_active=True)\
            .values_list('merchant', flat=True).distinct()
        if value == UserStatusFilterChoices.ActivelyTrading:
            return queryset.filter(id__in=merchants)
        elif value == UserStatusFilterChoices.NotActivelyTrading:
            return queryset.filter(~Q(id__in=merchants))

    class Meta:
        model = CarMerchant
        fields = ("user",)
