from dataclasses import fields
from pyexpat import model
from rest_framework import serializers

from src.models.models import CarMerchant, Car, Wallet, Transaction, Trade, Disbursement, Activity, SpareParts


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


class SparePartsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpareParts
        fields = "__all__"
