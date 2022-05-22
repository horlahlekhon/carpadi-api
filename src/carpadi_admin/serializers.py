import itertools
from datetime import datetime
from decimal import Decimal

from django.db.models import Sum, Count
from django.db.transaction import atomic
from django.utils import timezone
from rest_framework import serializers, exceptions

from src.common.helpers import check_vin
from src.models.models import (
    Car,
    Wallet,
    Transaction,
    Trade,
    Disbursement,
    Activity,
    SpareParts,
    TradeUnit,
    TransactionStatus,
    TransactionTypes,
    TransactionKinds,
    CarMerchant,
    Assets, VehicleInfo,
)
from src.models.models import (
    TradeStates,
    CarStates,
    CarMaintenance,
    CarMaintenanceTypes,
    MiscellaneousExpenses,
    DisbursementStates,
)


class SocialSerializer(serializers.Serializer):
    """
    Serializer which accepts an OAuth2 access token.
    """

    access_token = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )


class VehicleInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleInfo
        fields = "__all__"


class CarSerializer(serializers.ModelSerializer):
    maintenance_cost = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()
    pictures = serializers.SerializerMethodField()
    vin = serializers.CharField(max_length=17, min_length=17)
    information = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = "__all__"
        ref_name = "car_serializer_admin"
        read_only_fields = ('information',)

    def get_information(self, obj: Car):
        return VehicleInfoSerializer(instance=obj.information).data

    def get_pictures(self, obj: Car):
        pictures = Assets.objects.filter(object_id=obj.id).values_list("asset", flat=True)
        return pictures

    def get_total_cost(self, obj: Car):
        return obj.total_cost_calc()

    def get_maintenance_cost(self, obj: Car):
        return obj.maintenance_cost_calc()

    def validate_status(self, value):
        if self.instance:  # we are doing update
            if value == CarStates.Inspected:
                if (
                        not self.instance.inspection_report
                        and not self.initial_data.get("inspection_report")
                        and not self.instance.inspector
                        and not self.initial_data.get("inspector")
                ):
                    raise serializers.ValidationError(
                        "Inspection report is required for a car with status of inspected")
            if value == CarStates.Available:
                # you can only change the status to available if the car is inspected and all the cost have been
                # accounted for
                if not self.instance.inspection_report and not self.initial_data.get("inspection_report"):
                    raise serializers.ValidationError(
                        "Inspection report is required for a car with status of available")
                if not self.instance.resale_price and not self.initial_data.get("resale_price"):
                    raise serializers.ValidationError("Resale price is required for a car with status of available")
            return value
        else:
            # we are doing create
            if value == CarStates.Inspected:
                if not self.initial_data.get("inspection_report"):
                    raise serializers.ValidationError(
                        "Inspection report is required for a car with status of inspected")
                if not self.initial_data.get("car_inspector"):
                    raise serializers.ValidationError(
                        "A valid car inspector is required for cars that have been inspected")
            if value == CarStates.Available:
                if not self.initial_data.get("inspection_report"):
                    raise serializers.ValidationError(
                        "Inspection report is required for a car with status of available")
                if not self.initial_data.get("resale_price"):
                    raise serializers.ValidationError("Resale price is required for a car with status of available")
            return value

    def validate_resale_price(self, value):
        if self.instance:
            if value < self.instance.total_cost_calc():
                raise serializers.ValidationError("Resale price cannot be less than the total cost of the car")
        else:
            raise serializers.ValidationError("Aye! You cannot create set the resale price of a car while creating it")
        return value

    def validate_vin(self, attr):
        try:
            return VehicleInfo.objects.get(vin=attr)
        except VehicleInfo.DoesNotExist as reason:
            vin = check_vin(attr)
            if not vin:
                raise serializers.ValidationError("Invalid vin number")
            return VehicleInfo.objects.create(vin=attr, **vin)

    @atomic()
    def create(self, validated_data):
        info = validated_data.pop("vin")
        car = Car.objects.create(vin=info.vin, information=info, **validated_data)
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
        try:
            if car.trade:
                raise serializers.ValidationError("This car is already being traded")
        except BaseException as e:
            pass
        return car

    def to_representation(self, value):
        return value.id


