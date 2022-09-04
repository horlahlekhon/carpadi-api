import datetime
from decimal import Decimal
from uuid import uuid4

import requests
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from rest_framework import serializers, exceptions

from src.config import common
from src.models.models import TransactionKinds, TransactionStatus, TransactionTypes

# from .models import Transaction
from ..models.models import (
    CarMerchant,
    Car,
    TransactionPin,
    User,
    TransactionPinStatus,
    Wallet,
    Transaction,
    Trade,
    TradeUnit,
    TradeStates,
    BankAccount,
    Banks,
)


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
    device_serial_number = serializers.CharField(max_length=50, required=False, default="")

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
        device = validated_data["device_serial_number"]
        pin = validated_data["pin"]
        active_pins = user.transaction_pins.filter(status=TransactionPinStatus.Active)
        if len(active_pins) >= 3:
            raise exceptions.NotAcceptable(
                "User is already logged in on 3 devices," " please delete one of the logged in sessions."
            )
        if len(active_pins.filter(device_serial_number=device)) > 0:
            # user have a pin on this device but tries to create with same device
            raise serializers.ValidationError(
                {"error": "You have a pin configured for this device already," " only one pin can be used on one device"}
            )
        if len(active_pins.filter(pin=pin)) > 0:
            raise serializers.ValidationError({"error": "Pin already belong to one of your devices, please use " "another one"})
        validated_data["pin"] = pin
        validated_data["status"] = TransactionPinStatus.Active
        return TransactionPin.objects.create(**validated_data)


class UpdateTransactionPinSerializers(serializers.Serializer):
    old_pin = serializers.CharField(max_length=6, required=True)
    new_pin = serializers.CharField(max_length=6, required=True)

    # def create(self, validated_data):
    #     pin: TransactionPin = self.context["pin"]
    #

    def create(self, validated_data):
        user: User = validated_data["user"]
        old_pin = validated_data["old_pin"]
        new_pin = validated_data["new_pin"]
        try:
            device = validated_data["device"]
            pin = user.transaction_pins.get(status=TransactionPinStatus.Active, pin=old_pin, device_serial_number=device)
            # if not check_password(old_pin, pin.pin):
            #     raise serializers.ValidationError("Pin is not correct")
            # pin.pin = make_password(new_pin)
            pin.pin = new_pin
            pin.save(update_fields=["pin"])
            pin.refresh_from_db()
            return pin
        except TransactionPin.DoesNotExist as reason:
            raise serializers.ValidationError({"error": "Pin is not correct"}) from reason


class CarMerchantUpdateSerializer(serializers.Serializer):
    bvn = serializers.CharField(max_length=14, required=False)

    def update(self, merch: CarMerchant, validated_data):
        merch.bvn = validated_data.get("bvn")
        merch.save(update_fields=["bvn"])
        return merch


class CarMerchantSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, merchant: CarMerchant):
        from ..models.serializers import UserSerializer

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
        return wallet.get_unsettled_cash()

    def get_total_cash(self, wallet: Wallet):
        return wallet.get_total_cash()

    def get_trading_cash(self, wallet: Wallet):
        return wallet.get_trading_cash()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        units_rots = (
            TradeUnit.objects.filter(
                merchant=instance.merchant, trade__trade_status__in=[TradeStates.Ongoing, TradeStates.Completed]
            )
            .aggregate(total=Sum("estimated_rot"))
            .get("total", Decimal(0))
        )
        data['estimated_total_rot'] = units_rots
        return data

    class Meta:
        model = Wallet
        fields = "__all__"
        read_only_fields = (
            'created',
            'modified',
            'user',
            'balance',
            "withdrawable_cash",
            "unsettled_cash",
            "total_cash",
            "trading_cash",
        )


