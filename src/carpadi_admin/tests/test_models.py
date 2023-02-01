from decimal import Decimal
from typing import List

import faker_vehicle
from django.test import TestCase
from faker import factory

from src.carpadi_admin.tests import BaseTest
from src.carpadi_admin.tests.factories import (
    VehicleFactory,
    CarFactory,
    InspectionFactory,
    SparePartFactory,
    TradeFactory,
    TradeUnitFactory,
    TransactionsFactory,
)
from src.models.models import (
    User,
    UserTypes,
    InspectionVerdict,
    InspectionStatus,
    CarMaintenance,
    CarStates,
    Settings,
    TradeStates,
    CarMerchant,
    TransactionTypes,
    TransactionKinds,
    TransactionStatus,
    DisbursementStates,
    Disbursement,
    Wallet,
    Trade,
)
from src.models.test.factories import UserFactory, WalletFactory, CarMerchantFactory


class CarTests(BaseTest):
    def setUp(self) -> None:
        super(CarTests, self).setUp()
        self.merchants = UserFactory(user_type=UserTypes.CarMerchant)
        self.inspection = InspectionFactory(
            inspector=self.admin,
            inspection_assignor=self.admin,
            inspection_verdict=InspectionVerdict.Good,
            status=InspectionStatus.Completed,
        )
        self.spare_part = SparePartFactory()
        self.car = self.inspection.car

    def test_car_creation_with_maintenance(self):
        assert self.car.status == CarStates.New
        self.car.update_on_inspection_changes(self.inspection)
        self.maintenance = CarMaintenance.objects.create(maintenance=self.spare_part, car=self.car)
        self.car.bought_price = Decimal(100000)
        self.car.resale_price = Decimal(150000)
        self.car.save()
        self.car.refresh_from_db()
        assert self.car.maintenance_cost_calc() == Decimal(2000.0)
        assert self.car.total_cost_calc() == Decimal(100000) + Decimal(2000)
        assert self.car.margin_calc() == Decimal(150000) - (Decimal(100000) + Decimal(2000))
        assert self.car.status == CarStates.Inspected

    def test_car_update_on_sold(self):
        assert self.car.status == CarStates.New
        self.car.update_on_inspection_changes(self.inspection)
        self.maintenance = CarMaintenance.objects.create(maintenance=self.spare_part, car=self.car)
        self.car.bought_price = Decimal(100000)
        self.car.resale_price = Decimal(150000)
        self.car.save()
        self.car.update_on_sold()
        self.car.refresh_from_db()
        assert self.car.cost_of_repairs == Decimal(2000)
        assert self.car.total_cost == Decimal(2000.0) + Decimal(100000)
        assert self.car.margin == Decimal(150000) - Decimal(100000) - Decimal(2000)
        assert self.car.status == CarStates.Sold


