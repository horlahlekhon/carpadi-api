import asyncio
from asyncio import AbstractEventLoop
from decimal import Decimal
import requests
from django_seed import Seed
from faker_vehicle import VehicleProvider
from src.carpadi_admin.serializers import CarMaintenanceSerializerAdmin
from src.carpadi_api.serializers import TradeUnitSerializer
from src.models.models import (
    CarMerchant,
    User,
    UserTypes,
    Wallet,
    Car,
    CarBrand,
    CarMaintenance,
    MiscellaneousExpenses,
    CarMaintenanceTypes,
    CarStates,
    Trade,
    TradeStates,
    TradeUnit,
    VehicleInfo,
    FuelTypes, Assets, AssetEntityType
)
from django.db.transaction import atomic

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
        missing = usernames.difference(set(in_db))
        user_ids = []
        if len(missing) > 0:
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
                {
                    'user': lambda x: User.objects.get(pk=idx),
                    'bvn': lambda x: f"{self.seeder.faker.random_number(digits=10)}",
                },
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
            self.seeder.execute()  # [Wallet][0]
        merch_ids = CarMerchant.objects.filter(user__username__in=usernames)
        return merch_ids

    def seed_admin(self):
        admin = User.objects.filter(user_type=UserTypes.Admin, is_active=True, is_staff=True, username='lekan').first()
        if not admin:
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
        else:
            self.admin = admin
            return [admin.id]

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
                'car_inspector': self.admin,
                'offering_price': Decimal(100000.0),
                'inspection_report': 'good' if self.admin else None,
                'vin': vin,
                'resale_price': None,
                'colour': self.seeder.faker.color_name(),
                'information': self.seed_vehicle_info(vin)
                # 'maintenance_cost': Decimal(cost),
            },
        )
        car = self.seeder.execute()[Car][0]
        data = {
            "type": "expense",
            "cost": abs(self.seeder.faker.random_number(digits=4)),
            "description": self.seeder.faker.sentence(),
            "name": self.seeder.faker.name(),
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
        trade = self.seeder.execute()[Trade][0]
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
        else:
            print("Skipping database seed")

    def seed_vehicle_info(self, vin):
        vehicle = self.seeder.faker.vehicle_object()
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
                "year": vehicle["Year"],
                "model": vehicle['Model'],
                "manufacturer": vehicle['Make'],
                "make": vehicle['Make'],
            },
        )
        ret = self.seeder.execute()[VehicleInfo][0]
        return VehicleInfo.objects.get(id=ret)

    async def seed_async(self, loop: AbstractEventLoop):
        self.seed()
        await asyncio.sleep(20)
        loop.stop()
