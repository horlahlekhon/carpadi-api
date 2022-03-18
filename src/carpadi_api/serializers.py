from email.policy import default
from celery import uuid
from rest_framework import serializers, exceptions

# from .models import Transaction
from ..models.models import CarMerchant, Car, TransactionPin, User, TransactionPinStatus

from django.contrib.auth.hashers import make_password, check_password


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
        if not str.isdigit(pin) or len(pin) != 4:
            raise serializers.ValidationError("Pin should be exactly 4 digits long")
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
