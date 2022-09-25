import contextlib
import itertools
from datetime import datetime
from decimal import Decimal
from typing import Optional, Union

from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import URLValidator
from django.db import models
from django.db.models import Sum, Count, Avg, Q
from django.db.transaction import atomic
from django.utils import timezone
from rest_framework import exceptions
from rest_framework import serializers
from rest_framework.fields import empty

from src.carpadi_api.serializers import BankAccountSerializer
from src.common.helpers import check_vin
from src.models.models import (
    CarMerchant,
    Car,
    Wallet,
    Transaction,
    Trade,
    Disbursement,
    Activity,
    SpareParts,
    CarStates,
    CarMaintenance,
    MiscellaneousExpenses,
    CarMaintenanceTypes,
    TradeStates,
    DisbursementStates,
    VehicleInfo,
    Assets,
    TradeUnit,
    TransactionStatus,
    TransactionTypes,
    TransactionKinds,
    AssetEntityType,
    ActivityTypes,
    FuelTypes,
    CarTypes,
    CarTransmissionTypes,
    CarBrand,
    Settings,
    InspectionStatus,
    CarDocuments,
)
from src.models.serializers import UserSerializer, CarBrandSerializer


class SocialSerializer(serializers.Serializer):
    """
    Serializer which accepts an OAuth2 access token.
    """

    access_token = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )


class VehicleInfoSerializer(serializers.ModelSerializer):
    engine = serializers.CharField(required=False)
    transmission = serializers.ChoiceField(required=False, choices=CarTransmissionTypes.choices)
    car_type = serializers.ChoiceField(choices=CarTypes.choices, required=False)
    fuel_type = serializers.ChoiceField(choices=FuelTypes.choices, required=False)
    mileage = serializers.IntegerField(required=False, min_value=1)
    age = serializers.IntegerField(required=False, min_value=1)
    description = serializers.CharField(required=False)
    trim = serializers.CharField(required=False)
    manufacturer = serializers.CharField(max_length=50, required=False)
    vin = serializers.CharField(required=True)
    brand = serializers.SerializerMethodField()

    class Meta:
        model = VehicleInfo
        fields = "__all__"
        # read_only_fields = (,)

    def get_brand(self, vehicle: VehicleInfo):
        return CarBrandSerializer(instance=vehicle.brand).data

    def create(self, validated_data):
        vin = validated_data.get("vin")
        info: Optional[VehicleInfo] = VehicleInfo.objects.filter(vin=vin).first()
        if not info:
            if data := check_vin(vin):
                validated_data.update(data)
                brand = dict(model=validated_data.pop("model"), year=validated_data.pop("year"),
                             name=validated_data.pop("make"))
                carbrand = CarBrandSerializer(data=brand)
                carbrand.is_valid(raise_exception=True)
                ins: CarBrand = carbrand.save()
                validated_data["brand"] = ins
                return super(VehicleInfoSerializer, self).create(validated_data)
            else:
                raise serializers.ValidationError(detail={"vin": "No vehicle is associated with that vin"}, code=400)
        return info


