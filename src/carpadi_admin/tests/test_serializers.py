import uuid
from decimal import Decimal

from rest_framework.exceptions import ValidationError
from django.test import TestCase
from nose.tools import *
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from src.carpadi_admin.serializers import (
    CarSerializer,
    CarMaintenanceSerializerAdmin,
    TradeSerializerAdmin,
    CarDocumentsSerializer,
)
from src.carpadi_admin.tests import BaseTest
from src.carpadi_admin.tests.factories import VehicleFactory, InspectionFactory, SparePartFactory, CarDocumentsFactory
from src.models.models import (
    UserTypes,
    User,
    VehicleInfo,
    Car,
    CarStates,
    CarMaintenance,
    InspectionStatus,
    InspectionVerdict,
    Settings,
    CarDocumentsTypes,
    Assets,
    AssetEntityType,
    CarDocuments,
)
from src.models.serializers import CreateUserSerializer
from src.models.test.factories import WalletFactory


class TestCarSerializer(TestCase):
    user_data = None
    admin = None
    vehicle = None

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
        cls.vehicle: VehicleInfo = VehicleFactory()

    # def setUp(self) -> None:
    #
    #     print(self.vehicle)

    def test_create_car_given_valid_date(self):
        payload = dict(information=str(self.vehicle.id), vin=self.vehicle.vin, colour="pink", bought_price=Decimal("100000"))
        ser = CarSerializer(data=payload)
        is_valid = ser.is_valid()
        eq_(is_valid, True)
        ser.save()
        car = Car.objects.all()
        eq_(len(car), 1)

    def test_car_creation_fails_on_invalid_vin(self):
        payload = dict(vin=str(uuid.uuid4())[:17], colour="pink", bought_price=Decimal("100000"))
        ser = CarSerializer(data=payload)
        is_valid = ser.is_valid()
        eq_(is_valid, False)
        errors = ser.errors
        assert len(errors) > 0
        assert "vin" in errors.keys()
        assert errors["vin"][0] == "Please validate the vin before attempting to create a car with it"

    def test_cannot_create_car_with_existing_car_vin(self):
        payload = dict(vin=self.vehicle.vin, colour="pink", bought_price=Decimal("100000"))
        ser = CarSerializer(data=payload)
        is_valid = ser.is_valid()
        eq_(is_valid, True)
        ser.save()
        payload2 = dict(vin=self.vehicle.vin, colour="pink", bought_price=Decimal("100000"))
        ser2 = CarSerializer(data=payload2)
        is_valid = ser2.is_valid()
        eq_(is_valid, False)
        errors = ser2.errors
        assert len(errors) > 0
        assert "vin" in errors.keys()
        assert errors["vin"][0] == f"Car with the vin number {self.vehicle.vin} exists before"

    def test_reject_update_car_status_to_available_without_inspection(self):
        from rest_framework import serializers

        payload = dict(vin=self.vehicle.vin, colour="pink", bought_price=Decimal("100000"))
        ser = CarSerializer(data=payload)
        is_valid = ser.is_valid()
        eq_(is_valid, True)
        car = ser.save()
        car.refresh_from_db()
        upd = dict(status=CarStates.Available)
        ser2 = CarSerializer(data=upd, instance=car, partial=True)
        try:
            ser2.is_valid(raise_exception=True)
        except Exception as reason:
            eq_(type(reason), serializers.ValidationError)
            eq_(reason.args[0]["status"][0], "Please create inspection for the car first.")

    def reject_update_for_inspected_status_inspected(self):
        from rest_framework import serializers

        payload = dict(vin=self.vehicle.vin, colour="pink", bought_price=Decimal("100000"))
        ser = CarSerializer(data=payload)
        is_valid = ser.is_valid()
        eq_(is_valid, True)
        car = ser.save()
        car.refresh_from_db()
        upd = dict(status=CarStates.Inspected)
        ser2 = CarSerializer(data=upd, instance=car, partial=True)
        try:
            ser2.is_valid(raise_exception=True)
        except Exception as reason:
            eq_(type(reason), serializers.ValidationError)
            eq_(reason.args[0]["status"][0], "You are not allowed to set the inspection status directly")

    def test_update_pass_for_car_with_inspection(self):
        payload = dict(vin=self.vehicle.vin, colour="pink", bought_price=Decimal("100000"))
        ser = CarSerializer(data=payload)
        is_valid = ser.is_valid()
        eq_(is_valid, True)
        car = ser.save()
        inspection = InspectionFactory(car=car, inspector=self.admin, inspection_assignor=self.admin)
        upd = dict(status=CarStates.Available)
        ser2 = CarSerializer(data=upd, instance=car, partial=True)
        isvalid = ser2.is_valid()
        # errors = ser2.errors
        # eq_(isvalid, True)
        # car2 = ser2.save()

    def test_total_cost_of_car_calculated_correctly(self):
        payload = dict(vin=self.vehicle.vin, colour="pink", bought_price=Decimal("100000"))
        ser = CarSerializer(data=payload)
        is_valid = ser.is_valid()
        eq_(is_valid, True)
        car = ser.save()
        inspection = InspectionFactory(car=car, inspector=self.admin, inspection_assignor=self.admin)
        maintenance = [
            {
                "type": "spare_part",
                "maintenance": {
                    "estimated_price": 1000,
                    "name": "lexus Brake pads",
                    "picture": "https://res.cloudinary.com/balorunduro/image/upload/v1659456477/test/xbwnjjuyazcjybdxpw63.png",
                },
                "car": str(car.id),
            },
            {
                "type": "spare_part",
                "maintenance": {
                    "estimated_price": 1000,
                    "name": "lexus Brake pads",
                    "picture": "https://res.cloudinary.com/balorunduro/image/upload/v1659456477/test/xbwnjjuyazcjybdxpw63.png",
                },
                "car": str(car.id),
            },
        ]
        maintenance_ser = CarMaintenanceSerializerAdmin(data=maintenance, many=True)
        is_valid = maintenance_ser.is_valid()
        eq_(is_valid, True)
        maint = maintenance_ser.save()
        car.refresh_from_db()
        data = CarSerializer(instance=car).data
        eq_(data["maintenance_cost"], Decimal(2000.0))
        eq_(data["total_cost"], car.bought_price + Decimal(2000.0))