class TradeSerializerAdmin(serializers.ModelSerializer):
    remaining_slots = serializers.SerializerMethodField()
    # trade_status = serializers.SerializerMethodField()
    return_on_trade = serializers.SerializerMethodField()
    return_on_trade_percentage = serializers.SerializerMethodField()
    car = CarSerializerField(queryset=Car.objects.all())
    return_on_trade_per_unit = serializers.SerializerMethodField()

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
        )
        extra_kwargs = {
            "car": {"error_messages": {"required": "Car to trade on is required", "unique": "Car already " "traded"}}}

    def get_return_on_trade_per_unit(self, obj: Trade):
        return obj.return_on_trade_per_slot()

    def get_return_on_trade(self, obj: Trade):
        return obj.return_on_trade_calc()

    def get_return_on_trade_percentage(self, obj: Trade):
        return obj.return_on_trade_calc_percent()

    def calculate_price_per_slot(self, car_price, slots_availble):
        return car_price / slots_availble

    def get_remaining_slots(self, trade: Trade):
        # TODO: this is a hack, fix it using annotations
        slots_purchased = sum([unit.slots_quantity for unit in trade.units.all()])
        return trade.slots_available - slots_purchased

    def get_bts_time(self, trade: Trade):
        if trade.date_of_sale:
            return (trade.created.date() - trade.date_of_sale).days
        return (trade.created.date() - timezone.now()).days

    def validate_trade_status(self, attr):
        trade: Trade = self.instance
        if not trade:  # we are creating
            if attr == TradeStates.Completed:
                raise serializers.ValidationError("Cannot set trade status to completed when creating a trade")
        else:
            if attr == TradeStates.Completed:
                if not trade.car.resale_price:
                    raise serializers.ValidationError(
                        "Please add resale price to the car first before completing the trade")
                if trade.trade_status != TradeStates.Purchased:
                    raise serializers.ValidationError(
                        "Cannot change trade status to {}, trade is {}".format(attr, trade.trade_status)
                    )
        return attr

    def validate_car(self, value):
        if value.status != CarStates.Available:
            raise serializers.ValidationError("Car is not available for trade yet")
        return value

    def validate_min_sale_price(self, value):
        car: Car = Car.objects.get(id=self.initial_data.get("car"))
        if value < car.total_cost_calc():
            raise serializers.ValidationError("Minimum sale price cannot be less than the total cost of the car")
        return value

    def validate_max_sale_price(self, value):
        car: Car = Car.objects.get(id=self.initial_data.get("car"))
        if value < car.total_cost_calc():
            raise serializers.ValidationError("Maximum sale price cannot be less than the total cost of the car")
        return value

    @atomic()
    def create(self, validated_data):
        return super().create(validated_data)

    def complete_trade(self, trade: Trade):
        """
        Completes the trade by setting the trade status to completed and updating the car status.
        we also try to do some validation to make sure trade and its corresponding objects are valid
        :param trade: Trade object
        """
        successful_disbursements = trade.units.filter(
            disbursement__disbursement_status=DisbursementStates.Unsettled).count()
        query = trade.units.annotate(total_disbursed=Sum('disbursement__amount'))
        total_disbursed = query.aggregate(sum=Sum('total_disbursed')).get('sum') or Decimal(0)
        if successful_disbursements == trade.units.count() and total_disbursed == trade.total_payout():
            car: Car = trade.car
            car.update_on_sold()
        else:
            raise exceptions.APIException(
                "Error, cannot complete trade, because calculated" " payout seems to be unbalanced with the disbursements"
            )

    @atomic()
    def update(self, instance: Trade, validated_data):
        if instance.trade_status == TradeStates.Closed:
            raise serializers.ValidationError("Cannot update a closed trade.. Geez!!")
        # if validated_data.get("trade_status") and validated_data.get("trade_status") == TradeStates.Completed:
        #     instance.run_disbursement()
        #     # check disbursements and update trade state
        #     self.complete_trade(instance)
        return super(TradeSerializerAdmin, self).update(instance, validated_data)


