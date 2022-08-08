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

from src.carpadi_admin.serializers import CarMaintenanceSerializerAdmin
from src.carpadi_api.serializers import TradeUnitSerializer
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
            merch_ids.append(id1)
            self.seeder.add_entity(
                Wallet,
                1,
                {
                    'merchant': lambda x: CarMerchant.objects.get(pk=id1),
                    'balance': Decimal(10000000.0),
                    'withdrawable_cash': Decimal(10000000.0),
                    'trading_cash': Decimal(0.0),
                    'total_cash': Decimal(0.0),
                },
            )

            self.seeder.execute()
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
        self.seeder.execute()

    def seed_cars(self):
        cost = self.seeder.faker.random_number(digits=4)
        self.seeder.add_entity(
            MiscellaneousExpenses,
            1,
            {
                'estimated_price': cost,
            },
        )
        exp = self.seeder.execute()[MiscellaneousExpenses][0]
        # exp = MiscellaneousExpenses.objects.get(pk=exp)
        vin = self.seeder.faker.random_number(digits=17)
        self.seeder.add_entity(
            Car,
            1,
            {
                'status': CarStates.Inspected if self.admin else CarStates.New,
                'bought_price': Decimal(100000.0),
                'vin': vin,
                'resale_price': None,
                'colour': self.seeder.faker.color_name(),
                'information': self.seed_vehicle_info(vin)
                # 'maintenance_cost': Decimal(cost),
            },
        )
        car = self.seeder.execute()[Car][0]
        self.seed_inspection(car, user=None)
        data = {
            "type": "expense",
            "maintenance": {
                "estimated_price": abs(self.seeder.faker.random_number(digits=4)),
                "name": self.seeder.faker.name(),
                "picture": "https://res.cloudinary.com/balorunduro/image/upload/v1659456477/test/xbwnjjuyazcjybdxpw63.png",
            },
            "car": car,
        }
        ser = CarMaintenanceSerializerAdmin(data=data)
        if ser.is_valid(raise_exception=True):
            ser.save()
        self.seed_assets(car, AssetEntityType.Car)
        return car

    def seed_assets(self, entity, ent_type, count=1):
        # https://picsum.photos/v2/list?page=100&limit=2
        resp = requests.get('https://picsum.photos/v2/list?page=100&limit={}'.format(count))
        data = resp.json()
        urls = [d['download_url'] for d in data]
        car = Car.objects.get(pk=entity)
        Assets.create_many(urls, car, ent_type)

    def seed_trade(self, car, status: TradeStates):
        assert status not in (
            TradeStates.Completed,
            TradeStates.Closed,
            TradeStates.Purchased,
        ), "Invalid status when creating trade"
        assert car.status == CarStates.Inspected, "Invalid car status when creating trade"
        self.seeder.add_entity(
            Trade,
            1,
            {
                'car': car,
                'slots_available': 5,
                'min_sale_price': Decimal(120000.0),
                'max_sale_price': Decimal(200000.0),
                'trade_status': status,
                'date_of_sale': None,
                'bts_time': None,
                'return_on_trade': None,
            },
        )
        return self.seeder.execute()[Trade][0]

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
        car = self.seed_cars()
        car = Car.objects.get(pk=car)
        trade = self.seed_trade(car, TradeStates.Ongoing)
        trade = Trade.objects.get(pk=trade)
        units = self.seed_units(trade, merchants)
        if len(merchants) < trade.slots_available:
            return trade
        trade.trade_status = TradeStates.Completed
        trade.save(update_fields=['trade_status'])
        if should_close:
            trade.close()
        return trade

    @atomic
    def seed(self):
        # wallet_ids, merch_ids = self.seed_merchants()
        if shouldseed == True or self.request is not None:
            self.seed_admin()
            merch_ids = self.seed_merchants()
            self.seed_completed_trade(merch_ids, should_close=True)
            self.seed_completed_trade(merch_ids, should_close=False)
            self.seed_completed_trade(merch_ids[:3])
            self.seed_completed_trade(merch_ids[:2])
            self.seed_settings()
        else:
            print("Skipping database seed")

    def seed_vehicle_info(self, vin):
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
                "vin": vin,
                "engine": "L4, 1.8L; DOHC; 16V",
                "transmission": "STANDARD",
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
        self.seeder.add_entity(
            Settings,
            1,
            {
                "carpadi_trade_rot_percentage": Decimal(10.0),
                "merchant_trade_rot_percentage": Decimal(5.0),
            },
        )
        self.seeder.execute()