# transaction  serializer
class TransactionSerializer(serializers.ModelSerializer):
    destination_account = serializers.PrimaryKeyRelatedField(queryset=BankAccount.objects.all(), required=False)

    class Meta:
        model = Transaction
        ref_name = "transactions_api_serializer"
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
            "transaction_payment_link",
            'destination_account',
        )
        read_only_fields = (
            'id',
            'created',
            'wallet',
            "transaction_payment_link",
            "transaction_status",
            "transaction_reference",
            "transaction_type",
            "transaction_payment_link",
        )

    def validate_transaction_kind(self, value):
        if value not in [TransactionKinds.Deposit, TransactionKinds.Withdrawal]:
            raise serializers.ValidationError("Transaction kind is not valid")
        return value

    def validate_amount(self, value):
        merchant = self.context["request"].user.merchant
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than 0")
        if self.initial_data.get("transaction_kind") == TransactionKinds.Withdrawal:
            if merchant.wallet.withdrawable_cash < value:
                raise serializers.ValidationError("Amount is greater than withdrawable cash available")
        return value

    def deposit(self, validated_data: dict, wallet: Wallet, reference: str):
        payload = dict(
            tx_ref=reference,
            amount=validated_data["amount"],
            redirect_url=common.FLW_REDIRECT_URL,
            customer=dict(phone=wallet.merchant.user.phone, email=wallet.merchant.user.email),
            currency="NGN",
        )
        headers = dict(Authorization=f"Bearer {common.FLW_SECRET_KEY}")
        try:
            tx = None
            response: requests.Response = requests.post(url=common.FLW_PAYMENT_URL, json=payload, headers=headers)
            data = response.json()
            if response.status_code == 200:
                if data["status"] == "success":
                    tx = Transaction.objects.create(
                        transaction_reference=reference,
                        transaction_kind=validated_data["transaction_kind"],
                        transaction_status=TransactionStatus.Pending,
                        transaction_description=validated_data.get("transaction_description") or "carpadi deposit",
                        # noqa
                        transaction_type=TransactionTypes.Credit,
                        amount=validated_data["amount"],
                        wallet=wallet,
                        transaction_payment_link=data["data"]["link"],
                    )
                else:
                    raise serializers.ValidationError(data["message"])
            else:
                raise serializers.ValidationError(data["message"])
            return tx
        except Exception as e:
            raise exceptions.APIException(f"Error while making transaction {e}")

    def withdraw(self, validated_data, wallet, ref):
        payload = {
            "account_bank": validated_data["destination_account"].bank.bank_code,
            "account_number": validated_data["destination_account"].account_number,
            "amount": validated_data["amount"],
            "narration": validated_data.get("transaction_description") or "withdrawal from carpadi",
            "currency": "NGN",
            "reference": ref,
            "callback_url": common.FLW_REDIRECT_URL,
            "debit_currency": "NGN",
        }
        headers = {"Authorization": f"Bearer {common.FLW_SECRET_KEY}", "Content-Type": "application/json"}
        try:
            tx = None
            response: requests.Response = requests.post(url=common.FLW_WITHDRAW_URL, json=payload, headers=headers)
            data = response.json()
            if response.status_code == 200:
                if data["status"] == "success":
                    tx = Transaction.objects.create(
                        transaction_reference=ref,
                        transaction_kind=TransactionKinds.Withdrawal,
                        transaction_status=TransactionStatus.Pending,
                        transaction_description=validated_data.get("transaction_description"),
                        # TODO write custom message
                        transaction_type=TransactionTypes.Debit,
                        amount=validated_data["amount"],
                        wallet=wallet,
                        transaction_payment_link=None,
                        transaction_fees=data["data"]["fee"],
                        transaction_response=data["data"],
                    )
                else:
                    raise serializers.ValidationError(data["message"])
            else:
                raise serializers.ValidationError(data["message"])
            return tx
        except Exception as e:
            raise exceptions.APIException(f"Error while making transaction {e}")

    def validate_destination_account(self, value: BankAccount):
        merchant = self.context["request"].user.merchant
        if value.merchant != merchant:
            raise serializers.ValidationError("Invalid account for this merchant")
        return value

    def validate(self, attrs):
        attrs = super(TransactionSerializer, self).validate(attrs)
        if attrs.get("transaction_kind") == TransactionKinds.Withdrawal and not attrs.get("destination_account"):
            raise serializers.ValidationError("Destination account is required for withdrawals")
        return attrs

    # TODO: a last part of the transaction shoud be a job that polls for the transaction
    #  status on flutter wave in case our webhook/callback is not working. we can have a job that get all
    #  pending transactions that are not more than 4hrs old and check their status. greater than 4hrs should just fail.
    def create(self, validated_data):
        # rave = Rave(common.FLW_PUBLIC_KEY, common.FLW_SECRET_KEY)
        ref = f"CP-{uuid4()}"
        wallet: Wallet = validated_data["merchant"].wallet
        if validated_data["transaction_kind"] == TransactionKinds.Deposit:
            return self.deposit(validated_data, wallet, ref)
        elif validated_data["transaction_kind"] == TransactionKinds.Withdrawal:
            return self.withdraw(validated_data, wallet, ref)
        else:
            raise serializers.ValidationError("Transaction kind is not valid")


