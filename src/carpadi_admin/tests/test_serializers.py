import uuid
from decimal import Decimal

from django.test import TestCase
from nose.tools import ok_, eq_

from src.carpadi_admin.serializers import CarSerializer
from src.carpadi_admin.tests.factories import VehicleFactory, InspectionFactory
from src.models.models import UserTypes, User, VehicleInfo, Car, CarStates
from src.models.serializers import CreateUserSerializer


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
        errors = ser2.errors
        eq_(isvalid, True)
        car2 = ser2.save()

    # def test_total_cost_of_car_calculated_correctly(self):
    #     payload = dict(vin=self.vehicle.vin,
    #                    colour="pink", bought_price=Decimal("100000"))
    #     ser = CarSerializer(data=payload)
    #     is_valid = ser.is_valid()
    #     eq_(is_valid, True)
    #     car = ser.save()
    #     inspection = InspectionFactory(car=car, inspector=self.admin, inspection_assignor=self.admin)
    #     upd = dict(resale_price=CarStates.Available)
    #     ser2 = CarSerializer(data=upd, instance=car, partial=True)
    #     isvalid = ser2.is_valid()
    #     errors = ser2.errors
    #     eq_(isvalid, True)
    #     car2 = ser2.save()