class CarMaintenanceSerializerTest(TestCase):
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

        cls.vehicle: VehicleInfo = VehicleFactory()
        payload = dict(vin=cls.vehicle.vin, colour="pink", bought_price=Decimal("100000"))
        ser = CarSerializer(data=payload)
        is_valid = ser.is_valid()
        eq_(is_valid, True)
        cls.car = ser.save()

    def test_car_maintenance_created_successfully(self):
        var = {
            "type": "spare_part",
            "maintenance": {
                "estimated_price": 1000,
                "name": "lexus Brake pads",
                "picture": "https://res.cloudinary.com/balorunduro/image/upload/v1659456477/test/xbwnjjuyazcjybdxpw63.png",
            },
            "car": str(self.car.id),
        }
        car_maintenance_ser = CarMaintenanceSerializerAdmin(data=var)
        is_valid = car_maintenance_ser.is_valid()
        eq_(is_valid, True)
        maint: CarMaintenance = car_maintenance_ser.save()
        ok_(maint)
        eq_(maint.cost(), var["maintenance"]["estimated_price"])
        eq_(maint.type, var["type"])

    def test_car_maintenance_with_invalid_data(self):
        var = {
            "maintenance": {
                "name": "lexus Brake pads",
                "picture": "https://res.cloudinary.com/balorunduro/image/upload/v1659456477/test/xbwnjjuyazcjybdxpw63.png",
            },
            "car": str(self.car.id),
        }
        car_maintenance_ser = CarMaintenanceSerializerAdmin(data=var)
        is_valid = car_maintenance_ser.is_valid()
        eq_(is_valid, False)
        eq_(car_maintenance_ser.errors["type"][0], "This field is required.")

    @raises(ValidationError)
    def test_serializer_type_validate_accordingly(self):
        var = {
            "type": "spare_part",
            "maintenance": {
                "name": "lexus Brake pads",
                "picture": "https://res.cloudinary.com/balorunduro/image/upload/v1659456477/test/xbwnjjuyazcjybdxpw63.png",
            },
            "car": str(self.car.id),
        }
        car_maintenance_ser = CarMaintenanceSerializerAdmin(data=var)
        is_valid = car_maintenance_ser.is_valid()
        eq_(is_valid, True)
        maint = car_maintenance_ser.save()
        ok_(maint)


class TestTradeSerializer(BaseTest):
    @classmethod
    def setUpTestData(cls):
        cls.set = Settings.objects.create(
            merchant_trade_rot_percentage=Decimal(5.00), carpadi_commision=Decimal(50.00), bonus_percentage=Decimal(50.00)
        )

    def setUp(self) -> None:
        super(TestTradeSerializer, self).setUp()
        self.wallets = WalletFactory.create_batch(size=5)
        self.inspection = InspectionFactory(
            inspector=self.admin,
            inspection_assignor=self.admin,
            inspection_verdict=InspectionVerdict.Good,
            status=InspectionStatus.Completed,
        )
        self.spare_part = SparePartFactory()
        self.car = self.inspection.car

    def prepare_car(self, bought=Decimal(0.0), resale=Decimal(0.0), inspection=True, docs=True):
        self.car.bought_price = Decimal(bought or 100000)
        self.car.resale_price = Decimal(resale or 150000)
        self.car.save()
        if inspection:
            self.car.update_on_inspection_changes(self.inspection)
        self.maintenance = CarMaintenance.objects.create(maintenance=self.spare_part, car=self.car)
        if docs:
            for i in CarDocumentsTypes.choices:
                data = dict(
                    car=self.car.id,
                    is_verified=True,
                    document_type=i[0],
                    name=i[0],
                    asset="https://picsum.photos/id/116/3504/2336",
                )
                ser = CarDocumentsSerializer(data=data)
                ser.is_valid(raise_exception=True)
                ser.save()

    def test_trade_created_successfully(self):
        self.prepare_car(resale=Decimal(0.0))
        data = dict(car=self.car.id, slots_available=5)
        ser = TradeSerializerAdmin(data=data)
        valid = ser.is_valid()
        assert valid
        trade = ser.save()
        read_ser = TradeSerializerAdmin(instance=trade).data
        assert read_ser["remaining_slots"] == data["slots_available"]
        assert read_ser["car"]["bought_price"] == self.car.bought_price
        assert read_ser["car"]["maintenance_cost"] == self.car.maintenance_cost_calc()
        assert read_ser["return_on_trade_per_unit"] == trade.return_on_trade_per_slot
        assert read_ser["trade_margin"] == trade.margin_calc()
        assert read_ser["return_on_trade_percentage"] == trade.return_on_trade_calc_percent()
        assert read_ser["sold_slots_price"] == trade.sold_slots_price()

    def test_trade_creation_rejected_if_docs_not_complete(self):
        self.prepare_car(resale=Decimal(0.0), inspection=True, docs=False)
        data = dict(car=self.car.id, slots_available=5)
        ser = TradeSerializerAdmin(data=data)
        valid = ser.is_valid()
        try:
            ser.save()
        except Exception as reason:
            assert type(reason) == ValidationError
            assert (
                reason.args[0]
                == "Some documents have either not being uploaded or not yet verified, please contact admin', code='invalid'"
            )
