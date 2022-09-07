from decimal import Decimal
from typing import List

from django.test import TestCase
from nose.tools import ok_, eq_

from src.carpadi_admin.tests.factories import (
    TransactionsFactory,
    InspectionFactory,
    SparePartFactory,
    TradeFactory,
    TradeUnitFactory,
)
from src.models.models import (
    UserTypes,
    User,
    Settings,
    TransactionTypes,
    TransactionKinds,
    TransactionStatus,
    InspectionVerdict,
    InspectionStatus,
    CarMaintenance,
    TradeStates,
    CarMerchant,
    DisbursementStates,
    CarStates,
)
from src.models.serializers import CreateUserSerializer
from src.models.test.factories import WalletFactory


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
        cls.set = Settings.objects.create(
            merchant_trade_rot_percentage=Decimal(5.00), carpadi_commision=Decimal(50.00), bonus_percentage=Decimal(50.00)
        )

    def setUp(self) -> None:
        self.wallet = WalletFactory(
            balance=Decimal(100000.00), withdrawable_cash=Decimal(100000.00), total_cash=Decimal(100000.00)
        )
        self.inspection = InspectionFactory(
            inspector=self.admin,
            inspection_assignor=self.admin,
            inspection_verdict=InspectionVerdict.Good,
            status=InspectionStatus.Completed,
        )
        self.spare_part = SparePartFactory()
        self.car = self.inspection.car

    def test_money_moved_to_trading_give_trade_unit_purchase(self):
        tx = TransactionsFactory(
            amount=Decimal(20000),
            wallet=self.wallet,
            transaction_type=TransactionTypes.Debit,
            transaction_kind=TransactionKinds.TradeUnitPurchases,
            transaction_status=TransactionStatus.Success,
        )
        self.wallet.update_balance(tx)
        assert self.wallet.trading_cash == Decimal(20000)
        assert self.wallet.withdrawable_cash == Decimal(100000) - self.wallet.trading_cash

    def prepare_car(self, bought=None, resale=None):
        self.car.update_on_inspection_changes(self.inspection)
        self.maintenance = CarMaintenance.objects.create(maintenance=self.spare_part, car=self.car)
        self.car.bought_price = Decimal(bought or 100000)
        self.car.resale_price = Decimal(resale or 150000)
        self.car.save()
        self.car.update_on_sold()
