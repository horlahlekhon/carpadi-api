import uuid
from decimal import Decimal

from django.contrib.auth.hashers import check_password
from django.test import TestCase, SimpleTestCase, TransactionTestCase
from django_seed import Seed
from nose.tools import eq_, ok_
from rest_framework.exceptions import AuthenticationFailed

from ..models import UserTypes, User, Otp, CarMerchant, Wallet
from ..serializers import CreateUserSerializer, UserSerializer, PhoneVerificationSerializer, TokenObtainModSerializer
from ...common.seeder import PadiSeeder


class TestCreateUserSerializer(TestCase):
    def setUp(self):
        self.merchant_user_data = {
            'username': 'test',
            'password': 'test',
            "email": "olalekan@gmail.com",
            "phone": "+2348129014778",
            "user_type": UserTypes.CarMerchant.value,
        }

    def test_serializer_with_empty_data(self):
        serializer = CreateUserSerializer(data={})
        eq_(serializer.is_valid(), False)

    def test_serializer_with_valid_data(self):
        serializer = CreateUserSerializer(data=self.merchant_user_data)
        isvalid = serializer.is_valid(raise_exception=True)
        ok_(isvalid)
        serializer.save()
        user = User.objects.filter(email=self.merchant_user_data["email"]).first()
        print(user)
        ok_(user)
        eq_(user.is_merchant(), True)
        eq_(user.is_active, False)
        eq_(user.is_staff, False)

    def test_serializer_hashes_password_and_user_created(self):
        serializer = CreateUserSerializer(data=self.merchant_user_data)
        isvalid = serializer.is_valid()
        ok_(isvalid)
        user = serializer.save()
        ok_(check_password(self.merchant_user_data.get('password'), user.password))
        user = User.objects.filter(email=self.merchant_user_data["email"]).first()
        ok_(user)


class TestUserSerializer(TestCase):
    seeder = Seed.seeder()
    faker = seeder.faker

    def setUp(self) -> None:
        self.user_data = {
            'username': 'test',
            'password': 'test',
            "email": "olalekan@gmail.com",
            "phone": "+2348129014778",
            "user_type": UserTypes.CarMerchant.value,
        }
        serializer = CreateUserSerializer(data=self.user_data)
        isvalid = serializer.is_valid()
        self.user = user = serializer.save()

    def test_user_update_sucessful(self):
        update = dict(
            profile_picture=PadiSeeder.get_asset(1)[0], first_name=self.faker.first_name(), last_name=self.faker.last_name()
        )
        serializer = UserSerializer(data=update, instance=self.user, partial=True)
        eq_(serializer.is_valid(), True)
        user = serializer.save()
        ok_(user)
        eq_(user.first_name, update["first_name"])
        eq_(user.last_name, update["last_name"])
        eq_(user.profile_picture.asset, update["profile_picture"])

    def test_user_data_renders_correctly(self):
        serializer = UserSerializer(instance=self.user)
        data = serializer.data
        eq_(data["first_name"], self.user.first_name)
        eq_(data["username"], self.user.username)
        eq_(data["username"], self.user.username)
        eq_(data.get("password"), None)
        # eq_(data["user_type"], UserTypes.CarMerchant.value)


class TestPhoneVerificationSerializer(TestCase):
    def setUp(self) -> None:
        self.user_data = {
            'username': 'test',
            'password': 'test',
            "email": "olalekan@gmail.com",
            "phone": "+2348129014778",
            "user_type": UserTypes.CarMerchant.value,
        }
        serializer = CreateUserSerializer(data=self.user_data)
        isvalid = serializer.is_valid()
        self.user = user = serializer.save()

    def test_user_validated_successfully(self):
        otp: Otp = self.user.otps.latest()
        ok_(otp, "otp was not created")
        payload = dict(phone=self.user.phone, token=otp.otp, device_imei=str(uuid.uuid4()))
        serializer = PhoneVerificationSerializer(data=payload)
        ok_(serializer.is_valid())
        user: User = serializer.save()
        merchant = CarMerchant.objects.filter(user_id=user.id).first()
        ok_(merchant)
        wallet: Wallet = merchant.wallet
        ok_(wallet)
        eq_(wallet.balance, Decimal(0.00))
        eq_(wallet.withdrawable_cash, Decimal(0.00))
        eq_(wallet.unsettled_cash, Decimal(0.00))
        eq_(wallet.get_total_cash(), Decimal(0.00))

    def test_invalid_token_fails_validation(self):
        payload = dict(phone=self.user.phone, token="wrong", device_imei=str(uuid.uuid4()))
        serializer = PhoneVerificationSerializer(data=payload)
        eq_(serializer.is_valid(), False)


class TestTokenObtainModSerializer(TestCase):
    def setUp(self) -> None:
        self.user_data = {
            'username': 'test',
            'password': 'test',
            "email": "olalekan@gmail.com",
            "phone": "+2348129014778",
            "user_type": UserTypes.CarMerchant.value,
        }
        serializer = CreateUserSerializer(data=self.user_data)
        serializer.is_valid()
        self.user = serializer.save()
        self.user.refresh_from_db()
        otp = self.user.otps.latest()
        payload = dict(phone=self.user.phone, token=otp.otp, device_imei=str(uuid.uuid4()))
        serializer = PhoneVerificationSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        serializer.save()

    def test_user_login_rejected_given_not_tx_pin_and_no_skip_pin(self):
        payload = dict(username=self.user.username, password=self.user_data["password"], device_imei=str(uuid.uuid4()))
        ser = TokenObtainModSerializer(data=payload)
        try:
            is_valid = ser.is_valid()
            errors = ser.errors
        except Exception as reason:
            eq_(type(reason), AuthenticationFailed)
            eq_(
                reason.args[0],
                "You are logging in to this device for the first time,kindly create a new transaction " "pin for this device",
            )

    def test_login_successful_given_skip_pin(self):
        payload = dict(
            username=self.user.username, password=self.user_data["password"], device_imei=str(uuid.uuid4())[:20], skip_pin=True
        )
        ser = TokenObtainModSerializer(data=payload)
        is_valid = ser.is_valid()
        errors = ser.errors
        eq_(errors, {})
        eq_(is_valid, True)

    def test_login_successful_given_admin_user(self):
        payload = dict(username=self.user.username, password=self.user_data["password"])
