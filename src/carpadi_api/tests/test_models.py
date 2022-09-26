from decimal import Decimal
from typing import List

from django.core.exceptions import ValidationError
from django.test import TestCase
from nose.tools import ok_

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
    Disbursement,
    TradeUnit,
    Transaction,
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

    def test_money_move_to_unsettled_given_disbursement(self):
        bought_price = Decimal(100000)
        maintenance = Decimal(2000)
        resale_price = Decimal(105100.0) + maintenance
        self.prepare_car(resale=resale_price)
        trade = TradeFactory(car=self.car, trade_status=TradeStates.Completed)
        merchant: List[CarMerchant] = self.wallet.merchant
        tx = TransactionsFactory(
            amount=trade.price_per_slot,
            wallet=self.wallet,
            transaction_type=TransactionTypes.Credit,
            transaction_kind=TransactionKinds.Disbursement,
            transaction_status=TransactionStatus.Success,
        )
        unit: TradeUnit = TradeUnitFactory(merchant=merchant, trade=trade, buy_transaction=tx)
        disb = Disbursement.objects.create(
            trade_unit=unit, disbursement_status=DisbursementStates.Unsettled, amount=unit.payout()
        )
        self.wallet.refresh_from_db()
        assert self.wallet.unsettled_cash == disb.amount
        withdrawabale_cash = self.wallet.withdrawable_cash
        disb.settle()
        disb.refresh_from_db()
        self.wallet.refresh_from_db()
        assert self.wallet.unsettled_cash == Decimal(0.0)
        assert disb.disbursement_status == DisbursementStates.Settled
        assert self.wallet.withdrawable_cash == withdrawabale_cash + disb.amount
        assert self.wallet.trading_cash == Decimal(0.0)

    def test_wallet_update_balance_when_deposit(self):
        amount = Decimal(10000)
        tx: Transaction = TransactionsFactory(
            amount=amount,
            wallet=self.wallet,
            transaction_type=TransactionTypes.Credit,
            transaction_kind=TransactionKinds.Deposit,
            transaction_status=TransactionStatus.Success,
        )
        withdrawable_cash = self.wallet.withdrawable_cash
        self.wallet.update_balance(tx)
        assert self.wallet.withdrawable_cash == withdrawable_cash + tx.amount

    def test_wallet_cant_update_deposit_unless_successful(self):
        amount = Decimal(10000)
        tx: Transaction = TransactionsFactory(
            amount=amount,
            wallet=self.wallet,
            transaction_type=TransactionTypes.Credit,
            transaction_kind=TransactionKinds.Deposit,
            transaction_status=TransactionStatus.Pending,
        )
        try:
            self.wallet.update_balance(tx)
        except Exception as reason:
            assert isinstance(reason, ValidationError)
