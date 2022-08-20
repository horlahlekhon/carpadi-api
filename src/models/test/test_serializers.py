from django.contrib.auth.hashers import check_password
from django.test import TestCase, SimpleTestCase, TransactionTestCase
from django_seed import Seed
from nose.tools import eq_, ok_

from ..models import UserTypes, User
from ..serializers import CreateUserSerializer, UserSerializer
from ...common.seeder import PadiSeeder


class TestCreateUserSerializer(TestCase):
    def setUp(self):
        self.merchant_user_data = {'username': 'test', 'password': 'test',
                                   "email": "olalekan@gmail.com",
                                   "phone": "+2348129014778", "user_type": UserTypes.CarMerchant.value}

    def test_serializer_with_empty_data(self):
        serializer = CreateUserSerializer(data={})
        eq_(serializer.is_valid(), False)

    def test_serializer_with_valid_data(self):
        serializer = CreateUserSerializer(data=self.merchant_user_data)
        isvalid = serializer.is_valid(raise_exception=True)
        ok_(isvalid)
        user = User.objects.filter(email=self.merchant_user_data["email"]).first()
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
        self.user = {'username': 'test', 'password': 'test',
                                   "email": "olalekan@gmail.com",
                                   "phone": "+2348129014778", "user_type": UserTypes.CarMerchant.value}
        serializer = CreateUserSerializer(data=self.user)
        isvalid = serializer.is_valid()
        user = serializer.save()

    def test_user_update_sucessful(self):
        update = dict(profile_picture=PadiSeeder.get_asset(1)[0],
                      first_name=self.faker.first_name(), last_name=self.faker.last_name())
        serializer = UserSerializer(data=update, partial=True)
        eq_(serializer.is_valid(), True)
        user = serializer.save()
        ok_(user)
        eq_(user.first_name, update["first_name"])
        eq_(user.last_name, update["last_name"])
