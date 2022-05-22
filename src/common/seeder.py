from decimal import Decimal

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
    TradeUnit, VehicleInfo, FuelTypes,
)
from django.db.transaction import atomic

PASSWORD = "pbkdf2_sha256$260000$dl1wNc1JopbXE6JndG5I51$qJCq6RPPESnd1pMEpLDuJJ00PVbKK4Nu2YLpiK3OliA="


class PadiSeeder:
    seeder = Seed.seeder()


    def __init__(self, command):
        self.admin = None
        self.command = command
        self.seeder.faker.add_provider(VehicleProvider)

    def seed_merchants(self, count=1):
        self.seeder.add_entity(
            User,
            count,
            {
                "is_staff": False,
                "is_superuser": False,
                "is_active": True,
                'user_type': UserTypes.CarMerchant,
                'password': PASSWORD,
            },
        )
        user_ids = self.seeder.execute()[User]
        self.command.stdout.write(self.command.style.SUCCESS(f"Seeded {user_ids[1]} users"))
        merch_ids = []
        wallet_ids = []
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
            # self.command.stdout.write(self.command.style.SUCCESS(f"Seeded {len(merch_ids)} merchants"))
            self.seeder.add_entity(
                Wallet,
                1,
                {
                    'merchant': lambda x: CarMerchant.objects.get(pk=id1),
                    'balance': Decimal(100000.0),
                    'withdrawable_cash': Decimal(100000.0),
                    'trading_cash': Decimal(0.0),
                    'total_cash': Decimal(0.0),
                },
            )
            wallet_id = self.seeder.execute()[Wallet][0]
            wallet_ids.append(wallet_id)
        # self.command.stdout.write(self.command.style.SUCCESS(f"Seeded {len(wallet_ids)} wallets"))
        return wallet_ids, merch_ids

    def seed_admin(self):
        self.seeder.add_entity(
            User,
            1,
            {"is_staff": True, "is_superuser": True, "is_active": True, 'user_type': UserTypes.Admin, 'password': PASSWORD},
        )
        user_ids = self.seeder.execute()[User]
        self.command.stdout.write(self.command.style.SUCCESS(f"Seeded {user_ids[0]} users"))
        self.admin = User.objects.get(pk=user_ids[0])
        return user_ids

    def seed_cars(self):
        self.seeder.add_entity(
            CarBrand,
            1,
            {
                'name': lambda x: 'Toyota',
                'model': lambda x: 'Camry',
                'year': lambda x: self.seeder.faker.year(),
            },
        )
        brands = self.seeder.execute()[CarBrand][0]
        cost = self.seeder.faker.random_number(digits=4)
        self.seeder.add_entity(
            MiscellaneousExpenses,
            1,
            {
                'estimated_price': cost,
            },
        )
        exp = self.seeder.execute()[MiscellaneousExpenses][0]
        exp = MiscellaneousExpenses.objects.get(pk=exp)
        carbrand = CarBrand.objects.get(pk=brands)
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
        return car

    @atomic
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
            data = dict(trade=trade.id, merchant=merchant, slots_quantity=1)
            ser = TradeUnitSerializer(data=data)
            ser.context["merchant"] = CarMerchant.objects.get(pk=merchant)
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

    def seed(self):
        # wallet_ids, merch_ids = self.seed_merchants()
        self.seed_admin()
        wallet_ids, merch_ids = self.seed_merchants(count=5)
        # self.seed_trade(Car.objects.get(pk=car), TradeStates.Ongoing)
        self.seed_completed_trade(merch_ids, should_close=True)
        self.seed_completed_trade(merch_ids, should_close=False)
        self.seed_completed_trade(merch_ids[:3])
        self.seed_completed_trade(merch_ids[:2])

    def seed_vehicle_info(self, vin):
        vehicle = self.seeder.faker.vehicle_object()
        self.seeder.add_entity(VehicleInfo, 1, {
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
            "make": vehicle['Make']
        })
        ret = self.seeder.execute()[VehicleInfo][0]
        return VehicleInfo.objects.get(id=ret)
