from dataclasses import field
from django_filters import rest_framework as filters

from src.models.models import Transaction, Wallet, Disbursement, Activity


class TransactionsFilterAdmin(filters.FilterSet):
    min_amount = filters.NumberFilter(field_name="amount", lookup_expr='gte')
    max_amount = filters.NumberFilter(field_name="amount", lookup_expr='lte')

    transaction_date_lte = filters.DateTimeFilter(field_name="created", lookup_expr='day__lte')
    transaction_date_gte = filters.DateTimeFilter(field_name="created", lookup_expr='day__gte')
    transaction_date_range = filters.DateTimeFromToRangeFilter(field_name="created")

    class Meta:
        model = Transaction
        fields = ['wallet', 'amount', 'created']


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


# class CarMerchantFilerAdmin(filters.FilterSet):
#     ...
