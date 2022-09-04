from decimal import Decimal

import faker_vehicle
from django.test import TestCase
from faker import factory

from src.carpadi_admin.tests import BaseTest
from src.carpadi_admin.tests.factories import VehicleFactory, CarFactory, InspectionFactory, SparePartFactory, TradeFactory
from src.models.models import (
    User,
    UserTypes,
    InspectionVerdict,
    InspectionStatus,
    CarMaintenance,
    CarStates,
    Settings,
    TradeStates,
)
from src.models.test.factories import UserFactory, WalletFactory


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
        self.wallets = WalletFactory.create_batch(size=5)
        self.inspection = InspectionFactory(
            inspector=self.admin,
            inspection_assignor=self.admin,
            inspection_verdict=InspectionVerdict.Good,
            status=InspectionStatus.Completed,
        )
        self.spare_part = SparePartFactory()
        self.car = self.inspection.car

    def prepare_car(self, bought=None, resale=None):
        self.car.update_on_inspection_changes(self.inspection)
        self.maintenance = CarMaintenance.objects.create(maintenance=self.spare_part, car=self.car)
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
        assert trade.return_on_trade_calc_percent() == rot / Decimal(150000) * 100
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
        maintenance = Decimal(2000)
        resale_price = Decimal(105100.0) + maintenance
        self.prepare_car(resale=resale_price)
        trade = TradeFactory(car=self.car, trade_status=TradeStates.Completed)
        rot = (bought_price + maintenance) * Decimal(5.00) / 100
        assert trade.return_on_trade_calc() == rot
        assert trade.return_on_trade_per_slot == rot / 5
        assert trade.carpadi_commission_calc() == rot / 2
        assert trade.margin_calc() == (resale_price - bought_price) - maintenance
        assert trade.return_on_trade_calc_percent() == rot / resale_price * 100
        assert trade.calculate_price_per_slot() == (bought_price + maintenance) / 5
        bonus = Decimal(0)
        assert trade.bonus_calc() == bonus
        traders_bonus = bonus * Decimal(50.00) / 100
        assert trade.traders_bonus() == traders_bonus
        assert trade.carpadi_bonus_calc() == bonus - traders_bonus
        assert trade.carpadi_rot_calc() == (bonus - traders_bonus) + rot / 2


    def test_create_trade_with_loss(self):
        """
                bought_price = Decimal(100000)
                resale_price = Decimal(50000.0)
                maintenance = Decimal(2000)
                bonus_percentage=Decimal(50.00)
            """
        bought_price = Decimal(100000)
        maintenance = Decimal(2000)
        resale_price = Decimal(50000.0) + maintenance
        self.prepare_car(resale=resale_price)
        trade = TradeFactory(car=self.car, trade_status=TradeStates.Completed)
        rot = (bought_price + maintenance) * Decimal(5.00) / 100
        assert trade.return_on_trade_calc() == rot
        assert trade.return_on_trade_per_slot == rot / 5
        assert trade.carpadi_commission_calc() == rot / 2
        assert trade.margin_calc() == (resale_price - bought_price) - maintenance
        assert trade.return_on_trade_calc_percent() == rot / resale_price * 100
        assert trade.calculate_price_per_slot() == (bought_price + maintenance) / 5
        bonus = Decimal(0)
        assert trade.bonus_calc() == bonus
        traders_bonus = bonus * Decimal(50.00) / 100
        assert trade.traders_bonus() == traders_bonus
        assert trade.carpadi_bonus_calc() == bonus - traders_bonus
        assert trade.carpadi_rot_calc() == Decimal(0)
        assert trade.deficit_balance() == abs(resale_price - (bought_price + maintenance))

    def test_trade_with_units(self):
        units = []
