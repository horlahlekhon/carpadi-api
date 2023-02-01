import uuid
from decimal import Decimal

import factory
from factory import Faker
from faker_vehicle import VehicleProvider

from src.models.models import (
    VehicleInfo,
    CarTransmissionTypes,
    CarTypes,
    FuelTypes,
    CarBrand,
    CarMaintenance,
    SpareParts,
    MiscellaneousExpenses,
    Inspections,
    InspectionVerdict,
    InspectionStatus,
    Car,
    TradeUnit,
    UserTypes,
    Transaction,
    Trade,
    TradeStates,
    CarDocuments,
    Assets,
)

# faker: Faker =
from src.models.test.factories import UserFactory


class BrandFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('word')
    model = factory.Faker('word')
    year = factory.Faker('year')

    class Meta:
        model = CarBrand


class VehicleFactory(factory.django.DjangoModelFactory):
    vin = factory.Faker('isbn13')
    engine = factory.Faker('text')
    transmission = CarTransmissionTypes.Automatic
    car_type = CarTypes.MINIVAN
    fuel_type = FuelTypes.LPG
    mileage = factory.Faker('random_int')
    age = factory.Faker('random_int')
    description = factory.Faker('text')
    manufacturer = "Toyota"
    brand = factory.SubFactory(BrandFactory)

    class Meta:
        model = VehicleInfo
        # django_get_or_create = ('vin',)


class SparePartFactory(factory.django.DjangoModelFactory):
    car_brand = factory.SubFactory(BrandFactory)
    name = factory.Faker('word')
    estimated_price = Decimal(1000.0)
    repair_cost = Decimal(1000.0)

    class Meta:
        model = SpareParts


class MiscellaneousMaintenanceFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('word')
    estimated_price = 1000
    description = factory.Faker('text')

    class Meta:
        model = MiscellaneousExpenses


class CarFactory(factory.django.DjangoModelFactory):
    information = factory.SubFactory(VehicleFactory)
    colour = "black"
    description = factory.Faker('text')
    name = factory.Faker('word')
    licence_plate = factory.Sequence(lambda n: f'KJA-45KJ{n}')

    class Meta:
        model = Car


class InspectionFactory(factory.django.DjangoModelFactory):
    car = factory.SubFactory(CarFactory)
    inspector = None
    inspection_assignor = None
    inspection_verdict = InspectionVerdict.Bad
    status = (InspectionStatus.Completed.value,)
    owners_name = factory.Faker('name')
    inspection_date = factory.Faker('date')
    owners_phone = "+238198998344"
    owners_review = factory.Faker('word')
    address = factory.Faker('address')

    class Meta:
        model = Inspections


class TransactionsFactory(factory.django.DjangoModelFactory):
    amount = None
    wallet = None
    transaction_type = None
    transaction_reference = factory.LazyFunction(lambda: f'CP-{str(uuid.uuid4()).upper()}')
    transaction_kind = None
    transaction_status = None

    class Meta:
        model = Transaction


class TradeFactory(factory.django.DjangoModelFactory):
    car = None
    slots_available = 5
    trade_status = TradeStates.Ongoing

    class Meta:
        model = Trade


class TradeUnitFactory(factory.django.DjangoModelFactory):
    trade = None
    merchant = None
    slots_quantity = 1
    buy_transaction = None

    class Meta:
        model = TradeUnit


# class MaintenanceFactory(factory.django.DjangoModelFactory):
#     car =  None
#
#     class Meta:
#         model = CarMaintenance


class AssetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Assets


class CarDocumentsFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CarDocuments

    car = None
    is_verified = True
    name = factory.Faker('name')
    asset = "https://www.google.com"
    description = owners_review = factory.Faker('word')
    document_type = None
