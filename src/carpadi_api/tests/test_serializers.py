# Create your tests here.
import uuid

from django.test import TestCase
from nose.tools import ok_, eq_
from rest_framework.exceptions import NotAcceptable, ErrorDetail

from src.carpadi_api.serializers import TransactionPinSerializers
from src.models.models import UserTypes, User, TransactionPin, TransactionPinStatus
from src.models.serializers import CreateUserSerializer


class TestTransactionPinSerializers(TestCase):
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

    def test_transaction_pin_created_by_merchant(self):
        data = {"device_platform": "ios", "pin": "123451", "device_name": "techno Ex"}
        ser = TransactionPinSerializers(data=data)
        is_valid = ser.is_valid()
        eq_(is_valid, True)
        pin: TransactionPin = ser.save(user=self.user, device_serial_number=str(uuid.uuid4()))
        ok_(pin)
        eq_(pin.pin, data["pin"])

    def test_transaction_pin_creation_rejected_for_too_many_pins(self):
        data = [
            {"device_platform": "ios", "pin": "123451", "device_name": "techno Ex", "device_serial_number": str(uuid.uuid4())},
            {"device_platform": "ios", "pin": "123450", "device_name": "techno Ex", "device_serial_number": str(uuid.uuid4())},
            {
                "device_platform": "android",
                "pin": "123452",
                "device_name": "techno Ex",
                "device_serial_number": str(uuid.uuid4()),
            },
        ]
        ser = TransactionPinSerializers(data=data, many=True)
        eq_(ser.is_valid(), True)
        pin: TransactionPin = ser.save(user=self.user)
        data2 = {"device_platform": "ios", "pin": "123455", "device_name": "techno Ex", "device_serial_number": str(uuid.uuid4())}
        ser = TransactionPinSerializers(data=data2)
        try:
            ser.is_valid(raise_exception=True)
        except Exception as reason:
            eq_(type(reason), NotAcceptable)

    def test_duplicate_pin_and_imei_combo_rejected(self):
        data2 = {"device_platform": "ios", "pin": "123455", "device_name": "techno Ex", "device_serial_number": str(uuid.uuid4())}
        ser = TransactionPinSerializers(data=data2)
        eq_(ser.is_valid(), True)
        ser.save(user=self.user)
        pins = self.user.transaction_pins.filter(status=TransactionPinStatus.Active)
        data3 = data2
        ser = TransactionPinSerializers(data=data3)
        eq_(ser.is_valid(), False)
        errors = ser.errors
        eq_(errors["non_field_errors"][0], "The fields device_serial_number, pin must make a unique set.")

    def test_duplicate_pin_rejected(self):
        data2 = {"device_platform": "ios", "pin": "123455", "device_name": "techno Ex", "device_serial_number": str(uuid.uuid4())}
        ser = TransactionPinSerializers(data=data2)
        eq_(ser.is_valid(), True)
        ser.save(user=self.user)
        pins = self.user.transaction_pins.filter(status=TransactionPinStatus.Active)
        data3 = data2
        data3["device_serial_number"] = str(uuid.uuid4())
        ser = TransactionPinSerializers(data=data3)
        is_valid = ser.is_valid()
        eq_(is_valid, True)
        try:
            ser.save(user=self.user)
        except Exception as reason:
            eq_(reason.args[0]["error"], 'Pin already belong to one of your devices, please use another one')