class CarSerializer(serializers.ModelSerializer):
    maintenance_cost = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()
    pictures = serializers.SerializerMethodField()
    vin = serializers.CharField(max_length=17, min_length=17)
    information = serializers.SerializerMethodField()
    car_pictures = serializers.ListField(write_only=True, child=serializers.URLField(), default=[], required=False)
    status = serializers.ChoiceField(choices=CarStates.choices, required=False, default=CarStates.New)
    bought_price = serializers.DecimalField(required=False, max_digits=15, decimal_places=5)
    inspection = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = "__all__"
        ref_name = "car_serializer_admin"
        read_only_fields = ('information',)

    def get_inspection(self, car: Car):
        with contextlib.suppress(ObjectDoesNotExist):
            if car.inspections:
                return dict(id=car.inspections.id, status=car.inspections.status)
            return None

    def get_information(self, obj: Car):
        return VehicleInfoSerializer(instance=obj.information).data

    def get_pictures(self, obj: Car):
        return Assets.objects.filter(object_id=obj.id).values_list("asset", flat=True)

    def get_total_cost(self, obj: Car):
        return obj.total_cost_calc()

    def get_maintenance_cost(self, obj: Car):
        return obj.maintenance_cost_calc()

    def validate_status(self, value):
        if self.instance:  # we are doing update
            if value == CarStates.Inspected:
                raise serializers.ValidationError("You are not allowed to set the inspection status directly")
            if value == CarStates.Available:
                # you can only change the status to available if the car is inspected and all the cost have been
                # accounted for
                try:
                    inst: Car = self.instance
                    if not inst.inspections or inst.inspections.status != InspectionStatus.Completed.value:
                        raise serializers.ValidationError(
                            "Inspection report is required and must be completed for a car to be available"
                        )
                    # if not self.instance.resale_price and not self.initial_data.get("resale_price"):
                    #     raise serializers.ValidationError(
                    #         "Resale price is required for a car with status of available")
                except ObjectDoesNotExist as reason:
                    raise serializers.ValidationError("Please create inspection for the car first.") from reason
        else:
            # we are doing create
            if value == CarStates.Inspected:
                raise serializers.ValidationError("You are not allowed to set the inspection status directly")
            if value == CarStates.Available:
                raise serializers.ValidationError("You cannot update the status of a car while creating it.")

        return value

    def validate_resale_price(self, value):
        car_trade = None
        with contextlib.suppress(models.ObjectDoesNotExist):
            car_trade: Trade = self.instance.trade
            if not self.instance or not car_trade:
                raise serializers.ValidationError("Aye! You cannot set the resale price of a car while creating it")
            if value < self.instance.trade.min_sale_price:
                raise serializers.ValidationError(
                    f"Resale price cannot be less than " f"{self.instance.trade.min_sale_price} of the car"
                )
            if self.instance and car_trade.trade_status not in (
                    TradeStates.Purchased,
                    TradeStates.Ongoing,
                    TradeStates.Pending,
            ):  # noqa
                raise serializers.ValidationError(
                    "Resale price for a car that has a trade can only" "be set after trade have been purchased "
                )
            return value

    def validate_vin(self, attr):
        info = VehicleInfo.objects.filter(vin=attr).first()
        with contextlib.suppress(ObjectDoesNotExist):
            if info and info.car:
                raise serializers.ValidationError(f"Car with the vin number {attr} exists before")
            elif not info:
                raise serializers.ValidationError("Please validate the vin before attempting to create a car with it")
        return info

    @atomic()
    def create(self, validated_data):
        info = validated_data.pop("vin")
        images = validated_data.pop("car_pictures")
        car = Car.objects.create(vin=info.vin, information=info, **validated_data)
        Assets.create_many(images=images, feature=car, entity_type=AssetEntityType.Car)
        return car

    @atomic()
    def update(self, instance: Car, validated_data):
        if validated_data.get("status") == CarStates.Available:
            validated_data["total_cost"] = instance.total_cost_calc()
            validated_data["maintenance_cost"] = instance.maintenance_cost_calc()
        return super().update(instance, validated_data)


