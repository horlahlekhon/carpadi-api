from email.policy import default
from uuid import uuid4

from celery import uuid
from rest_framework import serializers, exceptions

# from .models import Transaction
from ..models.models import CarMerchant, Car, TransactionPin, User, TransactionPinStatus, Wallet, Transaction, \
    TransactionKinds, TransactionStatus, TransactionTypes, Trade, TradeUnit
from rave_python import Rave
from django.contrib.auth.hashers import make_password, check_password
import requests
from ..models.serializers import UserSerializer
from src.config import common


class SocialSerializer(serializers.Serializer):
    """
    Serializer which accepts an OAuth2 access token.
    """

    access_token = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )


class CarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Car
        fields = "__all__"
        ref_name = "car_serializer"


class TransactionPinSerializers(serializers.ModelSerializer):
    class Meta:
        model = TransactionPin
        fields = "__all__"
        read_only_fields = ("id", "created", "modified", "status", "user")
        extra_kwargs = {'pin': {'write_only': True}}

    def validate_pin(self, pin):
        if not str.isdigit(pin) or len(pin) != 6:
            raise serializers.ValidationError("Pin should be exactly 6 digits long")
        return pin

    def create(self, validated_data):
        user: User = validated_data["user"]
        active_pins = user.transaction_pins.filter(status=TransactionPinStatus.Active).count()
        if active_pins >= 3:
            raise exceptions.NotAcceptable(
                "User is already logged in on 3 devices," " please delete one of the logged in sessions."
            )
        validated_data["pin"] = make_password(validated_data["pin"])
        validated_data["status"] = TransactionPinStatus.Active
        return TransactionPin.objects.create(**validated_data)


class UpdateTransactionPinSerializers(serializers.Serializer):
    old_pin = serializers.CharField(max_length=4, required=True)
    new_pin = serializers.CharField(max_length=4, required=True)

    # def create(self, validated_data):
    #     pin: TransactionPin = self.context["pin"]
    #

    def update(self, pin: TransactionPin, validated_data):
        old_pin = validated_data["old_pin"]
        new_pin = validated_data["new_pin"]
        if not check_password(old_pin, pin.pin):
            raise serializers.ValidationError("Pin is not correct")
        pin.pin = make_password(new_pin)
        pin.save(update_fields=["pin"])
        pin.refresh_from_db()
        return pin


class CarMerchantUpdateSerializer(serializers.Serializer):
    bvn = serializers.CharField(max_length=14, required=False)

    def update(self, merch: CarMerchant, validated_data):
        merch.bvn = validated_data.get("bvn")
        merch.save(update_fields=["bvn"])
        return merch


class CarMerchantSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, merchant: CarMerchant):
        user_ser = UserSerializer(instance=merchant.user)
        return user_ser.data

    class Meta:
        model = CarMerchant
        fields = "__all__"


# wallet serialer
class WalletSerializer(serializers.ModelSerializer):
    withdrawable_cash = serializers.SerializerMethodField()
    unsettled_cash = serializers.SerializerMethodField()
    total_cash = serializers.SerializerMethodField()
    trading_cash = serializers.SerializerMethodField()

    def get_withdrawable_cash(self, wallet: Wallet):
        return wallet.withdrawable_cash

    def get_unsettled_cash(self, wallet: Wallet):
        return wallet.unsettled_cash

    def get_total_cash(self, wallet: Wallet):
        return wallet.total_cash

    def get_total_cash(self, wallet: Wallet):
        return wallet.total_cash

    def get_trading_cash(self, wallet: Wallet):
        return wallet.trading_cash

    class Meta:
        model = Wallet
        fields = "__all__"
        read_only_fields = ('created', 'modified', 'user', 'balance', "withdrawable_cash",
                            "unsettled_cash", "total_cash", "trading_cash")


# transaction  serializer
class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = (
            'id',
            'created',
            'wallet',
            'amount',
            "transaction_type",
            "transaction_status",
            "transaction_reference",
            "transaction_description",
            "transaction_kind",
            "transaction_payment_link"
        )
        read_only_fields = (
            'id',
            'created',
            'wallet',
            "transaction_payment_link",
            "transaction_status",
            "transaction_reference",
            "transaction_type",
            "transaction_payment_link")

    from uuid import uuid4
    from src.models.models import TransactionKinds, TransactionStatus, TransactionTypes
    def create(self, validated_data):
        # rave = Rave(common.FLW_PUBLIC_KEY, common.FLW_SECRET_KEY)
        ref = f"CP-{uuid4()}"
        wallet: Wallet = validated_data["merchant"].wallet
        payload = dict(tx_ref=ref, amount=validated_data["amount"], redirect_url=common.FLW_REDIRECT_URL,
                       customer=dict(phone=wallet.merchant.user.phone,
                                     email=wallet.merchant.user.email),
                       currency="NGN",
                       )
        headers = dict(Authorization=f"Bearer {common.FLW_SECRET_KEY}")
        try:
            transaction = None
            response: requests.Response = requests.post(url=common.FLW_PAYMENT_URL, json=payload, headers=headers)
            data = response.json()
            if response.status_code == 200:
                if data["status"] == "success":
                    transaction = Transaction.objects.create(
                        transaction_reference=ref,
                        transaction_kind=validated_data["transaction_kind"],
                        transaction_status=TransactionStatus.Pending,
                        transaction_description=validated_data["transaction_description"],
                        # noqa
                        transaction_type=TransactionTypes.Credit if validated_data["transaction_kind"] == TransactionKinds.Deposit else TransactionTypes.Debit,
                        amount=validated_data["amount"],
                        wallet=wallet,
                        transaction_payment_link=data["data"]["link"]
                    )
                else:
                    raise serializers.ValidationError(data["message"])
            else:
                raise serializers.ValidationError(data["message"])
            return transaction
        except Exception as e:
            raise exceptions.APIException(f"Error while making transaction {e}")


class TradeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trade
        fields = "__all__"
        read_only_fields = "__all__"
        # ('created', 'modified', 'slots_available', 'slots_purchased',
        #                 "expected_return_on_trade", "return_on_trade", "traded_slots",
        #                 "remaining_slots", "total_slots", "price_per_slot", "trade_status", "car")


class TradeUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = TradeUnit
        fields = "__all__"
        read_only_fields = ('created', 'modified', "id")
