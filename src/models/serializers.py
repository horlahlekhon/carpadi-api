import datetime
import re

from rest_framework import serializers, exceptions

from src.config.common import OTP_EXPIRY
from src.models.models import (
    Transactions,
    Wallets,
    CarMerchant,
    BankAccount,
    CarBrand,
    Car,
    UserTypes,
    TransactionPinStatus,
    TransactionPin, Otp,
)
from src.common.serializers import ThumbnailerJSONSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, PasswordField
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model, authenticate
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from src.notifications.services import USER_PHONE_VERIFICATION, notify

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    profile_picture = ThumbnailerJSONSerializer(required=False, allow_null=True, alias_target='src.models')

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'profile_picture',
        )
        # read_only_fields = ('username',)


class CreateUserSerializer(serializers.ModelSerializer):
    profile_picture = ThumbnailerJSONSerializer(required=False, allow_null=True, alias_target='src.models')
    # tokens = serializers.SerializerMethodField()
    phone = serializers.CharField(max_length=15, required=True)
    email = serializers.EmailField(required=True)
    birth_date = serializers.DateField(required=False)
    username = serializers.CharField(required=False)
    user_type = serializers.ChoiceField(required=False, choices=UserTypes.choices)
    merchant_id = serializers.SerializerMethodField()

    def get_merchant_id(self, user: User):
        return user.merchant.id

    def get_tokens(self, user):
        return user.get_tokens()

    @transaction.atomic()
    def create(self, validated_data):
        # call create_user on user object. Without this
        # the password will be stored in plain text.
        try:
            validated_data['username'] = (
                str(validated_data.get("username")).lower() if validated_data.get("username") else validated_data.get(
                    "email")
            )
            validated_data["is_active"] = False
            if validated_data.get("user_type") == UserTypes.CarMerchant:
                user = User.objects.create_user(**validated_data)
                user.eligible_for_reset()
                CarMerchant.objects.create(user=user)
            elif validated_data.get("user_type") == UserTypes.Admin:
                user = User.objects.create_superuser(**validated_data)
            else:
                raise exceptions.ValidationError("Invalid user type")
        except IntegrityError as reason:
            raise exceptions.ValidationError("phone or email already exists", 400)
        return user

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
            # 'tokens',
            'profile_picture',
            "phone",
            'birth_date',
            'user_type',
            'merchant_id',
        )
        read_only_fields = ('merchant_id',)
        extra_kwargs = {'password': {'write_only': True}}


def is_valid_phone(phone):
    is_valid = re.search(r'\+?[\d]{3}[\d]{10}', phone)
    if not is_valid:
        raise serializers.ValidationError("Invalid phone number, phone number should match format: +234 000 000 0000")
    return phone


class PhoneVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=6, required=True)
    phone = serializers.CharField(validators=(is_valid_phone,), max_length=15)

    def get_tokens(self, user):
        return user.get_tokens()

    def validate(self, attrs):
        user = User.objects.get(phone=attrs["phone"])
        if user:
            otp = user.otps.latest()
            if otp.expiry > now() and otp.otp == attrs["token"]:
                return attrs
            elif otp.expiry < now() and otp.otp == attrs["token"]:
                raise serializers.ValidationError("Otp has expired", 400)
            else:
                raise serializers.ValidationError("Invalid OTP", 400)
        else:
            raise serializers.ValidationError(f"User with the phone {attrs['phone']} does not exist")

    def create(self, validated_data):
        user: User = User.objects.get(phone=validated_data["phone"])
        user.is_active = True
        user.save(update_fields=["is_active"])
        user.refresh_from_db()
        return user

    class Meta:
        fields = ('token',)


# transaction  serializer
class TransactionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactions
        fields = (
            'id',
            'created',
            'wallet',
            'amount',
        )
        read_only_fields = (
            'id',
            'created',
            'wallet',
            'amount',
        )


# wallet serialer
class Wallet_serializer(serializers.ModelSerializer):
    class Meta:
        model = Wallets
        fields = "__all__"
        read_only_fields = 'created'


class CarMerchantSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, merchant: CarMerchant):
        user_ser = UserSerializer(instance=merchant.user)
        return user_ser.data

    class Meta:
        model = CarMerchant
        fields = "__all__"


class BankAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankAccount
        fields = "__all__"


class CarBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarBrand
        fields = "__all__"


from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken


class TokenObtainModSerializer(serializers.Serializer):
    username_field = get_user_model().USERNAME_FIELD

    default_error_messages = {
        'no_active_account': _('No active account found with the given credentials'),
        'new_device_detected': _(
            'You are logging in to this device for the first time,' ' kindly create a new transaction pin for this device'
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()
        self.fields['password'] = PasswordField()
        self.fields['device_imei'] = serializers.CharField()
        self.fields['skip_pin'] = serializers.BooleanField(required=False)

    def validate(self, attrs):
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            'password': attrs['password'],
        }
        try:
            authenticate_kwargs['request'] = self.context['request']
        except KeyError:
            pass

        self.user: User = authenticate(**authenticate_kwargs)

        if not api_settings.USER_AUTHENTICATION_RULE(self.user):
            raise exceptions.AuthenticationFailed(
                self.error_messages['no_active_account'],
                'no_active_account',
            )

        device_logins = self.user.transaction_pins.filter(
            device_serial_number=attrs.get('device_imei'), status__in=(TransactionPinStatus.Active,)
        ).count()
        skip_pin = attrs.get("skip_pin", False)
        if device_logins < 1 and not skip_pin:
            raise exceptions.AuthenticationFailed(
                self.error_messages['new_device_detected'],
                'new_device_detected',
            )
        User.update_last_login(self.user, **dict(device_imei=attrs.get("device_imei")))

        refresh = self.get_token(self.user)
        car_merch = CarMerchantSerializer(instance=self.user.merchant)
        data = {'refresh': str(refresh), 'access': str(refresh.access_token), "merchant": car_merch.data}
        return data

    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)


class OtpSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)

    def validate(self, attrs):
        username = attrs["username"]
        if username and re.search(r'[^@\s]+@[^@\s]+\.[^@\s]+', username):
            kwargs = {'email': username}
        elif username and re.search(r'\+?[\d]{3}[\d]{10}', username):
            kwargs = {'phone': username}
        else:
            kwargs = {'username': username}
        return kwargs

    def create(self, validated_data):
        users = User.objects.filter(**validated_data)
        if len(users) > 0:
            user = users[0]
            expiry = datetime.datetime.now() + datetime.timedelta(minutes=OTP_EXPIRY)
            otp = "123456"
            context = dict(username=user.username, otp=otp)
            # notify(
            #     USER_PHONE_VERIFICATION,
            #     context=context,
            #     email_to=[
            #         user.email,
            #     ],
            # )
            return Otp.objects.create(user=user, expiry=expiry, otp=otp)
        else:
            key = list(validated_data.keys())[0]
            raise serializers.ValidationError(f"user with {key} {validated_data[key]} does not exist")


from rest_framework.renderers import JSONRenderer