class WalletSerializerAdmin(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = "__all__"


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = "__all__"
        read_only_fields = (
            "amount",
            "transaction_type",
            "wallet",
            "transaction_reference",
            "transaction_description",
            "transaction_status",
            "transaction_response",
            "transaction_kind",
            "transaction_payment_link",
        )


class CarSerializerField(serializers.RelatedField):
    def to_internal_value(self, data):
        car: Car = Car.objects.get(id=data)
        with contextlib.suppress(BaseException):
            if car.trade:
                raise serializers.ValidationError("This car is already being traded")
        return car

    def to_representation(self, value: Car):
        pics = value.pictures.first().asset if value.pictures.first() else None
        return dict(
            id=value.id,
            bought_price=value.bought_price,
            image=pics,
            model=value.information.brand.model,
            make=value.information.brand.name,
            maintenance_cost=value.maintenance_cost_calc(),
            resale_price=value.resale_price,
        )


class TradeSerializerAdmin(serializers.ModelSerializer):
    remaining_slots = serializers.SerializerMethodField()
    # trade_status = serializers.SerializerMethodField()
    return_on_trade = serializers.SerializerMethodField()
    return_on_trade_percentage = serializers.SerializerMethodField()
    car = CarSerializerField(queryset=Car.objects.all())
    return_on_trade_per_unit = serializers.SerializerMethodField()
    total_users_trading = serializers.SerializerMethodField()
    sold_slots_price = serializers.SerializerMethodField()
    # carpadi_rot = serializers.SerializerMethodField()
    trade_margin = serializers.SerializerMethodField()
    estimated_carpadi_rot = serializers.SerializerMethodField()

    class Meta:
        model = Trade
        fields = "__all__"
        read_only_fields = (
            'created',
            'modified',
            'slots_purchased',
            "traded_slots",
            "remaining_slots",
            "total_slots",
            "price_per_slot",
            "min_sale_price",
        )
        extra_kwargs = {
            "car": {"error_messages": {"required": "Car to trade on is required", "unique": "Car already " "traded"}}}

    def get_estimated_carpadi_rot(self, trade: Trade):
        return trade.estimated_carpadi_rot()

    def get_trade_margin(self, trade: Trade):
        return trade.margin_calc()

    # def get_carpadi_rot(self, trade: Trade):
    #     return trade.carpadi_rot

    def get_total_users_trading(self, obj: Trade):
        return obj.get_trade_merchants().count()

    def get_return_on_trade_per_unit(self, obj: Trade):
        return obj.return_on_trade_per_slot

    def get_return_on_trade(self, obj: Trade):
        return obj.return_on_trade_calc()

    def get_return_on_trade_percentage(self, obj: Trade):
        return obj.return_on_trade_calc_percent()

    def get_sold_slots_price(self, instance: Trade):
        return instance.sold_slots_price()

    def get_remaining_slots(self, trade: Trade):
        # TODO: this is a hack, fix it using annotations
        slots_purchased = sum(unit.slots_quantity for unit in trade.units.all())
        return trade.slots_available - slots_purchased

    def get_bts_time(self, trade: Trade):
        if trade.date_of_sale:
            return (trade.created.date() - trade.date_of_sale).days
        return (trade.created.date() - timezone.now()).days

    def validate_trade_status(self, attr):
        trade: Trade = self.instance
        if attr == TradeStates.Completed:
            if not trade:
                raise serializers.ValidationError("Cannot set trade status to completed when creating a trade")

            if not trade.car.resale_price:
                raise serializers.ValidationError(
                    "Please add resale price to the car first before completing the trade")

            if trade.trade_status != TradeStates.Purchased:
                raise serializers.ValidationError(
                    f"Cannot change trade status to {attr}, trade is {trade.trade_status}")

        return attr

    @atomic()
    def create(self, validated_data):
        self.validate_trade_dependencies(validated_data)
        validated_data["trade_status"] = TradeStates.Ongoing
        trade = super().create(validated_data)
        car = trade.car
        car.status = CarStates.OngoingTrade
        car.save(update_fields=["status"])
        return trade

    def validate_trade_dependencies(self, validated_data):
        car: Car = validated_data.get("car")
        inspection = car.inspections
        if inspection.status != InspectionStatus.Completed:
            raise serializers.ValidationError("Inspection is not completed yet, trade cannot be created")
        if not CarDocuments.documentation_completed(car.id):
            raise serializers.ValidationError("Some documents have either not "
                                              "being uploaded or not yet verified, please contact admin")
        if car.status != CarStates.Available:
            raise serializers.ValidationError("Car is not available for trade")
        if not car.bought_price:
            raise serializers.ValidationError("Please set the amount the car was bought for before creating a trade")
        if validated_data.get("slots_available") < 4:
            raise serializers.ValidationError("The minimum amount of slot is four.")

    def validate_trade_update(self, instance: Trade, validated_data):
        if validated_data.get(
                "trade_status") != TradeStates.Closed and instance.trade_status == TradeStates.Completed:
            raise serializers.ValidationError("You can only close a completed trade")
        if validated_data.get("trade_status") != TradeStates.Completed and\
                instance.trade_status == TradeStates.Purchased:
            raise serializers.ValidationError("You can only complete a purchased trade")
        if instance.trade_status == TradeStates.Closed and validated_data.get("trade_status"):
            raise serializers.ValidationError("The status of a closed trade cannot be changed.")
        for key in validated_data.keys():
            if key not in ("estimated_sales_duration", "trade_status"):
                raise serializers.ValidationError("you can only update the duration and status of a trade")

    @atomic()
    def update(self, instance: Trade, validated_data):
        self.validate_trade_update(instance, validated_data)
        updated_instance: Trade = super(TradeSerializerAdmin, self).update(instance, validated_data)
        if (
                "trade_status" in validated_data.keys()
                and updated_instance.trade_status == TradeStates.Completed
                and instance.trade_status != TradeStates.Completed
        ):
            updated_instance.check_updates()
            updated_instance.refresh_from_db()
        return updated_instance


class DisbursementSerializerAdmin(serializers.ModelSerializer):
    class Meta:
        model = Disbursement
        fields = ("created", "id", "amount", "trade_unit")
        read_only_fields = ("created", "id", "amount", "trade_unit")


class SparePartsSerializer(serializers.ModelSerializer):
    part_picture = serializers.SerializerMethodField()
    picture = serializers.URLField(write_only=True, required=False)

    class Meta:
        model = SpareParts
        fields = "__all__"

    def get_part_picture(self, part: SpareParts):
        if asset := Assets.objects.filter(object_id=part.id).first():
            return asset.asset
        return None

    def create(self, validated_data):
        if maybe_par := SpareParts.objects.filter(
                name=validated_data.get("name"), car_brand=validated_data.get("car_brand")
        ).first():
            return self.update(instance=maybe_par, validated_data=validated_data)
        picture = validated_data.pop("picture")
        instance: SpareParts = super(SparePartsSerializer, self).create(validated_data)
        if picture:
            Assets.objects.create(asset=picture, content_object=instance, entity_type=AssetEntityType.CarSparePart)
        instance.refresh_from_db()
        return instance

    def update(self, instance, validated_data):
        if picture := validated_data.get("picture"):
            asset: Assets = Assets.objects.create(
                asset=picture, content_object=instance, entity_type=AssetEntityType.CarSparePart
            )
            validated_data["picture"] = asset.asset
        return super(SparePartsSerializer, self).update(instance, validated_data)


class MiscellaneousExpensesSerializer(serializers.ModelSerializer):
    class Meta:
        model = MiscellaneousExpenses
        fields = "__all__"


class CarMaintenanceSerializerAdmin(serializers.ModelSerializer):
    maintenance = serializers.DictField(write_only=True, help_text="An object of either the expense or spare part")
    object_id = serializers.HiddenField(required=False, default=None)
    content_type = serializers.HiddenField(required=False, default=None)
    maintenance_data = serializers.SerializerMethodField()
    cost = serializers.SerializerMethodField()

    class Meta:
        model = CarMaintenance
        fields = "__all__"
        read_only_fields = ("created", "modified")
        hidden_fields = ("object_id", "content_type")

    def get_cost(self, instance: CarMaintenance):
        return instance.cost()

    def get_maintenance_data(self, obj: CarMaintenance):
        if obj.type == CarMaintenanceTypes.Expense:
            return MiscellaneousExpensesSerializer(instance=obj.maintenance).data
        return SparePartsSerializer(instance=obj.maintenance).data

    def validate_maintenance_kind(self, value: dict, car: Car, maintenance_type: str):
        result = dict(type=maintenance_type)
        if maintenance_type == CarMaintenanceTypes.SparePart:
            value["car_brand"] = car.information.brand.id
            part = SparePartsSerializer(data=value)
            return self.validate_part(part, result)
        elif maintenance_type == CarMaintenanceTypes.Expense:
            part = MiscellaneousExpensesSerializer(data=value)
            return self.validate_part(part, result)
        raise serializers.ValidationError(
            {"error": f"Invalid maintenance types. please select from {CarMaintenanceTypes.choices}"}
        )

    def validate_part(self, part, data):
        part.is_valid(raise_exception=True)
        instance: Union[SpareParts, MiscellaneousExpenses] = part.save()
        data["maintenance"] = instance
        return data

    @atomic()
    def create(self, validated_data):
        car: Car = validated_data["car"]
        if car.status in [CarStates.OngoingTrade, CarStates.Sold, CarStates.Archived]:
            raise serializers.ValidationError({"error": f"new maintenance cannot be created for an {car.status} car"})
        data = self.validate_maintenance_kind(validated_data.pop("maintenance"), car, validated_data.pop("type"))
        validated_data.update(data)
        return super(CarMaintenanceSerializerAdmin, self).create(validated_data)

    @atomic()
    def update(self, instance: CarMaintenance, validated_data):
        type = instance.type
        car = instance.car
        if validated_data.get("type") or validated_data.get("car"):
            raise serializers.ValidationError({"error": "car or type cannot be updated"})
        if car.status in (CarStates.Available, CarStates.OngoingTrade, CarStates.Bought, CarStates.Archived):
            raise serializers.ValidationError(
                {"error": "Maintenance can only be created or updated for cars that have not been traded."}
            )
        if validated_data.get("maintenance"):
            if type == CarMaintenanceTypes.SparePart:
                ser = SparePartsSerializer(data=validated_data["maintenance"], partial=True)
                ser.is_valid(raise_exception=True)
                maint_inst: SpareParts = ser.update(instance.maintenance, validated_data["maintenance"])
            else:
                ser = MiscellaneousExpensesSerializer(data=validated_data["maintenance"], partial=True)
                ser.is_valid(raise_exception=True)
                maint_inst: MiscellaneousExpenses = ser.update(instance.maintenance, validated_data["maintenance"])
        instance.refresh_from_db()
        return instance


class TradeDashboardSerializer(serializers.Serializer):
    active_trades = serializers.SerializerMethodField()
    sold_trades = serializers.SerializerMethodField()
    closed_trades = serializers.SerializerMethodField()
    expired_trades = serializers.SerializerMethodField()
    purchased_trades = serializers.SerializerMethodField()

    # TODO trading users here includes duplicates pls distinct them
    def get_active_trades(self, obj):
        trds = Trade.objects.filter(trade_status=TradeStates.Ongoing)
        trading_users = trds.annotate(trading_user=Count('units')).distinct().aggregate(
            trading_users=Sum('trading_user')).get(
            'trading_users'
        ) or Decimal(0)
        return dict(trading_users=trading_users, active_trades=trds.count())

    def get_sold_trades(self, obj):
        trds = Trade.objects.filter(trade_status=TradeStates.Completed)
        trading_users = [trd.get_trade_merchants() for trd in trds]
        # users = list(itertools.chain(*trading_users))
        return dict(trading_users=len(trading_users), sold_trades=len(trds))

    def get_closed_trades(self, obj):
        trds = Trade.objects.filter(trade_status=TradeStates.Closed)
        trading_users = {trd.get_trade_merchants() for trd in trds}
        return dict(trading_users=len(trading_users), closed_trades=len(trds))

    def get_purchased_trades(self, obj):
        trds = Trade.objects.filter(trade_status=TradeStates.Purchased)
        trading_users = [trd.get_trade_merchants() for trd in trds]
        return dict(trading_users=len(trading_users), purchased_trades=len(trds))

    def get_expired_trades(self, obj):
        trds = Trade.objects.filter(trade_status=TradeStates.Expired)
        trading_users = [trd.get_trade_merchants() for trd in trds]
        return dict(trading_users=len(trading_users), expired_trades=len(trds))


class AccountDashboardSerializer(serializers.Serializer):
    start_date = serializers.DateField(required=False, write_only=True)
    end_date = serializers.DateField(required=False, write_only=True)
    total_trading_cash = serializers.SerializerMethodField()
    total_withdrawable_cash = serializers.SerializerMethodField()
    total_unsettled_cash = serializers.SerializerMethodField()
    total_transfer_charges = serializers.SerializerMethodField()
    total_withdrawals_count = serializers.SerializerMethodField()
    total_deposits_count = serializers.SerializerMethodField()
    total_assets = serializers.SerializerMethodField()

    def __init__(self, instance=None, data=None, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.start_date = self.initial_data["start_date"] if self.initial_data else datetime.now().date().replace(day=1)
        self.end_date = self.initial_data["end_date"] if self.initial_data else datetime.now().date()

    def get_total_trading_cash(self, value):
        """
        Total trading cash is the amount of cash that is used to trade cars currently.
        It is the sum of all units bought on trades that are not completed.
        """
        units = TradeUnit.objects.filter(
            trade__trade_status__in=(
                TradeStates.Ongoing,
                TradeStates.Purchased,
            ),
        )
        total_trading_cash = units.aggregate(value=Sum("unit_value")).get("value") or Decimal(0)
        users_trading_count = units.values("merchant").distinct().count()
        return dict(total_trading_cash=total_trading_cash, users_trading_count=users_trading_count)

    def get_total_withdrawable_cash(self, value):
        """The total amount of cash that can be withdrawn from user accounts accross the system"""
        wallets = Wallet.objects.filter(merchant__user__is_active=True)
        total_withdrawable_cash = sum(i.get_withdrawable_cash() for i in wallets)
        users_withdrawable_count = wallets.count()
        return dict(total_withdrawable_cash=total_withdrawable_cash, users=users_withdrawable_count)

    def get_total_unsettled_cash(self, value):
        """The total amount of cash that is unsettled across the system.
        unsettled cash are for now the trades rots that are yet to be moved to withdrawable cash
        """
        wallets = Wallet.objects.filter(merchant__user__is_active=True)
        total_unsettled_cash = sum(i.get_unsettled_cash() for i in wallets)
        users_unsettled_count = wallets.count()
        return dict(total_unsettled_cash=total_unsettled_cash, users=users_unsettled_count)

    def get_total_transfer_charges(self, value):
        """The total amount of transfer charges that was paid for withdrawals across the system"""
        transactions = Transaction.objects.filter(
            transaction_status=TransactionStatus.Success,
            transaction_type=TransactionTypes.Debit,
            transaction_kind=TransactionKinds.Withdrawal,
            created__date__gte=self.start_date,
            created__date__lte=self.end_date,
        )
        total_transfer_charges = transactions.aggregate(value=Sum("transaction_fees")).get("value") or Decimal(0)
        users = transactions.values("wallet__merchant").distinct().count()
        return dict(total_transfer_charges=total_transfer_charges, users=users)

    def get_total_deposits_count(self, value):
        """The total amount of deposits made across the system"""
        transactions = Transaction.objects.filter(
            transaction_status=TransactionStatus.Success,
            transaction_type=TransactionTypes.Credit,
            transaction_kind=TransactionKinds.Deposit,
            created__date__gte=self.start_date,
            created__date__lte=self.end_date,
        )
        total_deposits_count = transactions.count()
        users = transactions.values("wallet__merchant").distinct().count()
        return dict(total_deposits_count=total_deposits_count, users=users)

    def get_total_withdrawals_count(self, value):
        """The total amount of withdrawals made across the system"""
        transactions = Transaction.objects.filter(
            transaction_status=TransactionStatus.Success,
            transaction_type=TransactionTypes.Debit,
            transaction_kind=TransactionKinds.Withdrawal,
            created__date__gte=self.start_date,
            created__date__lte=self.end_date,
        )
        total_withdrawals_count = transactions.count()
        users = transactions.values("wallet__merchant").distinct().count()
        return dict(total_withdrawals_count=total_withdrawals_count, users=users)

    def get_total_assets(self, value):
        """The total amount of assets across the system"""
        wallets = Wallet.objects.filter(merchant__user__is_active=True)
        total_asset = sum(i.get_total_cash() for i in wallets)
        users = wallets.count()
        return dict(total_assets=total_asset, users=users)

    def get_asset_pie_chart(self, value):
        """the distribution of assets by their transaction type across the system"""
        result = {}
        deposits = Transaction.objects.filter(
            transaction_status=TransactionStatus.Success,
            transaction_type=TransactionTypes.Credit,
            transaction_kind=TransactionKinds.Deposit,
        )
        withdrawals = Transaction.objects.filter(
            transaction_status=TransactionStatus.Success,
            transaction_type=TransactionTypes.Debit,
            transaction_kind=TransactionKinds.Withdrawal,
        )
        disbursements = Transaction.objects.filter(
            transaction_status=TransactionStatus.Success,
            transaction_type=TransactionTypes.Debit,
            transaction_kind=TransactionKinds.Disbursement,
        )
        result["deposits"] = deposits.aggregate(value=Sum("transaction_amount")).get("value") or Decimal(0)
        result["withdrawals"] = withdrawals.aggregate(value=Sum("transaction_amount")).get("value") or Decimal(0)
        result["disbursements"] = disbursements.aggregate(value=Sum("transaction_amount")).get("value") or Decimal(0)
        result['chart_data'] = []  # TODO clarification on this is still needed
        return result


class InventoryDashboardSerializer(serializers.Serializer):
    car_listing = serializers.SerializerMethodField()
    under_inspection = serializers.SerializerMethodField()
    passed_for_trade = serializers.SerializerMethodField()
    ongoing_trade = serializers.SerializerMethodField()
    sold = serializers.SerializerMethodField()
    archived = serializers.SerializerMethodField()

    def get_car_listing(self, value):
        """The total amount of cars in the system"""
        return Car.objects.exclude(status=CarStates.Available).count()

    def get_under_inspection(self, value):
        """The total amount of cars under inspection"""
        return Car.objects.filter(status=CarStates.OngoingInspection).count()

    def get_passed_for_trade(self, value):
        """The total amount of cars passed for trade"""
        return Car.objects.filter(status=CarStates.Available).count()

    def get_ongoing_trade(self, value):
        """The total amount of cars in trade"""
        return Car.objects.filter(
            trade__trade_status=TradeStates.Ongoing
        ).count()  # Trade.objects.filter(trade_status=TradeStates.Ongoing).count()

    def get_sold(self, value):
        """The total amount of cars sold"""
        return Car.objects.filter(status=CarStates.Sold).count()

    def get_archived(self, value):
        """The total amount of cars archived"""
        return Car.objects.filter(status=CarStates.Archived).count()


class MerchantDashboardSerializer(serializers.Serializer):
    total_users = serializers.SerializerMethodField()
    active_users = serializers.SerializerMethodField()
    inactive_users = serializers.SerializerMethodField()

    def get_total_users(self, value):
        """The total amount of users in the system"""
        return CarMerchant.objects.count()

    def get_active_users(self, value):
        """The total amount of active users in the system"""
        return TradeUnit.objects.filter(merchant__user__is_active=True).values('merchant').distinct().count()

    def get_inactive_users(self, value):
        """The total amount of inactive users in the system"""
        return CarMerchant.objects.filter(user__is_active=False, user__is_staff=False).count()

    def get_non_trading_users(self, value):
        """The total amount of non trading users in the system"""
        return self.get_total_users(None) - self.get_active_users(None)


class TradeUnitSerializerAdmin(serializers.ModelSerializer):
    merchant = serializers.SerializerMethodField()
    trade_sold_date = serializers.SerializerMethodField()
    trade_car = serializers.SerializerMethodField()
    rot_per_slot = serializers.SerializerMethodField()
    price_per_slot = serializers.SerializerMethodField()
    payment_transaction_ref = serializers.SerializerMethodField()
    trade_status = serializers.SerializerMethodField()

    def get_trade_status(self, unit: TradeUnit):
        return unit.trade.trade_status

    def get_payment_transaction_ref(self, unit: TradeUnit):
        return unit.buy_transaction.transaction_reference

    def get_trade_sold_date(self, unit: TradeUnit):
        return unit.trade.date_of_sale

    def get_trade_car(self, unit: TradeUnit):
        pictures = unit.trade.car.pictures.count()
        return dict(
            id=unit.trade.car.id,
            manufacturer=unit.trade.car.information.manufacturer,
            model=unit.trade.car.information.brand.model,
            year=unit.trade.car.information.brand.year,
            images=unit.trade.car.pictures.first().asset if pictures else None,
        )

    def get_merchant(self, unit: TradeUnit):
        return dict(name=unit.merchant.user.username, id=unit.merchant.id,
                    image=str(unit.merchant.user.profile_picture))

    def get_rot_per_slot(self, unit: TradeUnit):
        return unit.estimated_rot / unit.slots_quantity

    def get_price_per_slot(self, unit: TradeUnit):
        return unit.unit_value / unit.slots_quantity

    class Meta:
        model = TradeUnit
        fields = (
            "share_percentage",
            "slots_quantity",
            "unit_value",
            "estimated_rot",
            "merchant",
            "trade",
            "id",
            "trade_sold_date",
            "trade_car",
            "rot_per_slot",
            "price_per_slot",
            "payment_transaction_ref",
            "trade_status",
        )


class HomeDashboardSerializer(serializers.Serializer):
    average_bts = serializers.SerializerMethodField()
    number_of_trading_users = serializers.SerializerMethodField()
    average_trading_cash = serializers.SerializerMethodField()
    total_available_shares = serializers.SerializerMethodField()
    total_available_shares_value = serializers.SerializerMethodField()
    total_cars_with_shares = serializers.SerializerMethodField()
    total_trading_cash_vs_return_on_trades = serializers.SerializerMethodField()
    cars_summary = serializers.SerializerMethodField()
    recent_trade_activities = serializers.SerializerMethodField()

    def __init__(self, instance=None, data=None, **kwargs):
        super().__init__(instance, data, **kwargs)
        self.fields['start_date'] = serializers.DateField(
            required=False, default=datetime.now().date().replace(day=1), allow_null=True
        )
        self.fields['end_date'] = serializers.DateField(required=False, default=datetime.now().date(), allow_null=True)
        self.fields['filter_year_only'] = serializers.BooleanField(default=False, required=False, allow_null=True)

    def validate(self, attrs):
        self.filter_year_only = attrs["filter_year_only"]
        self.start_date = attrs.get("start_date")
        self.end_date = attrs.get("end_date")
        if self.filter_year_only:
            self.start_date.replace(month=1, day=1)
            self.end_date.replace(month=12, day=31)
        return attrs

    def get_average_bts(self, value):
        """
        The Average Buy to sell time for all completed trades,
        within the current month or a specified date range.
        """

        bts = (
            Trade.objects.filter(
                trade_status__in=(TradeStates.Completed, TradeStates.Closed),
                created__date__gte=self.start_date,
                created__date__lte=self.end_date,
            )
                .aggregate(value=Avg("bts_time"))
                .get("value")
        )

        return bts or Decimal(0.00)

    def get_number_of_trading_users(self, value):
        """
        The total number of users that has placed a trade,
        within the current month or a specified date range.
        """

        return (
                TradeUnit.objects.filter(created__date__gte=self.start_date, created__date__lte=self.end_date)
                .values("merchant")
                .distinct()
                .count()
                or 0
        )

    def get_average_trading_cash(self, value):
        """
        The average cash per slot,
        i.e. the average amount the users uses to invest in a car,
        within the current month or a specified date range.
        """

        cash = (
            TradeUnit.objects.filter(created__date__gte=self.start_date, created__date__lte=self.end_date)
                .aggregate(value=Avg("unit_value"))
                .get("value")
        )

        return cash or Decimal(0.00)

    def get_total_available_shares(self, value):
        """
        The total available shares in all open trades,
        within the current month or a specified date range.
        """

        shares = (
            Trade.objects.filter(
                trade_status=TradeStates.Ongoing, created__date__gte=self.start_date, created__date__lte=self.end_date
            )
                .aggregate(value=Sum("slots_available"))
                .get("value")
        )

        return shares or 0

    def get_total_available_shares_value(self, value):
        """
        The total value of shares in all open trades,
        within the current month or a specified date range.
        """

        trades = Trade.objects.filter(
            trade_status=TradeStates.Ongoing, created__date__gte=self.start_date, created__date__lte=self.end_date
        )
        values = Decimal(0)
        for i in trades:
            value = i.remaining_slots() * i.price_per_slot
            values = values + value
        return values

    def get_total_cars_with_shares(self, value):
        """
        The total numbers of cars on trade with available shares,
        within the current month or a specified date range.
        """

        cars = Trade.objects.filter(
            trade_status=TradeStates.Ongoing, created__date__gte=self.start_date, created__date__lte=self.end_date
        ).count()
        return cars or 0

    def extract_monthly_graph(self):
        cash = [Decimal(0)] * 12
        trade_return = [Decimal(0)] * 12

        i = 0
        while i < 12:
            self.start_date.replace(month=i + 1)

            ttc = TradeUnit.objects.filter(created__date__month=self.start_date.month).values("slots_quantity",
                                                                                              "unit_value")

            cash[i] = sum(s["slots_quantity"] * s["unit_value"] for s in ttc) or Decimal(0)

            rot = (
                Trade.objects.filter(
                    trade_status__in=(TradeStates.Completed, TradeStates.Closed),
                    modified__date__year=self.start_date.year,
                    modified__date__month=self.start_date.month,
                )
                    .aggregate(value=Sum("return_on_trade"))
                    .get("value")
            )

            trade_return[i] = rot or Decimal(0)

            i += 1

        return dict(graph_type="monthly", ttc=cash, rot=trade_return)

    def extract_weekly_graph(self):
        cash = [Decimal(0)] * 5
        trade_return = [Decimal(0)] * 5

        current_week = self.start_date.isocalendar()[1]
        start_week = serializers.IntegerField

        if current_week >= datetime.today().isocalendar()[1]:
            start_week = current_week - 5 or 1
        else:
            start_week = current_week - 3

        graph_partition = 5
        i = 0
        while i < graph_partition:
            ttc = TradeUnit.objects.filter(created__date__year=self.start_date.year,
                                           created__date__week=start_week).values(
                "slots_quantity", "unit_value"
            )

            cash[i] = sum(s["slots_quantity"] * s["unit_value"] for s in ttc) or Decimal(0)

            rot = (
                Trade.objects.filter(
                    trade_status__in=(TradeStates.Completed, TradeStates.Closed),
                    modified__date__year=self.start_date.year,
                    modified__date__week=start_week,
                )
                    .aggregate(value=Sum("return_on_trade"))
                    .get("value")
            )

            trade_return[i] = rot or Decimal(0)

            i += 1

        return dict(graph_type="weekly", ttc=cash, rot=trade_return)

    def get_total_trading_cash_vs_return_on_trades(self, value):
        """
        Segmented value of  Total Trading cash and Return on Trades,
        within the current month or a specified date range,
        which can be used to plot weekly or monthly graph.
        """

        if self.filter_year_only:
            monthly = self.extract_monthly_graph()
            return monthly
        else:
            weekly = self.extract_weekly_graph()
            return weekly

    def get_cars_summary(self, value):
        """
        Cars Summary
        """
        total_cars = Car.objects.filter(
            created__date__year=datetime.now().year,
        ).count()

        inspected_cars = Car.objects.filter(created__date__year=datetime.now().year, status=CarStates.Inspected).count()
        inspected_cars_percent = (inspected_cars / total_cars) * 100 or Decimal(0)
        inspection = dict(count=inspected_cars, percentage=inspected_cars_percent)

        available_cars = Car.objects.filter(created__date__year=datetime.now().year, status=CarStates.Available).count()
        available_cars_percent = (available_cars / total_cars) * 100 or Decimal(0)
        available = dict(count=available_cars, percentage=available_cars_percent)

        trading_cars = Car.objects.filter(created__date__year=datetime.now().year,
                                          status=CarStates.OngoingTrade).count()
        trading_cars_percent = (trading_cars / total_cars) * 100 or Decimal(0)
        trading = dict(count=trading_cars, percentage=trading_cars_percent)

        sold_cars = Car.objects.filter(created__date__year=datetime.now().year, status=CarStates.Sold).count()
        sold_cars_percent = (sold_cars / total_cars) * 100 or Decimal(0)
        sold = dict(count=sold_cars, percentage=sold_cars_percent)

        return dict(total_cars=total_cars, available=available, trading=trading, inspection=inspection, sold=sold)

    def get_recent_trade_activities(self, value):
        """
        Last Ten Trading activities carried out
        """
        recent_activities = Activity.objects.filter(activity_type=ActivityTypes.TradeUnit).values("description",
                                                                                                  "merchant")[:10]
        return dict(recent_activities=recent_activities)


class CarMerchantAdminSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    banks = serializers.SerializerMethodField()

    def get_banks(self, merchant: CarMerchant):
        return BankAccountSerializer(instance=merchant.bank_accounts.all(), many=True).data

    def get_user(self, merchant: CarMerchant):
        user_ser = UserSerializer(instance=merchant.user)
        return user_ser.data

    class Meta:
        model = CarMerchant
        fields = "__all__"


class SettingsSerializerAdmin(serializers.ModelSerializer):
    class Meta:
        model = Settings
        fields = "__all__"


class CarDocumentsSerializer(serializers.ModelSerializer):
    asset = serializers.URLField(required=True)

    class Meta:
        model = CarDocuments
        fields = "__all__"

    @atomic()
    def create(self, validated_data):
        url = validated_data.pop("asset")
        doc = super(CarDocumentsSerializer, self).create(validated_data)
        asset = Assets.objects.create(asset=url, content_object=doc, entity_type=AssetEntityType.CarDocument)
        doc.asset = asset
        doc.save(update_fields=["asset"])
        return doc

    @atomic()
    def update(self, instance, validated_data):
        url = validated_data.pop("asset") if validated_data.get("asset") else None
        doc = super(CarDocumentsSerializer, self).update(instance, validated_data)
        if url:
            asset = Assets.objects.create(asset=url, content_object=doc, entity_type=AssetEntityType.CarDocument)
            doc.asset = asset
        doc.save(update_fields=["asset"])
        return doc

