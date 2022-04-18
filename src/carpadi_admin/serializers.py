from dataclasses import fields
from pyexpat import model
from django.db.models import Sum, Avg
import datetime

from rest_framework import serializers

from src.models.models import CarMerchant, Car, Wallet, Transaction, Trade, TradeUnit, Disbursement, Activity


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
    total_trading_cash = serializers.DecimalField(max_digits=15, decimal_places=5)
    total_available_shares = serializers.IntegerField()
    available_shares_value = serializers.DecimalField(max_digits=15, decimal_places=5)
    cars_with_available_share = serializers.IntegerField()
    recent_trade_activities = serializers.JSONField()
    cars_summary = serializers.JSONField()
    rot_vs_ttc = serializers.JSONField()

    @staticmethod
    def filter_data(model_name, model_field: str = None, value: str = None, created: bool = False, month: datetime.date.month = None,
                    year: datetime.date.year = None):
        date = datetime.date.today()

        if created and not month and not year:
            return model_name.objects.filter(model_field=value, created__month=date.month, created__year=date.year)

        elif not created and not month and not year:
            return model_name.objects.filter(model__field=value, modified__month=date.month, modified__year=date.year)

        elif created and month and year:
            return model_name.objects.filter(model__field=value, created__month=month, created__year=year)

        elif not created and month and year:
            return model_name.objects.filter(model_field=value, modified__month=month, created__year=year)

        elif not created  and not month:
            return model_name.objects.filter(model__field=value, modified__year=year)

        elif created and not month:
            return model_name.objects.filter(model__field=value, created__year=year)

        elif not model_field and not created and not month and not year:
            return model_name.objects.filter(modified__month=date.month, created__year=date.year)

        elif not model_field and created and not month and not year:
            return model_name.objects.filter(created__month=date.month, created__year=date.year)

        elif not model_field and created and month and year:
            return model_name.objects.filter(created__month=month, created__year=year)

        # data = model.objects.filter(model_field=f"{value}", month=month, year=year)

    def get_average_bts(self, trade: Trade, month, year):
        return self.filter_data(trade, 'trade_status', 'completed', month, year)\
                   .aggregate(data=Avg('bts_time')), 200

    def get_total_available_shares(self, trade: Trade, month, year):
        return self.filter_data(trade, 'trade_status', 'ongoing', True, month, year)\
            .aggregate(data=Avg('remaining_slots')), 200

    def get_number_of_users_trading(self, trade_unit: TradeUnit,  month, year):
        return self.filter_data(trade_unit, year, month, created=True).aggregate(data=Sum('merchant')), 200

    def get_total_trading_cash(self, trade_unit: TradeUnit, month, year):
        return self.filter_data(trade_unit, month, year, created=True).aggregate(data=Sum('unit_value')), 200

    # def get_available_shares_value(self, trade: Trade, month, year):
    #     collect_data = self.filter_data(trade, 'trade_status', 'ongoing', month, year)\
    #         .annotate(data=Sum('remaining_slots'))

    def get_cars_with_available_shares(self, trade: Trade, month, year):
        return self.filter_data(trade, 'trade__status', 'ongoing', month, year).aggregate(data=Sum('car')), 200

    # def get_rot_vs_ttc(self):
    #     return self.filter_data()