class TradeSerializer(serializers.ModelSerializer):
    remaining_slots = serializers.SerializerMethodField()
    trade_status = serializers.SerializerMethodField()
    slots_purchased = serializers.SerializerMethodField()
    return_on_trade_percentage = serializers.SerializerMethodField()
    # return_on_trade = serializers.SerializerMethodField()
    return_on_trade_per_unit = serializers.SerializerMethodField()

    class Meta:
        model = Trade
        fields = "__all__"
        read_only_fields = (
            'created',
            'modified',
            'slots_purchased',
            "expected_return_on_trade",
            "return_on_trade",
            "remaining_slots",
            "price_per_slot",
            "trade_status",
            "car",
        )
        hidden_fields = ("return_on_trade", "expected_return_on_trade",
                         "estimated_return_on_trade", "min_sale_price")

    def serialize_car(self, car: Car):
        return {
            "id": car.id,
            "make": car.information.brand.name,
            "model": car.information.brand.name,
            "year": car.information.brand.name,
            "color": car.colour,
            "name": car.name,
            "car_pictures": car.pictures.values_list("asset", flat=True),
            # "image": c,
        }

    def get_fields(self):
        fields = super(TradeSerializer, self).get_fields()
        fields.pop("return_on_trade")
        fields.pop("estimated_return_on_trade")
        fields.pop("min_sale_price")
        return fields

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["car"] = self.serialize_car(instance.car)
        return data

    def get_slots_purchased(self, obj):
        return obj.slots_purchased()

    # def get_return_on_trade(self, obj: Trade):
    #     return obj.return_on_trade_calc()
    def get_return_on_trade_per_unit(self, obj: Trade):
        return obj.return_on_trade_per_slot

    def get_return_on_trade_percentage(self, obj: Trade):
        return obj.return_on_trade_calc_percent()

    def get_trade_status(self, obj: Trade):
        return obj.trade_status

    def calculate_price_per_slot(self, car_price, slots_availble):
        return car_price / slots_availble

    def get_remaining_slots(self, trade: Trade):
        return trade.remaining_slots()

    def get_bts_time(self, trade: Trade):
        if trade.date_of_sale:
            return (trade.created.date() - trade.date_of_sale).days
        return (trade.created.date() - timezone.now()).days

    def create(self, validated_data):
        raise exceptions.APIException("Cannot create a trade")

    def update(self, instance, validated_data):
        raise exceptions.APIException("Cannot update a trade")


