from decimal import Decimal

import factory
from django.contrib.auth import get_user_model

from src.models.models import Wallet, UserTypes, CarMerchant

User = get_user_model()


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ('username',)

    id = factory.Faker('uuid4')
    username = factory.Sequence(lambda n: f'testuser{n}')
    password = factory.PostGenerationMethodCall('set_password', 'asdf')
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True
    is_staff = False
    user_type = None
    phone = factory.Sequence(lambda n: f'+234812901477{n}')


class CarMerchantFactory(factory.django.DjangoModelFactory):
    user = factory.SubFactory(UserFactory, user_type=UserTypes.CarMerchant)
    bvn = factory.Sequence(lambda n: f"2334892900292{n}")

    class Meta:
        model = CarMerchant


class WalletFactory(factory.django.DjangoModelFactory):
    balance = Decimal(1000000)
    merchant = factory.SubFactory(CarMerchantFactory)
    trading_cash = Decimal(0.00)
    withdrawable_cash = Decimal(1000000)
    unsettled_cash = Decimal(0.00)
    total_cash = Decimal(1000000)

    class Meta:
        model = Wallet