class TestTrade(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.set = Settings.objects.create(
            merchant_trade_rot_percentage=Decimal(5.00), carpadi_commision=Decimal(50.00), bonus_percentage=Decimal(50.00)
        )

    def setUp(self) -> None:
        super(TestTrade, self).setUp()
        self.merchants = CarMerchantFactory.create_batch(size=5)
        self.wallets = []
        count = [i.delete() for i in Wallet.objects.all()]
        self.wallets.append(WalletFactory(merchant=self.merchants[0]))
        self.wallets.append(WalletFactory(merchant=self.merchants[1]))
        self.wallets.append(WalletFactory(merchant=self.merchants[2]))
        self.wallets.append(WalletFactory(merchant=self.merchants[3]))
        self.wallets.append(WalletFactory(merchant=self.merchants[4]))
        self.inspection = InspectionFactory(
            inspector=self.admin,
            inspection_assignor=self.admin,
            inspection_verdict=InspectionVerdict.Good,
            status=InspectionStatus.Completed,
        )
        self.spare_part = SparePartFactory()
        self.car = self.inspection.car

    def prepare_car(self, bought=None, resale=None, maintain=True):
        self.car.update_on_inspection_changes(self.inspection)
        self.maintenance = CarMaintenance.objects.create(maintenance=self.spare_part, car=self.car) if maintain else Decimal(0.0)
        self.car.bought_price = Decimal(bought or 100000)
        self.car.resale_price = Decimal(resale or 150000)
        self.car.save()
        self.car.update_on_sold()

    def test_create_trade_with_excess_margin(self):
        """
        bought_price = Decimal(100000)
        resale_price = Decimal(150000)
        maintenance = Decimal(2000)
        bonus_percentage=Decimal(50.00)
        """
        self.prepare_car()
        trade = TradeFactory(car=self.car, trade_status=TradeStates.Completed)
        rot = (Decimal(100000) + Decimal(2000)) * Decimal(5.00) / 100
        assert trade.return_on_trade_calc() == rot
        assert trade.return_on_trade_per_slot == rot / 5
        assert trade.carpadi_commission_calc() == rot / 2
        assert trade.margin_calc() == (Decimal(150000) - Decimal(100000)) - Decimal(2000)
        assert trade.return_on_trade_calc_percent() == rot / Decimal(102000) * 100
        assert trade.calculate_price_per_slot() == (Decimal(100000) + Decimal(2000)) / 5
        bonus = (Decimal(150000) - Decimal(100000)) - Decimal(2000) - rot
        assert trade.bonus_calc() == bonus
        traders_bonus = bonus * Decimal(50.00) / 100
        assert trade.traders_bonus() == traders_bonus
        assert trade.carpadi_bonus_calc() == bonus - traders_bonus
        assert trade.carpadi_rot_calc() == (bonus - traders_bonus) + rot / 2

    def test_create_trade_without_excess(self):
        """
        bought_price = Decimal(100000)
        resale_price = Decimal(105100.0)
        maintenance = Decimal(2000)
        bonus_percentage=Decimal(50.00)
        """
        bought_price = Decimal(100000)
        self.car.bought_price = bought_price
        self.car.save(updated_fields=['bought_price'])
        maintenance = Decimal(2000)
        resale_price = Decimal(105100.0) + maintenance
        self.prepare_car(resale=resale_price)
        trade = TradeFactory(car=self.car, trade_status=TradeStates.Completed)
        rot = (bought_price + maintenance) * Decimal(5.00) / 100
        assert trade.return_on_trade_calc() == rot
        assert trade.return_on_trade_per_slot == rot / 5
        assert trade.carpadi_commission_calc() == rot / 2
        assert trade.margin_calc() == (resale_price - bought_price) - maintenance
        assert trade.return_on_trade_calc_percent() == rot / Decimal(102000) * 100
        assert trade.calculate_price_per_slot() == (bought_price + maintenance) / 5
        bonus = Decimal(0)
        assert trade.bonus_calc() == bonus
        traders_bonus = bonus * Decimal(50.00) / 100
        assert trade.traders_bonus() == traders_bonus
        assert trade.carpadi_bonus_calc() == bonus - traders_bonus
        assert trade.carpadi_rot_calc() == (bonus - traders_bonus) + rot / 2

    def test_create_trade_without_excess(self):
        """
        bought_price = Decimal(100000)
        resale_price = Decimal(105100.0)
        maintenance = Decimal(2000)
        bonus_percentage=Decimal(50.00)
        """
        bought_price = Decimal(1_000_000)
        maintenance = Decimal(2000)
        resale_price = Decimal(1_100_000)  # + maintenance
        self.prepare_car(resale=resale_price, bought=bought_price, maintain=False)
        trade: Trade = TradeFactory(car=self.car, trade_status=TradeStates.Completed, slots_available=4)
        # rot = (bought_price ) * Decimal(5.00) / 100
        min_sale_price = trade.min_sale_price_calc()
        estimated_carpadi_rot = trade.estimated_carpadi_rot()
        rot = trade.return_on_trade_calc()
        rot_per_slot = trade.return_on_trade_per_slot
        carpadi_commision = trade.carpadi_commission_calc()
        margin = trade.margin_calc()
        rot_perc = trade.return_on_trade_calc_percent()
        pps = trade.calculate_price_per_slot()
        bonus = Decimal(0)
        bonus = trade.bonus_calc()
        traders_bonus = bonus * Decimal(50.00) / 100
        trader_bonus = trade.traders_bonus()
        cp_bonus = trade.carpadi_bonus_calc()
        cp_rot = trade.carpadi_rot_calc()
        assert True

    # def test_create_trade_with_loss(self):
    #     """
    #     bought_price = Decimal(100000)
    #     resale_price = Decimal(50000.0)
    #     maintenance = Decimal(2000)
    #     bonus_percentage=Decimal(50.00)
    #     """
    #     bought_price = Decimal(100000)
    #     maintenance = Decimal(2000)
    #     resale_price = Decimal(50000.0) + maintenance
    #     self.prepare_car(resale=resale_price)
    #     trade = TradeFactory(car=self.car, trade_status=TradeStates.Completed)
    #     rot = (bought_price + maintenance) * Decimal(5.00) / 100
    #     assert trade.return_on_trade_calc() == rot
    #     assert trade.return_on_trade_per_slot == rot / 5
    #     assert trade.carpadi_commission_calc() == rot / 2
    #     assert trade.margin_calc() == (resale_price - bought_price) - maintenance
    #     assert trade.return_on_trade_calc_percent() == rot / Decimal(102000) * 100
    #     assert trade.calculate_price_per_slot() == (bought_price + maintenance) / 5
    #     bonus = Decimal(0)
    #     assert trade.bonus_calc() == bonus
    #     traders_bonus = bonus * Decimal(50.00) / 100
    #     assert trade.traders_bonus() == traders_bonus
    #     assert trade.carpadi_bonus_calc() == bonus - traders_bonus
    #     assert trade.carpadi_rot_calc() == Decimal(0)
    #     assert trade.deficit_balance() == abs(resale_price - (bought_price + maintenance))
    #
    # def test_trade_with_units(self):
    #     self.car.update_on_inspection_changes(self.inspection)
    #     self.maintenance = CarMaintenance.objects.create(maintenance=self.spare_part, car=self.car)
    #     self.car.bought_price = Decimal(100000)
    #     self.car.resale_price = Decimal(150000)
    #     self.car.save()
    #     trade = TradeFactory(car=self.car, trade_status=TradeStates.Ongoing)
    #     units = []
    #     merchants: List[CarMerchant] = [i.merchant for i in self.wallets]
    #     for merchant in merchants:
    #         tx = TransactionsFactory(
    #             amount=trade.price_per_slot,
    #             wallet=merchant.wallet,
    #             transaction_type=TransactionTypes.Debit,
    #             transaction_kind=TransactionKinds.TradeUnitPurchases,
    #             transaction_status=TransactionStatus.Success,
    #         )
    #         unit = TradeUnitFactory(merchant=merchant, trade=trade, buy_transaction=tx)
    #         units.append(unit)
    #     trade.refresh_from_db()
    #     assert trade.trade_status == TradeStates.Purchased
    #     assert trade.remaining_slots() == 0
    #     assert trade.units.count() == len(units)
    #     assert trade.return_on_trade_calc() == trade.return_on_trade_per_slot * trade.slots_available
    #     trade.trade_status = TradeStates.Completed
    #     trade.save(update_fields=["trade_status"])
    #     trade.check_updates()
    #     trade.refresh_from_db()
    #     for unit in trade.units.all():
    #         assert unit.disbursement is not None
    #         assert unit.disbursement.disbursement_status == DisbursementStates.Unsettled
    #         assert unit.checkout_transaction is not None
    #         assert unit.checkout_transaction == unit.disbursement.transaction
    #         trade_bonus = (unit.trade.bonus_calc() * self.set.bonus_percentage / 100) / 5
    #         base = (unit.trade.return_on_trade_per_slot * unit.slots_quantity) + unit.unit_value
    #         commission = unit.trade.carpadi_commission_per_slot() * unit.slots_quantity
    #         assert unit.disbursement.transaction.amount == (base + trade_bonus) - commission
    #         assert unit.trade_bonus == trade_bonus
    #     self.car.refresh_from_db()
    #     assert self.car.cost_of_repairs == Decimal(2000)
    #     assert self.car.total_cost == Decimal(2000.0) + Decimal(100000)
    #     assert self.car.margin == Decimal(150000) - Decimal(100000) - Decimal(2000)
    #     assert self.car.status == CarStates.Sold
    #
    # def test_close_trade(self):
    #     self.car.update_on_inspection_changes(self.inspection)
    #     self.maintenance = CarMaintenance.objects.create(maintenance=self.spare_part, car=self.car)
    #     self.car.bought_price = Decimal(100000)
    #     self.car.resale_price = Decimal(150000)
    #     self.car.save()
    #     trade = TradeFactory(car=self.car, trade_status=TradeStates.Ongoing)
    #     units = []
    #     merchants: List[CarMerchant] = [i.merchant for i in self.wallets]
    #     for merchant in merchants:
    #         tx = TransactionsFactory(
    #             amount=trade.price_per_slot,
    #             wallet=merchant.wallet,
    #             transaction_type=TransactionTypes.Debit,
    #             transaction_kind=TransactionKinds.TradeUnitPurchases,
    #             transaction_status=TransactionStatus.Success,
    #         )
    #         unit = TradeUnitFactory(merchant=merchant, trade=trade, buy_transaction=tx)
    #         units.append(unit)
    #     trade.refresh_from_db()
    #     assert trade.trade_status == TradeStates.Purchased
    #     assert trade.remaining_slots() == 0
    #     assert trade.units.count() == len(units)
    #     trade.trade_status = TradeStates.Completed
    #     trade.save(update_fields=["trade_status"])
    #     trade.check_updates()
    #     for unit in trade.units.all():
    #         assert unit.merchant.wallet.unsettled_cash == unit.disbursement.amount
    #         assert unit.disbursement.transaction.transaction_status == TransactionStatus.Unsettled
    #         assert unit.disbursement.disbursement_status == DisbursementStates.Unsettled
    #     trade.close()
    #     trade.refresh_from_db()
    #     assert trade.trade_status == TradeStates.Closed
    #     for unit in trade.units.all():
    #         assert unit.disbursement.disbursement_status == DisbursementStates.Settled
    #         assert unit.disbursement.transaction.transaction_status == TransactionStatus.Success
    #         assert unit.merchant.wallet.unsettled_cash == Decimal(0.00)
    #     # assert trade.
    #
    # def test_trade_with_trade_unit_with_loss(self):
    #     bought_price = Decimal(100000)
    #     maintenance = Decimal(2000)
    #     resale_price = Decimal(90000.0) + maintenance
    #     self.prepare_car(resale=resale_price)
    #     trade = TradeFactory(car=self.car, trade_status=TradeStates.Ongoing)
    #     units = []
    #     wallets = WalletFactory.create_batch(
    #         size=5, balance=Decimal(20400.00), withdrawable_cash=Decimal(20400.00), total_cash=Decimal(20400.00)
    #     )
    #     merchants: List[CarMerchant] = [i.merchant for i in wallets]
    #     for merchant in merchants:
    #         tx = TransactionsFactory(
    #             amount=trade.price_per_slot,
    #             wallet=merchant.wallet,
    #             transaction_type=TransactionTypes.Debit,
    #             transaction_kind=TransactionKinds.TradeUnitPurchases,
    #             transaction_status=TransactionStatus.Success,
    #         )
    #         unit = TradeUnitFactory(merchant=merchant, trade=trade, buy_transaction=tx)
    #         tx.wallet.update_balance(tx=tx)
    #         units.append(unit)
    #     trade.refresh_from_db()
    #     assert trade.trade_status == TradeStates.Purchased
    #     assert trade.remaining_slots() == 0
    #     assert trade.units.count() == len(units)
    #     assert trade.deficit_balance() == Decimal(10000.00)
    #     trade.trade_status = TradeStates.Completed
    #     trade.save(update_fields=["trade_status"])
    #     # unit = trade.units.first()
    #     trade.check_updates()
    #     trade.refresh_from_db()
    #     for unit in trade.units.all():
    #         assert unit.merchant.wallet.unsettled_cash == unit.disbursement.amount
    #         assert unit.disbursement.transaction.transaction_status == TransactionStatus.Unsettled
    #         assert unit.disbursement.disbursement_status == DisbursementStates.Unsettled
    #     trade.close()
    #     trade.refresh_from_db()
    #     assert trade.trade_status == TradeStates.Closed
    #     # unit = trade.units.first()
    #     for unit in trade.units.all():
    #         ideal_return = (unit.unit_value + trade.return_on_trade_per_slot * unit.slots_quantity) - (
    #             trade.deficit_balance() / 5
    #         ) * unit.slots_quantity
    #         commission = unit.trade.carpadi_commission_per_slot() * unit.slots_quantity
    #         assert unit.merchant.wallet.withdrawable_cash == ideal_return - commission
    #
    # def test_rollback_trade_completion(self):
    #     self.car.update_on_inspection_changes(self.inspection)
    #     self.maintenance = CarMaintenance.objects.create(maintenance=self.spare_part, car=self.car)
    #     self.car.bought_price = Decimal(100000)
    #     self.car.resale_price = Decimal(150000)
    #     self.car.save()
    #     trade = TradeFactory(car=self.car, trade_status=TradeStates.Ongoing)
    #     units = []
    #     merchants: List[CarMerchant] = [i.merchant for i in self.wallets]
    #     for merchant in merchants:
    #         tx = TransactionsFactory(
    #             amount=trade.price_per_slot,
    #             wallet=merchant.wallet,
    #             transaction_type=TransactionTypes.Debit,
    #             transaction_kind=TransactionKinds.TradeUnitPurchases,
    #             transaction_status=TransactionStatus.Success,
    #         )
    #         unit = TradeUnitFactory(merchant=merchant, trade=trade, buy_transaction=tx)
    #         units.append(unit)
    #     trade.refresh_from_db()
    #     assert trade.trade_status == TradeStates.Purchased
    #     assert trade.remaining_slots() == 0
    #     assert trade.units.count() == len(units)
    #     trade.trade_status = TradeStates.Completed
    #     trade.save(update_fields=["trade_status"])
    #     trade.check_updates()
    #     trade.refresh_from_db()
    #     for unit in trade.units.all():
    #         assert unit.disbursement is not None
    #         assert unit.disbursement.disbursement_status == DisbursementStates.Unsettled
    #         assert unit.checkout_transaction is not None
    #         assert unit.checkout_transaction == unit.disbursement.transaction
    #         trade_bonus = (unit.trade.bonus_calc() * self.set.bonus_percentage / 100) / 5
    #         base = (unit.trade.return_on_trade_per_slot * unit.slots_quantity) + unit.unit_value
    #         commission = unit.trade.carpadi_commission_per_slot() * unit.slots_quantity
    #         assert unit.disbursement.transaction.amount == (base + trade_bonus) - commission
    #         assert unit.trade_bonus == trade_bonus
    #     self.car.refresh_from_db()
    #     assert self.car.cost_of_repairs == Decimal(2000)
    #     assert self.car.total_cost == Decimal(2000.0) + Decimal(100000)
    #     assert self.car.margin == Decimal(150000) - Decimal(100000) - Decimal(2000)
    #     assert self.car.status == CarStates.Sold
    #     trade.rollback()
    #     trade.refresh_from_db()
    #     assert trade.trade_status == TradeStates.Purchased
    #     assert trade.car.status == CarStates.OngoingTrade
    #     assert trade.carpadi_bonus == Decimal(0.00)
    #     assert trade.total_carpadi_rot == Decimal(0.00)
    #     assert trade.traders_bonus_per_slot == Decimal(0.00)
    #     assert trade.car.cost_of_repairs == Decimal(0.00)
    #     assert trade.car.margin == Decimal(0.00)
    #     for unit in trade.units.all():
    #         dis: Disbursement = unit.disbursement
    #         assert dis.disbursement_status == DisbursementStates.RolledBack
    #         assert dis.transaction.transaction_status == TransactionStatus.RolledBack
    #         wallet = unit.merchant.wallet
    #         assert wallet.unsettled_cash == Decimal(0.00)
    #         assert wallet.trading_cash == unit.unit_value
