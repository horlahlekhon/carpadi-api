import contextlib
import datetime
import re
from decimal import Decimal

from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from django.db.utils import IntegrityError
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from fcm_django.models import FCMDevice
from rest_framework import serializers, exceptions
from rest_framework_simplejwt.serializers import PasswordField
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken

from src.carpadi_api.serializers import TransactionSerializer, TradeUnitSerializer, WalletSerializer, CarSerializer
from src.config.common import OTP_EXPIRY
from src.models.models import (
    Wallet,
    CarMerchant,
    CarBrand,
    UserTypes,
    TransactionPinStatus,
    Otp,
    Disbursement,
    Activity,
    Assets,
    AssetEntityType,
    Car,
    Transaction,
    TradeUnit,
    Notifications,
    logger,
)

User = get_user_model()


def is_valid_phone(phone):
    if re.search(r'\+?[\d]{3}[\d]{10}', phone):
        return phone
    else:
        raise serializers.ValidationError("Invalid phone number, phone number should match format: +234 000 000 0000")


class UserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.URLField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'profile_picture', 'email', 'phone', 'is_active')
        # read_only_fields = ('username',)

    def to_representation(self, instance):
        data = super(UserSerializer, self).to_representation(instance)
        data["profile_picture"] = instance.profile_picture.asset if instance.profile_picture else None
        return data

    def update(self, instance, validated_data):
        if picture := validated_data.get("profile_picture"):
            picture = Assets.objects.create(asset=picture, content_object=instance, entity_type=AssetEntityType.Merchant)
            validated_data["profile_picture"] = picture
        return super(UserSerializer, self).update(instance, validated_data)


class CreateUserSerializer(serializers.ModelSerializer):
    profile_picture = serializers.URLField(required=False)
    # tokens = serializers.SerializerMethodField()
    phone = serializers.CharField(max_length=15, required=True)
    email = serializers.EmailField(required=True, max_length=255)
    birth_date = serializers.DateField(required=False)
    username = serializers.CharField(required=False)
    user_type = serializers.ChoiceField(required=True, choices=UserTypes.choices)
    merchant_id = serializers.SerializerMethodField()

    def get_merchant_id(self, user: User):
        return user.merchant.id if user.is_merchant() else None

    def get_tokens(self, user):
        return user.get_tokens()

    @transaction.atomic()
    def create(self, validated_data):
        # call create_user on user object. Without this
        # the password will be stored in plain text.
        try:
            validated_data['username'] = (
                str(validated_data.get("username")).lower() if validated_data.get("username") else validated_data.get("email")
            )
            validated_data["is_active"] = False
            if validated_data.get("user_type") == UserTypes.CarMerchant:
                validated_data["is_active"] = True
                user: User = User.objects.create_user(**validated_data)
                user.eligible_for_reset()
                CarMerchant.objects.create(user=user)
            elif validated_data.get("user_type") == UserTypes.Admin:
                user = User.objects.create_superuser(**validated_data)
            else:
                raise exceptions.ValidationError("Invalid user type")
        except IntegrityError as reason:
            logger.error(f"An error occur : {reason}")
            unique_violator = None
            if "username" in reason.args[0]:
                unique_violator = "username"
            elif "email" in reason.args[0]:
                unique_violator = "email"
            elif "phone" in reason.args[0]:
                unique_violator = "phone"
            else:
                raise exceptions.APIException("A fatal error occur, this will be reported, please try again later.") from reason
            raise exceptions.ValidationError(f"{unique_violator} already exists", 400) from reason
        return user

    # def update(self, instance, validated_data):
    #

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
        read_only_fields = ('merchant_id', 'profile_picture')
        extra_kwargs = {'password': {'write_only': True}}


class PhoneVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=6, required=True)
    phone = serializers.CharField(validators=(is_valid_phone,), max_length=15)
    device_imei = serializers.CharField(required=True, write_only=True)

    def get_tokens(self, user):
        return user.get_tokens(self.validated_data["device_imei"])

    def validate(self, attrs):
        user = User.objects.filter(phone=attrs["phone"]).first()
        if not user:
            raise serializers.ValidationError(f"User with the phone {attrs['phone']} does not exist")
        attrs["user"] = user
        otp = user.otps.latest()
        if otp.expiry > now() and otp.otp == attrs["token"]:
            pass
        elif otp.expiry < now() and otp.otp == attrs["token"]:
            raise serializers.ValidationError("Otp has expired", 400)
        else:
            raise serializers.ValidationError("Invalid OTP", 400)
        return attrs

    @transaction.atomic()
    def create(self, validated_data):
        user: User = validated_data["user"]
        merchant: CarMerchant = user.merchant
        user_wallet = Wallet.objects.filter(merchant=merchant).first()
        if not user_wallet and user.user_type == UserTypes.CarMerchant:
            Wallet.objects.get_or_create(
                merchant=user.merchant,
                balance=Decimal(0),
                trading_cash=Decimal(0),
                withdrawable_cash=Decimal(0),
                unsettled_cash=Decimal(0),
                total_cash=Decimal(0),
            )
        merchant.phone_verified = True
        merchant.save(update_fields=["phone_verified"])
        user.is_active = True
        user.save(update_fields=["is_active"])
        return user

    class Meta:
        fields = ('token', "device_imei")


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(required=True, min_length=6, max_length=6)

    def validate(self, attrs):
        user: User = self.context.get("user")
        if user:
            otp = user.otps.latest()
            if otp.expiry > now() and otp.otp == attrs["token"]:
                attrs["merchant"] = user.merchant
                return attrs
            elif otp.expiry < now() and otp.otp == attrs["token"]:
                raise serializers.ValidationError("Otp has expired", 400)
            else:
                raise serializers.ValidationError("Invalid OTP", 400)
        logger.error(f"user not found, serializer context: {self.context}")
        raise exceptions.APIException("Unable to verify the token, please try again later")

    def create(self, validated_data):
        merchant: CarMerchant = validated_data.get("merchant")
        merchant.email_verified = True
        merchant.save(update_fields=["email_verified"])
        return merchant


class CarMerchantSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    def get_user(self, merchant: CarMerchant):
        user_ser = UserSerializer(instance=merchant.user)
        return user_ser.data

    class Meta:
        model = CarMerchant
        fields = "__all__"


class CarBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarBrand
        fields = "__all__"

    def create(self, validated_data):
        if brand := CarBrand.objects.filter(**validated_data).first():
            return brand
        return super(CarBrandSerializer, self).create(validated_data)


