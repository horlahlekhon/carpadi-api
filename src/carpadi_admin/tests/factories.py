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
)


# faker: Faker =


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
    car_type = CarTypes.MicroCar
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
    brand = factory.SubFactory(BrandFactory)
    name = factory.Faker('word')
    estimated_price = 1000

    class Meta:
        model = SpareParts


class MiscellaneousMaintenanceFactory(factory.django.DjangoModelFactory):
    name = factory.Faker('word')
    estimated_price = 1000
    description = factory.Faker('text')

    class Meta:
        model = MiscellaneousExpenses


class InspectionFactory(factory.django.DjangoModelFactory):
    car = None
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


# class MaintenanceFactory(factory.django.DjangoModelFactory):
#     car =  None
#
#     class Meta:
#         model = CarMaintenance
