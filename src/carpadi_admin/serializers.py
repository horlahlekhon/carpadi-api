from rest_framework import serializers

from src.models.models import CarMerchant, Car, Wallet, Transaction, Trade


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
        read_only_fields = ("amount", "transaction_type",
                            "wallet", "transaction_reference",
                            "transaction_description", "transaction_status",
                            "transaction_response", "transaction_kind", "transaction_payment_link")


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = "__all__"
        read_only_fields = \
            ('created', 'modified', 'slots_purchased',
             "traded_slots",
             "remaining_slots", "total_slots", "price_per_slot", "trade_status", "car")

        