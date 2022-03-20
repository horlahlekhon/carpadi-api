import re

from rest_framework import serializers, exceptions

from src.models.models import Transactions, Wallets, CarMerchant, BankAccount, CarBrand, Car, UserTypes
from src.common.serializers import ThumbnailerJSONSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer, PasswordField
from django.db.utils import IntegrityError
from django.contrib.auth import get_user_model, authenticate
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

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
    tokens = serializers.SerializerMethodField()
    phone = serializers.CharField(max_length=15, required=True)
    email = serializers.EmailField(required=True)
    birth_date = serializers.DateField(required=False)
    username = serializers.CharField(required=False)
    user_type = serializers.ChoiceField(required=False, choices=UserTypes.choices)

    def get_tokens(self, user):
        return user.get_tokens()

    def create(self, validated_data):
        # call create_user on user object. Without this
        # the password will be stored in plain text.
        try:
            validated_data["is_active"] = False
            validated_data['username'] = (
                str(validated_data['username']).lower() if validated_data.get("username") else validated_data.get(
                    "email")
            )
            user = User.objects.create_user(**validated_data)
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
            'tokens',
            'profile_picture',
            "phone",
            'birth_date',
            'user_type',
        )
        read_only_fields = ('tokens',)
        extra_kwargs = {'password': {'write_only': True}}


def is_valid_phone(phone):
    is_valid = re.search(r'\+?[\d]{3}[\d]{10}', phone)
    if not is_valid:
        raise serializers.ValidationError("Invalid phone number, phone number should match format: +234 000 000 0000")
    return phone


class PhoneVerificationSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=6, required=True)
    phone = serializers.CharField(validators=(is_valid_phone,), max_length=15)

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
        'new_device_detected': _('You are logging in to this device for the first time,'
                                 ' kindly create a new transaction pin for this device')
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

        device_logins = self.user.transaction_pins.filter(device_serial_number=attrs.get('device_imei')).count()
        skip_pin = attrs.get("skip_pin")
        if device_logins < 1 and skip_pin:
            raise exceptions.AuthenticationFailed(
                self.error_messages['new_device_detected'],
                'new_device_detected',
            )
        User.update_last_login(self.user, **dict(device_imei=attrs.get("device_imei")))

        refresh = self.get_token(self.user)
        car_merch = CarMerchantSerializer(instance=self.user.merchant)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            "merchant": car_merch.data
        }
        return data

    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)
