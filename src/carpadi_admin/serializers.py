from dataclasses import fields
from pyexpat import model
from django.db.models import Sum, Avg
import datetime

from rest_framework import serializers

from src.models.models import Car, Wallet, Transaction, Trade, TradeUnit, Disbursement, Activity


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
    average_bts = serializers.FloatField()
    number_of_users_trading = serializers.IntegerField()
    total_trading_cash = serializers.DecimalField(max_digits=15, decimal_places=5)
    total_available_shares = serializers.IntegerField()
    available_shares_value = serializers.DecimalField(max_digits=15, decimal_places=5)
    cars_with_available_share = serializers.IntegerField()
    recent_trade_activities = serializers.ListField()
    cars_summary = serializers.JSONField()
    rot_vs_ttc = serializers.JSONField()

    class Meta:
        read_only_fields = "__all__"

    @staticmethod
    def filter_data(
        model_name,
        model_field: str = None,
        value: str = None,
        created: bool = False,
        month: datetime.date.month = None,
        year: datetime.date.year = None,
    ):
        date = datetime.date.today()

        if created and not month and not year:
            return model_name.objects.filter(model_field=value, created__month=date.month, created__year=date.year)

        elif not created and not month and not year:
            return model_name.objects.filter(model__field=value, modified__month=date.month, modified__year=date.year)

        elif created and month and year:
            return model_name.objects.filter(model__field=value, created__month=month, created__year=year)

        elif not created and month and year:
            return model_name.objects.filter(model_field=value, modified__month=month, created__year=year)

        elif not created and not month:
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
        self.average_bts = self.filter_data(trade, 'trade_status', 'completed', month=month, year=year)\
                               .aggregate(data=Avg('bts_time')), 200
        return self.average_bts

    def get_total_available_shares(self, trade: Trade, month, year):
        self.total_available_shares = self.filter_data(trade, 'trade_status', 'ongoing', True, month, year)\
                                          .aggregate(data=Avg('remaining_slots')), 200
        return self.total_available_shares

    def get_number_of_users_trading(self, trade_unit: TradeUnit, month, year):
        self.number_of_users_trading = self.filter_data(trade_unit, year, month, created=True)\
                                           .aggregate(data=Sum('merchant')), 200
        return self.number_of_users_trading

    def get_total_trading_cash(self, trade_unit: TradeUnit, month, year):
        self.total_trading_cash = self.filter_data(trade_unit, month, year, created=True)\
                                      .aggregate(data=Sum('unit_value')), 200
        return self.total_trading_cash

    def get_available_shares_value(self, trade: Trade, month, year):
        trade_data = self.filter_data(trade, 'trade_status', 'ongoing', month, year)

        if month:
            total_value = serializers.DecimalField(max_digits=15, decimal_places=5)
            for trade_data.modified.day in range(1, 32):
                value = trade_data.remaining_slots * trade_data.price_per_slot
                total_value = total_value + value
            self.available_shares_value = total_value
        return self.available_shares_value

    def get_cars_with_available_share(self, trade: Trade, month, year):
        self.cars_with_available_share = self.filter_data(trade, 'trade__status', 'ongoing', month=month, year=year)\
            .aggregate(data=Sum('car'))
        return self.cars_with_available_share

    def get_rot_vs_ttc(self, trade: Trade, month, year):
        trade_data = self.filter_data(trade, month=month, year=year)

        if month:
            ttc = [0.00] * 4
            rot = [0.00] * 4
            weekly = {"ttc": ttc, "rot": rot}
            for i in range(31):
                for trade_data.modified.day in range(1, 8):
                    weekly["ttc"][0] = weekly["ttc"][0] + (trade_data.slots_purchased * trade_data.price_per_slot)
                    weekly["rot"][0] = weekly["rot"][0] + trade_data.return_on_trade

                for trade_data.modified.day in (8, 16):
                    weekly["ttc"][1] = weekly["ttc"][1] + (trade_data.slots_purchased * trade_data.price_per_slot)
                    weekly["rot"][1] = weekly["rot"][1] + trade_data.return_on_trade

                for trade_data.modified.day in (16, 24):
                    weekly["ttc"][2] = weekly["ttc"][2] + (trade_data.slots_purchased * trade_data.price_per_slot)
                    weekly["rot"][2] = weekly["rot"][2] + trade_data.return_on_trade

                for trade_data.modified.day in (24, 32):
                    weekly["ttc"][3] = weekly["ttc"][3] + (trade_data.slots_purchased * trade_data.price_per_slot)
                    weekly["rot"][3] = weekly["rot"][3] + trade_data.return_on_trade

            self.rot_vs_ttc = weekly
            return self.rot_vs_ttc

        if not month:
            ttc = [0.00] * 12
            rot = [0.00] * 12
            monthly = {"ttc": ttc, "rot": rot}

            for trade_data.modified.month in range(1, 13):
                m = 0
                monthly["ttc"][m] = monthly["ttc"][m] + (trade_data.slots_purchased * trade_data.price_per_slot)
                monthly["rot"][m] = monthly["rot"][m] + trade_data.return_on_trade
                m += 1
            self.rot_vs_ttc = monthly
            return self.rot_vs_ttc

    def get_recent_trade_activities(self, trade_unit: TradeUnit, month, year):
        recent_trade = self.filter_data(trade_unit, created=True, month=month, year=year).order_by('created')[10]
        self.recent_trade_activities = recent_trade
        return self.recent_trade_activities

    def get_cars_summary(self, car: Car, month, year):
        summary = self.filter_data(car, month=month, year=year)
        inspected = summary.annotate(status='inspected')
        sold = summary.annotate(status='sold')
        available = summary.annotate(status='available')
        total = summary.Sum()
        percent_inspected = (inspected / total) * 100
        percent_sold = (sold / total) * 100
        percent_available = (available / total) * 100
        self.cars_summary = {
            "total": total,
            "inspected": {
                "percentage": percent_inspected,
                "number": inspected
            },
            "sold": {
                "percentage": percent_sold,
                "number": sold
            },
            "available": {
                "percentage": percent_available,
                "number": available
            }
        }
        return self.cars_summary