class DisbursementSerializerAdmin(serializers.ModelSerializer):
    class Meta:
        model = Disbursement
        fields = ("created", "id", "amount", "trade_unit")
        read_only_fields = ("created", "id", "amount", "trade_unit")


class CarMaintenanceSerializerAdmin(serializers.ModelSerializer):
    spare_part_id = serializers.UUIDField(required=False)
    cost = serializers.DecimalField(
        required=False, help_text="Cost of the maintenance in case it is a misc expenses", max_digits=10,
        decimal_places=2
    )
    description = serializers.CharField(required=False, help_text="Description of the maintenance")
    name = serializers.CharField(required=False, help_text="Name of the maintenance, in case it is a misc expenses")
    object_id = serializers.HiddenField(required=False, default=None)
    content_type = serializers.HiddenField(required=False, default=None)

    class Meta:
        model = CarMaintenance
        fields = "__all__"
        read_only_fields = ("created", "modified")
        hidden_fields = ("object_id", "content_type")

    def validate_spare_part_id(self, value):
        if value:
            try:
                spare_part = SpareParts.objects.get(id=value)
            except SpareParts.DoesNotExist:
                raise serializers.ValidationError("Spare part does not exist")
            return spare_part
        return value

    @atomic()
    def create(self, validated_data):
        car: Car = validated_data["car"]
        if car.status == CarStates.Available:
            raise serializers.ValidationError({"error": "new maintenance cannot be created for an available car"})
        maintenance_type = validated_data["type"]
        if maintenance_type == CarMaintenanceTypes.SparePart:
            part: SpareParts = validated_data["spare_part_id"]
            cost = part.estimated_price
            return CarMaintenance.objects.create(car=car, type=maintenance_type, cost=cost, maintenance=part)
        else:
            cost = validated_data["cost"]
            description = validated_data["description"]
            misc = MiscellaneousExpenses.objects.create(
                estimated_price=cost, description=description, name=validated_data["name"]
            )
            return CarMaintenance.objects.create(car=car, type=maintenance_type, cost=cost, maintenance=misc)


class SparePartsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpareParts
        fields = "__all__"


class TradeDashboardSerializer(serializers.Serializer):
    active_trades = serializers.SerializerMethodField()
    sold_trades = serializers.SerializerMethodField()
    closed_trades = serializers.SerializerMethodField()

    def get_active_trades(self, obj):
        trds = Trade.objects.filter(trade_status__in=(TradeStates.Ongoing, TradeStates.Purchased))
        trading_users = trds.annotate(trading_user=Count('units')).aggregate(trading_users=Sum('trading_user')).get(
            'trading_users'
        ) or Decimal(0)
        return dict(trading_users=trading_users, active_trades=trds.count())

    def get_sold_trades(self, obj):
        trds = Trade.objects.filter(trade_status=TradeStates.Completed)
        trading_users = [trd.get_trade_merchants() for trd in trds]
        users = list(itertools.chain(*trading_users))
        return dict(trading_users=len(users), sold_trades=len(trds))

    def get_closed_trades(self, obj):
        trds = Trade.objects.filter(trade_status=TradeStates.Closed)
        trading_users = [trd.get_trade_merchants() for trd in trds]
        users = list(itertools.chain(*trading_users))
        return dict(trading_users=len(users), closed_trades=len(trds))


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
        self.start_date = self.initial_data["start_date"]
        self.end_date = self.initial_data["end_date"]

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
        return Car.objects.filter(status=CarStates.Available).count()

    def get_under_inspection(self, value):
        """The total amount of cars under inspection"""
        return Car.objects.filter(status=CarStates.New).count()

    def get_passed_for_trade(self, value):
        """The total amount of cars passed for trade"""
        return Car.objects.filter(status=CarStates.Available).count()

    def get_ongoing_trade(self, value):
        """The total amount of cars in trade"""
        return Trade.objects.filter(trade_status=TradeStates.Ongoing).count()

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
