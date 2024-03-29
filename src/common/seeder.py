import asyncio
import uuid
from asyncio import AbstractEventLoop
from decimal import Decimal
from typing import Optional

import requests
from django.db.transaction import atomic
from django_seed import Seed
from faker_vehicle import VehicleProvider
from rest_framework import status

from src.carpadi_admin.serializers import CarMaintenanceSerializerAdmin, TradeSerializerAdmin, CarDocumentsSerializer
from src.carpadi_api.serializers import TradeUnitSerializer
from src.carpadi_market.serializers import CarProductSerializer
from src.config import common
from src.models.models import (
    CarMerchant,
    User,
    UserTypes,
    Wallet,
    Car,
    MiscellaneousExpenses,
    CarStates,
    Trade,
    TradeStates,
    VehicleInfo,
    FuelTypes,
    Assets,
    AssetEntityType,
    Banks,
    CarBrand,
    Inspections,
    InspectionStatus,
    Settings,
    CarProduct,
    CarDocumentsTypes,
    CarTransmissionTypes,
)

PASSWORD = "pbkdf2_sha256$260000$dl1wNc1JopbXE6JndG5I51$qJCq6RPPESnd1pMEpLDuJJ00PVbKK4Nu2YLpiK3OliA="

shouldseed = True


class PadiSeeder:
    seeder = Seed.seeder()

    def __init__(self, command=None, request=None):
        self.request = request
        self.admin = None
        self.command = command
        self.seeder.faker.add_provider(VehicleProvider)

    def seed_merchants(self):
        usernames = {'gsherman', 'brettmyers', 'curtishanson', 'russell48', "salk"}
        in_db = User.objects.filter(username__in=usernames).values_list('username', flat=True)

        user_ids = []
        if missing := usernames.difference(set(in_db)):
            self.seeder.add_entity(
                User,
                len(missing),
                {
                    'username': lambda x: missing.pop(),
                    'user_type': UserTypes.CarMerchant,
                    'password': PASSWORD,
                    'is_active': True,
                    'is_staff': False,
                    'is_superuser': False,
                },
            )

            user_ids = self.seeder.execute()[User]
        print(f"Seeded {user_ids} users")
        merch_ids = []
        for idx in user_ids:
            self.seeder.add_entity(
                CarMerchant,
                1,
                {'user': lambda x: User.objects.get(pk=idx), 'bvn': lambda x: f"{self.seeder.faker.random_number(digits=10)}"},
            )

            id1 = self.seeder.execute()[CarMerchant][0]
            wallet = Wallet.objects.get(merchant_id=id1)
            wallet.balance = Decimal(1000000)
            wallet.total_cash = Decimal(1000000)
            wallet.withdrawable_cash = Decimal(1000000)
            wallet.save(update_fields=["balance", "total_cash", "withdrawable_cash"])
            merch_ids.append(id1)
        merch_ids = CarMerchant.objects.filter(user__username__in=usernames)
        return merch_ids

    def seed_admin(self):
        if admin := User.objects.filter(user_type=UserTypes.Admin, is_active=True, is_staff=True, username='lekan').first():
            self.admin = admin
            return [admin.id]
        else:
            self.seeder.add_entity(
                User,
                1,
                {
                    "is_staff": True,
                    "is_superuser": True,
                    "is_active": True,
                    'username': 'lekan',
                    'user_type': UserTypes.Admin,
                    'password': PASSWORD,
                },
            )

            user_ids = self.seeder.execute()[User]
            print(f"Seeded {user_ids[0]} users")
            self.admin = User.objects.get(pk=user_ids[0])
            return user_ids

    def seed_inspection(self, car: str, user: Optional[User]):
        assert not user or user.is_staff, "User doe inspection has to be a staff"
        self.seeder.add_entity(
            Inspections,
            1,
            {
                "status": InspectionStatus.Ongoing,
                "inspector": user or self.admin,
                "inspection_assignor": self.admin,
                "car": Car.objects.get(pk=car),
            },
        )
        ins = self.seeder.execute()[Inspections][0]
        return Inspections.objects.get(id=ins)

    def seed_cars(self, count=1):
        self.seeder.add_entity(
            Car,
            count,
            {
                'status': CarStates.Inspected if self.admin else CarStates.New,
                'bought_price': Decimal(100_000.0),
                'vin': lambda x: self.seeder.faker.random_number(digits=17),
                'resale_price': None,
                'colour': self.seeder.faker.color_name(),
                'information': lambda x: self.seed_vehicle_info(),
                "cost_of_repairs": Decimal(0.00),
                "margin": Decimal(0.00),
                "total_cost": Decimal(0.00)
                # 'maintenance_cost': Decimal(cost),
            },
        )
        cars = self.seeder.execute()[Car]
        for car in cars:
            car_obj = Car.objects.get(id=car)
            car_obj.vin = car_obj.information.vin
            car_obj.save(update_fields=["vin"])
            inspection = self.seed_inspection(car, user=None)
            data = {
                "type": "expense",
                "maintenance": {
                    "estimated_price": Decimal(5000.00),
                    "name": self.seeder.faker.name(),
                    "picture": "https://res.cloudinary.com/balorunduro/image/upload/v1659456477/test/xbwnjjuyazcjybdxpw63.png",
                },
                "car": car,
            }
            ser = CarMaintenanceSerializerAdmin(data=data)
            if ser.is_valid(raise_exception=True):
                ser.save()
            inspection.status = InspectionStatus.Completed
            inspection.save(update_fields=["status"])
            self.seed_car_assets(car, AssetEntityType.Car)
            self.seed_car_documents(car)
        return cars

    def seed_car_documents(self, car):
        data = [
            dict(
                car=str(car),
                name=str(name)[:50],
                document_type=value,
                asset="https://d16encqm9nbktq.cloudfront.net/bmw.jpg",
                is_verified=True,
            )
            for value, name in CarDocumentsTypes.choices
        ]
        doc_ser = CarDocumentsSerializer(data=data, many=True)
        doc_ser.is_valid(raise_exception=True)
        doc_ser.save()

    def seed_car_assets(self, entity, ent_type, count=1):
        # https://picsum.photos/v2/list?page=100&limit=2
        urls = self.get_asset(1)
        car = Car.objects.get(pk=entity)
        Assets.create_many(urls, car, ent_type)

    @classmethod
    def get_asset(cls, count=1):
        # resp = requests.get(f'https://picsum.photos/v2/list?page=100&limit={count}')
        # data = resp.json()
        return ['https://random.imagecdn.app/500/150' for _ in range(count)]

    def seed_trade(self, car, status: TradeStates):
        assert status not in (
            TradeStates.Completed,
            TradeStates.Closed,
            TradeStates.Purchased,
        ), "Invalid status when creating trade"
        assert car.status in (CarStates.Available, CarStates.Inspected), f"Invalid car status when creating trade: {car.status}"
        self.seeder.add_entity(
            Trade,
            1,
            {
                'car': car,
                'slots_available': 5,
                'min_sale_price': Decimal(120000.0),
                'trade_status': status,
                'date_of_sale': None,
                'bts_time': None,
                'return_on_trade': None,
                'carpadi_bonus': Decimal(0.00),
                'total_carpadi_rot': Decimal(0.00),
                'traders_bonus_per_slot': Decimal(0.00),
                'carpadi_commission': Decimal(0.00),
            },
        )
        trade = self.seeder.execute()[Trade][0]
        car.status = CarStates.OngoingTrade
        car.save(update_fields=['status'])
        return trade

    def seed_units(self, trade, merchants):
        units = []
        for merchant in merchants:
            data = dict(trade=trade.id, merchant=merchant.id, slots_quantity=1)
            ser = TradeUnitSerializer(data=data)
            ser.context["merchant"] = merchant
            ser.is_valid(raise_exception=True)
            unit = ser.save()
            units.append(unit)
        return units

    def seed_completed_trade(self, merchants, should_close=False):
        car = self.seed_cars()[0]
        car = Car.objects.get(pk=car)
        trade = self.seed_trade(car, TradeStates.Ongoing)
        trade = Trade.objects.get(pk=trade)
        units = self.seed_units(trade, merchants)
        if len(merchants) < trade.slots_available:
            return trade
        car.resale_price = car.bought_price + car.maintenance_cost_calc() + Decimal(5000)
        car.save(update_fields=["resale_price"])
        trade.refresh_from_db()
        trade_serializer = TradeSerializerAdmin(data=dict(trade_status=TradeStates.Completed.value), instance=trade, partial=True)
        trade_serializer.is_valid(raise_exception=True)
        trade = trade_serializer.save()
        if should_close:
            trade.close()
        return trade

    @atomic
    def seed(self):
        # wallet_ids, merch_ids = self.seed_merchants()
        if shouldseed or self.request is not None:
            self.seed_settings()
            self.seed_admin()
            merch_ids = self.seed_merchants()
            t1 = self.seed_completed_trade(merch_ids, should_close=True)
            t2 = self.seed_completed_trade(merch_ids, should_close=False)
            t3 = self.seed_completed_trade(merch_ids[:3])
            t4 = self.seed_completed_trade(merch_ids[:2])
            self.seed_car_product(cars=[t4.car_id, t3.car_id, t2.car_id, t1.car_id])
            self.seed_cars(count=5)
            print("seeding completed successfully!")
        else:
            print("Skipping database seed")

    def seed_vehicle_info(self, vin=None):
        vehicle = self.seeder.faker.vehicle_object()
        self.seeder.add_entity(
            CarBrand,
            1,
            {
                "year": vehicle["Year"],
                "model": vehicle['Model'],
                "name": vehicle['Make'],
            },
        )
        brand = self.seeder.execute()[CarBrand][0]
        self.seeder.add_entity(
            VehicleInfo,
            1,
            {
                "id": uuid.uuid4(),
                "vin": lambda x: self.seeder.faker.random_number(digits=17),
                "engine": "L4, 1.8L; DOHC; 16V",
                "transmission": CarTransmissionTypes.Automatic.value,
                "car_type": vehicle["Category"],
                "fuel_type": FuelTypes.Petrol,
                "description": None,
                "trim": "BASE",
                "manufacturer": vehicle['Make'],
                "brand": CarBrand.objects.get(pk=brand),
            },
        )
        ret = self.seeder.execute()[VehicleInfo][0]
        return VehicleInfo.objects.get(id=ret)

    async def seed_async(self, loop: AbstractEventLoop):
        self.seed()
        await asyncio.sleep(20)
        loop.stop()

    def seed_banks(self):
        headers = dict(Authorization=f"Bearer {common.FLW_SECRET_KEY}")
        request = requests.get("https://api.flutterwave.com/v3/banks/ng", headers=headers)
        response = request.json()
        if request.status_code == status.HTTP_200_OK and response.get("status") == "success":
            banks = response.get("data")
            if Banks.objects.count() < len(banks):
                bank_list = []
                for bank in banks:
                    if Banks.objects.filter(bank_name=bank["name"], bank_code=bank["code"]).count() < 1:
                        b = Banks(id=uuid.uuid4(), bank_name=bank["name"], bank_code=bank["code"], bank_id=bank["id"])
                        bank_list.append(b)
                if bank_list:
                    resp = Banks.objects.bulk_create(bank_list)
                    print(f"seeded {len(resp)} banks to db...moving on without vawulence!!")
                else:
                    print("This is weird!! an we get a physician here abeg!!")
            else:
                print("Banks already seeded in the database.... and am not even cap'ng!!")
        else:
            print(f"we couldn't get banks list from the API... due to {response}")

    def seed_settings(self):
        Settings.objects.create(
            merchant_trade_rot_percentage=Decimal(5.00), carpadi_commision=Decimal(50.00), bonus_percentage=Decimal(50.00)
        )

    def get_pictures(self, count):
        # resp = requests.get(f'https://picsum.photos/v2/list?page=100&limit={count}')
        # data = resp.json()
        return ["https://d16encqm9nbktq.cloudfront.net/bmw.jpg" for _ in range(count)]

    def seed_car_product(self, cars):
        products = []
        cars = Car.objects.filter(product=None, id__in=cars)
        for car in cars:
            if car.trade:
                product = {
                    "car": str(car.id),
                    "selling_price": car.bought_price + car.maintenance_cost_calc(),
                    "images": [i.asset for i in car.pictures.all()],
                    "features": [
                        {"name": self.seeder.faker.name(), "images": self.get_pictures(2)},
                        {"name": self.seeder.faker.name(), "images": self.get_pictures(2)},
                    ],
                }
                products.append(product)
        car_product_serializer = CarProductSerializer(data=products, many=True)
        car_product_serializer.is_valid(raise_exception=True)
        car_product_serializer.save()

    # def seed_car_purchase(self, count=100):
    #     for i in count:
    #         vin = self.seed_vehicle_info()
    #         license = f"KJA-{self.seeder.faker.random_number(digits=3)}AA"
    #         data = dict(
    #             vin=vin.id, licence_plate=license, registeration_state="Lagos",
    #             current_usage_timeframe_by_user=self.seeder.faker.random_number(digits=2),
    #             mileage=self.seeder.faker.random_number(digits=5),
    #             count_of_previous_users=self.seeder.faker.random_number(digits=1),
    #             custom_papers_availability=True, car_condition="good",
    #             note="Good car", contact_preference="phone", inspection_location="Ikeja",
    #             is_negotiable=True, price=abs(self.seeder.faker.random_number(digits=6)),
    #             user=dict(first_name=self.seeder.faker.name(), last_name=self.seeder.faker.name(),
    #                       email=self.seeder.faker.email(), phone=self.seeder.faker.phone())
    #         )