# TokenObtainPairSerializer
class TokenObtainModSerializer(serializers.Serializer):
    username_field = get_user_model().USERNAME_FIELD

    default_error_messages = {
        'no_active_account': _('No active account found with the given credentials'),
        'new_device_detected': _(
            'You are logging in to this device for the first time,' '' 'kindly create a new transaction pin for this ' 'device'
        ),
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields[self.username_field] = serializers.CharField()
        self.fields['password'] = PasswordField()
        self.fields['device_imei'] = serializers.CharField(required=False, max_length=100)
        self.fields['skip_pin'] = serializers.BooleanField(required=False)
        self.fields["firebase_token"] = serializers.CharField(required=False)
        self.fields["device_type"] = serializers.CharField(required=False)

    def validate(self, attrs):
        # TODO check if device has a valid fcm token,
        #  if not fail login with a nice error
        authenticate_kwargs = {
            self.username_field: attrs[self.username_field],
            'password': attrs['password'],
        }
        with contextlib.suppress(KeyError):
            authenticate_kwargs['request'] = self.context['request']
        self.user: User = authenticate(**authenticate_kwargs)

        if not api_settings.USER_AUTHENTICATION_RULE(self.user):
            raise exceptions.AuthenticationFailed(
                self.error_messages['no_active_account'],
                'no_active_account',
            )
        if self.user.is_staff:
            return self.login_staff_user(attrs)
        if self.user.is_merchant:
            # if attrs.get("device_type")
            return self.login_merchant_user(attrs)

    @classmethod
    def get_token(cls, user, device_imei=None):
        token = RefreshToken.for_user(user)
        token["device_imei"] = device_imei
        return token

    def login_staff_user(self, attrs):
        User.update_last_login(self.user, **{})
        refresh = self.get_token(self.user)
        user = UserSerializer(instance=self.user)
        data = {'refresh': str(refresh), 'access': str(refresh.access_token), "user": user.data}
        return data

    def login_merchant_user(self, attrs):
        if not attrs.get('device_imei'):
            raise serializers.ValidationError("Device imei is required")

        device_logins = self.user.transaction_pins.filter(
            device_serial_number=attrs.get('device_imei'), status__in=(TransactionPinStatus.Active,)
        ).count()
        skip_pin = attrs.get("skip_pin", False)
        if device_logins < 1 and not skip_pin:
            raise exceptions.AuthenticationFailed(
                self.error_messages['new_device_detected'],
                'new_device_detected',
            )
        self.validate_firebase_(attrs.get('firebase_token'), self.user, attrs.get('device_imei'), attrs.get('device_type'))
        User.update_last_login(self.user, **dict(device_imei=attrs.get("device_imei")))

        refresh = self.get_token(self.user, attrs.get('device_imei'))
        car_merch = CarMerchantSerializer(instance=self.user.merchant)
        data = {'refresh': str(refresh), 'access': str(refresh.access_token), "merchant": car_merch.data}
        return data

    def validate_firebase_(self, token: str, user: User, imei: str, device_type: str):
        if token:
            device: FCMDevice = FCMDevice.objects.filter(registration_id=token, user=user).first()
            if not device:
                FCMDevice.objects.create(device_id=imei, registration_id=token, name=user.first_name, type=device_type, user=user)


class OtpSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    phone = serializers.CharField(validators=[is_valid_phone], required=False)

    def validate(self, attrs):
        if attrs.get("username"):
            return dict(username=attrs.get("username"))
        if attrs.get("phone"):
            return dict(phone=attrs.get("phone"))
        return dict(email=attrs.get("email"))

    def create(self, validated_data):
        users = User.objects.filter(**validated_data).first() if validated_data.get("username") else None
        if not users and validated_data.get("username"):
            key = list(validated_data.keys())[0]
            raise serializers.ValidationError(f"user with {key} {validated_data[key]} does not exist")
        expiry = datetime.datetime.now() + datetime.timedelta(minutes=OTP_EXPIRY)
        otp = "123456"
        return Otp.objects.create(
            user=users, expiry=expiry, otp=otp, email=validated_data.get("email"), phone=validated_data.get("phone")
        )


class DisbursementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Disbursement
        fields = ('id', 'created', 'trade_unit', 'amount')
        read_only_fields = ('id', 'created', 'trade_unit', 'amount')


class ActivitySerializer(serializers.ModelSerializer):
    content_type = serializers.HiddenField(default=None)
    object_id = serializers.HiddenField(default=None)
    activity_entity = serializers.SerializerMethodField()

    class Meta:
        model = Activity
        fields = ("created", "id", "activity_type", "object_id", "content_type", "description", 'activity_entity', "merchant")
        read_only_fields = ("created", "id", "activity_type", "object_id", "content_type", "description")

    def get_activity_entity(self, obj: Activity):
        ent = obj.activity
        if isinstance(ent, Transaction):
            return TransactionSerializer(instance=ent).data
        elif isinstance(ent, TradeUnit):
            return TradeUnitSerializer(instance=ent).data
        elif isinstance(ent, Disbursement):
            return DisbursementSerializer(instance=ent).data
        elif isinstance(ent, User):
            return UserSerializer(instance=ent).data
        elif isinstance(ent, CarMerchant):
            return CarMerchantSerializer(instance=ent).data
        elif isinstance(ent, Wallet):
            return WalletSerializer(instance=ent).data
        elif isinstance(ent, Car):
            return CarSerializer(instance=ent).data
        #  we don't know what this activity is, so we bailed
        return {}


class AssetsSerializer(serializers.ModelSerializer):
    content_object = serializers.HiddenField(default=None)
    object_id = serializers.HiddenField(default=None)
    content_type = serializers.HiddenField(default=None)
    asset = serializers.URLField(required=True)
    entity_type = serializers.ChoiceField(choices=AssetEntityType.choices, required=True)
    entity_id = serializers.UUIDField(required=True, write_only=True)

    class Meta:
        model = Assets
        fields = "__all__"
        read_only_fields = ("id", "created")

    def validate(self, attrs):
        if attrs["entity_type"] == AssetEntityType.Car:
            entity = Car.objects.filter(id=attrs["entity_id"]).first()
            if not entity:
                raise serializers.ValidationError("Car does not exist")
        elif attrs["entity_type"] == AssetEntityType.Merchant:
            entity = User.objects.filter(id=attrs["entity_id"]).first()
            if not entity:
                raise serializers.ValidationError("Merchant does not exist")
        else:
            raise serializers.ValidationError("Invalid entity type")
        attrs["content_object"] = entity
        return attrs

    def create(self, validated_data):
        return Assets.objects.create(
            content_object=validated_data["content_object"],
            asset=validated_data["asset"],
            entity_type=validated_data["entity_type"],
        )


class NotificationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notifications
        fields = "__all__"
        read_only_fields = ("id", "created", "modified")

    def create(self, validated_data):
        return Notifications.objects.create(**validated_data)


# class OtpSerializer(serializers.Serializer):
#     username = serializers.CharField(required=False, min_length=1)
#     email = serializers.EmailField(required=False)
#     phone = serializers.CharField(validators=[is_valid_phone], required=False)
#
#     def validate(self, attrs):
#         if attrs.get("username"):
#             return dict(username=attrs.get("username"))
#         if attrs.get("phone"):
#             return dict(phone=attrs.get("phone"))
#         return dict(email=attrs.get("email"))