class TradeUnitSerializer(serializers.ModelSerializer):
    merchant = serializers.PrimaryKeyRelatedField(queryset=CarMerchant.objects.all(), required=False)
    buy_transaction = serializers.HiddenField(default=None)
    vat_percentage = serializers.HiddenField(default=0)
    checkout_transaction = serializers.HiddenField(default=None)

    class Meta:
        model = TradeUnit
        fields = "__all__"
        read_only_fields = (
            'created',
            'modified',
            "id",
            "unit_value",
            "share_percentage",
            "estimated_rot",
        )

    def serialize_car(self, car: Car):
        return {
            "id": car.id,
            "name": car.name,
            "car_pictures": car.pictures.values_list("asset", flat=True),
            # "image": c,
        }

    def to_representation(self, instance: TradeUnit):
        data = super().to_representation(instance)
        data["car"] = self.serialize_car(instance.trade.car)
        data['trade_duration'] = instance.trade.estimated_sales_duration
        data['trade_start_date'] = instance.trade.created
        data['estimated_vehicle_sale_date'] = instance.trade.created + datetime.timedelta(
            days=instance.trade.estimated_sales_duration
        )
        data['description'] = instance.trade.car.description
        data['trade_status'] = instance.trade.trade_status
        data['estimated_profit_percentage'] = instance.estimated_rot / instance.unit_value * 100
        return data

    def validate(self, attrs):
        attrs = super().validate(attrs)
        merchant = self.context["merchant"]
        wallet: Wallet = merchant.wallet
        trade: Trade = attrs.get("trade")
        if trade.trade_status != TradeStates.Ongoing:
            raise serializers.ValidationError("Trade is not currently open")
        remaining_slots = trade.remaining_slots()
        if remaining_slots < attrs["slots_quantity"]:
            raise serializers.ValidationError({"trade": "Trade does not have enough slots available"})
        rot = trade.return_on_trade_per_slot * attrs["slots_quantity"]
        unit_value = trade.price_per_slot * attrs["slots_quantity"]
        if unit_value > wallet.get_withdrawable_cash():
            raise serializers.ValidationError("Wallet balance is insufficient for this transaction")
        attrs["trade"] = trade
        attrs["merchant"] = merchant
        attrs["estimated_rot"] = rot
        return attrs

    @transaction.atomic()
    def create(self, validated_data):
        trade: Trade = validated_data["trade"]
        merchant: CarMerchant = validated_data["merchant"]
        share_percentage = (trade.slots_available / validated_data["slots_quantity"]) * 100
        unit_value = trade.calculate_price_per_slot() * validated_data["slots_quantity"]
        ref = f"CP-{str(uuid4()).upper()}"
        tx = Transaction.objects.create(
            transaction_reference=ref,
            transaction_kind=TransactionKinds.TradeUnitPurchases,
            transaction_status=TransactionStatus.Success,
            transaction_description="Trade Unit Purchase",
            # noqa
            transaction_type=TransactionTypes.Debit,
            amount=unit_value,
            wallet=merchant.wallet,
            transaction_payment_link=None,
        )
        unit = TradeUnit.objects.create(
            trade=trade,
            merchant=merchant,
            share_percentage=share_percentage,
            slots_quantity=validated_data["slots_quantity"],
            estimated_rot=validated_data["estimated_rot"],
            unit_value=trade.price_per_slot * validated_data["slots_quantity"],
            buy_transaction=tx,
        )
        tx.wallet.update_balance(tx=tx)
        return unit


class BankAccountSerializer(serializers.ModelSerializer):
    merchant = serializers.PrimaryKeyRelatedField(queryset=CarMerchant.objects.all(), required=False)

    class Meta:
        model = BankAccount
        fields = "__all__"

    def validate_account_number(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Account number should be at least 10 digits")
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["bank"] = dict(id=instance.bank.id, name=instance.bank.bank_name)
        return data

    def check_account_details(self, account_number, bank_code):
        headers = dict(Authorization=f"Bearer {common.FLW_SECRET_KEY}")
        bdy = {
            "account_number": account_number,
            "account_bank": bank_code,
        }
        resp = requests.post(common.FLW_ACCOUNT_VERIFY_URL, json=bdy, headers=headers)
        data = resp.json()
        if resp.status_code != 200:
            raise serializers.ValidationError("Invalid account details")
        else:
            return data['data']["account_name"], data['data']["account_number"]

    def validate(self, attrs):
        # if BankAccount.objects.filter(account_number=attrs.get("account_number")).exists():
        #     raise serializers.ValidationError("Account number already exists")
        bank: Banks = attrs.get('bank')
        account_name, _ = self.check_account_details(attrs.get("account_number"), bank.bank_code)
        attrs["name"] = account_name
        attrs["bank"] = bank
        attrs["merchant"] = self.context['request'].user.merchant
        return attrs


class BankSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banks
        fields = "__all__"
