from django.test import TestCase
from nose.tools import ok_, eq_

from src.models.models import UserTypes, User
from src.models.serializers import CreateUserSerializer


class TestWallet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_data = {
            'username': 'test',
            'password': 'test',
            "email": "olalekan@gmail.com",
            "phone": "+2348129014778",
            "user_type": UserTypes.CarMerchant.value,
        }
        serializer = CreateUserSerializer(data=cls.user_data)
        isvalid = serializer.is_valid()
        ok_(isvalid)
        cls.user: User = serializer.save()
        cls.admin: User = User.objects.create_superuser("admin", email="admin@localhost", password="passersby")

    # def setUp(self) -> None:
