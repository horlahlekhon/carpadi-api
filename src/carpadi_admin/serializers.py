from dataclasses import fields
from pyexpat import model
from django.db.models import Sum, Avg
import datetime

from rest_framework import serializers

from src.models.models import CarMerchant, Car, Wallet, Transaction, Trade as trade, TradeUnit as trade_unit, Disbursement, Activity


class SocialSerializer(serializers.Serializer):
    """
    Serializer which accepts an OAuth2 access token.
    """

    access_token = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )


# class CarMerchantSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CarMerchant
#         fields = "__all__"


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = "__all__"
        ref_name = "car_serializer_admin"


class WalletSerializerAdmin(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = "__all__"


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
        read_only_fields = (
            "amount",
            "transaction_type",
            "wallet",
            "transaction_reference",
            "transaction_description",
            "transaction_status",
            "transaction_response",
            "transaction_kind",
            "transaction_payment_link",
        )


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = "__all__"
        read_only_fields = (
            'created',
            'modified',
            'slots_purchased',
            "traded_slots",
            "remaining_slots",
            "total_slots",
            "price_per_slot",
            "trade_status",
            "car",
        )


class DisbursementSerializerAdmin(serializers.ModelSerializer):
    class Meta:
        model = Disbursement
        fields = ("created", "id", "amount", "trade_unit")
        read_only_fields = ("created", "id", "amount", "trade_unit")


class ActivitySerializerAdmin(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ("created", "id", "activity_type", "object_id", "content_type", "description")
        read_only_fields = ("created", "id", "activity_type", "object_id", "content_type", "description")


class DashboardSerializerAdmin(serializers.Serializer):
    average_bts = serializers.IntegerField()
    number_of_users_trading = serializers.IntegerField()
    average_trading_cash = serializers.DecimalField(max_digits=15, decimal_places=5)
    total_available_shares = serializers.IntegerField()
    total_available_shares_value = serializers.DecimalField(max_digits=15, decimal_places=5)
    cars_with_available_share = serializers.IntegerField()
    recent_trade_activities = serializers.JSONField()
    cars_summary = serializers.JSONField()
    total_trading_cash_month = serializers.JSONField()
    return_on_trades_month = serializers.JSONField()
    total_trading_cash_year = serializers.JSONField()
    return_on_trades_year = serializers.JSONField()

    @classmethod
    def get_average_bts(cls, trade, month=None, year=None):
        if month and year:
            average_bts = trade.objects.filter(trade_status='completed',
                                               modified__year=year, modified__month=month) \
                .aggregate(data=Avg('bts_time'))

            return average_bts, 200

        if year and not month:
            average_bts = trade.objects.filter(trade_status='completed', modified__year=year) \
                .aggregate(data=Avg('bts_time'))

            return average_bts, 200

        date = datetime.date.today()
        average_bts = trade.objects.filter(trade_status='completed', modified__year=date.year,
                                           modified__month=date.month).aggregate(data=Avg('bts_time'))

        return average_bts, 200

    @classmethod
    get_total_available_shares(cls, trade, month=None, year=None):
    if month and year:
        average_bts = trade.objects.filter(trade_status='ongoing',
                                           modified__year=year, modified__month=month) \
            .aggregate(data=Avg('remaining_slots'))

        return total_available_shares, 200

    if year and not month:
        average_bts = trade.objects.filter(trade_status='ongoing', modified__year=year) \
            .aggregate(data=Avg('remaining_slots'))

        return total_available_shares, 200

    date = datetime.date.today()
    average_bts = trade.objects.filter(trade_status='ongoing', modified__year=date.year,
                                       modified__month=date.month).aggregate(data=Avg('remaining_slots'))

    return total_available_shares, 200

    @classmethod
    def get_number_of_users_trading(cls, trade_unit,  month=None, year=None):
        if year and month:
            number_of_users_trading = trade_unit.objects.filter(created__year=year, created__month=month)\
                .aggregate(data=Sum('merchant'))
            return number_of_users_trading, 200

        if year and not month:
            number_of_users_trading = trade_unit.objects.filter(created__year=year)\
                .aggregate(data=Sum('merchant'))
            return number_of_users_trading, 200

        date = datetime.date.today()
        number_of_users_trading = trade_unit.objects.filter(created__year=date.year, created__month=date.month)\
            .aggregate(data=Sum('merchant'))
        return number_of_users_trading, 200

    @classmethod
    get_average_trading_cash(cls, trade_unit, month=None, year=None):
        if year and month:
            average_trading_cash = unit_price.objects.filter(created__year=year, created__month=month) \
                .aggregate(data=Avg('unit_value'))
            return average_trading_cash, 200

        if year and not month:
            average_trading_cash = unit_price.objects.filter(created__year=year) \
                .aggregate(data=Avg('unit_value'))
            return average_trading_cash, 200

        date = datetime.date.today()
        average_trading_cash = unit_price.objects.filter(created__year=date.year, created__month=date.month) \
            .aggregate(data=Avg('unit_value'))
        return average_trading_cash, 200
