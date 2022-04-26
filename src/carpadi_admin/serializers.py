from dataclasses import fields
from decimal import Decimal
from pyexpat import model

from rest_framework import serializers, exceptions
from src.models.models import CarMerchant, Car, Wallet, Transaction, Trade, Disbursement, Activity, TradeStates, \
    TradeUnit, CarStates, CarMaintenance, CarMaintenanceTypes, SpareParts, MiscellaneousExpenses, DisbursementStates
from django.utils import timezone
from django.db.transaction import atomic
from django.db.models import Sum


class SocialSerializer(serializers.Serializer):
    """
    Serializer which accepts an OAuth2 access token.
    """

    access_token = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )


# class CarMerchantSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = CarMerchant
#         fields = "__all__"


class CarSerializer(serializers.ModelSerializer):
    maintenance_cost = serializers.SerializerMethodField()
    total_cost = serializers.SerializerMethodField()

    class Meta:
        model = Car
        fields = "__all__"
        ref_name = "car_serializer_admin"

    def get_total_cost(self, obj: Car):
        return obj.total_cost_calc()

    def get_maintenance_cost(self, obj: Car):
        return obj.maintenance_cost_calc()

    def validate_status(self, value):
        if self.instance:  # we are doing update
            if value == CarStates.Inspected:
                if not self.instance.inspection_report and not self.initial_data.get("inspection_report") and \
                        not self.instance.inspector and not self.initial_data.get("inspector"):
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

    @atomic()
    def create(self, validated_data):
        car = Car.objects.create(**validated_data)
        return car

    def update(self, instance: Car, validated_data):
        # car_merchant = validated_data.get("car_merchant", instance.car_merchant)
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


class CarSerializerField(serializers.PrimaryKeyRelatedField):

    def to_internal_value(self, data):
        car: Car = super().to_internal_value(data)
        if car.trade:
            raise serializers.ValidationError("This car is being traded already")
        return car


class TradeSerializerAdmin(serializers.ModelSerializer):
    remaining_slots = serializers.SerializerMethodField()
    # trade_status = serializers.SerializerMethodField()
    return_on_trade = serializers.SerializerMethodField()
    return_on_trade_percentage = serializers.SerializerMethodField()
    car = CarSerializerField(queryset=Car.objects.all())

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
            "price_per_slot"
        )
        extra_kwargs = {"car":
                            {"error_messages": {"required": "Car to trade on is required", "unique": "Car already "
                                                                                                     "traded"}}}

    def get_return_on_trade(self, obj: Trade):
        return obj.return_on_trade_calc()

    def get_return_on_trade_percentage(self, obj: Trade):
        return obj.return_on_trade_calc_percent()

    # def get_trade_status(self, obj: Trade):
    #     sum_of_slots = sum([unit.slots_quantity for unit in obj.units.all()])
    #     if obj.units.count() == obj.slots_available:
    #         return TradeStates.Purchased
    #     elif sum_of_slots >= 0 and obj.units.count() != obj.slots_available:
    #         return TradeStates.Ongoing
    #     else:
    #         raise exceptions.APIException("Error, cannot determine trade status")

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
                    raise serializers \
                        .ValidationError("Please add resale price to the car first before completing the trade")
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

    def create(self, validated_data):
        car: Car = validated_data["car"]
        price_per_slot = self.calculate_price_per_slot(car.resale_price, validated_data["slots_available"])
        return Trade.objects.create(slots_purchased=0, **validated_data, price_per_slot=price_per_slot)

    def complete_trade(self, trade: Trade):
        successful_disbursements = trade \
            .units \
            .annotate(is_disbursed="disbursement__disbursement_status") \
            .filter(is_disbursed=DisbursementStates.Completed).count()
        total_disbursed = trade.units \
            .annotate(total_disbursed=Sum('disbursements__amount')) \
            .aggregate(total_disbursed=Sum('total_disbursed')) \
            .get('total_disbursed')

        if successful_disbursements == trade.units.count() and total_disbursed == trade.total_payout():
            trade.trade_status = TradeStates.Closed
            trade.save(update_fields=["trade_status"])
            car: Car = trade.car
            car.update_on_sold()



    @atomic()
    def update(self, instance: Trade, validated_data):
        resp = super(TradeSerializerAdmin, self).update(instance, validated_data)
        if validated_data.get("trade_status") and validated_data.get("trade_status") == TradeStates.Completed:
            instance.run_disbursement()
            # check disbursements and update trade state
            self.complete_trade(instance)
        return resp


class DisbursementSerializerAdmin(serializers.ModelSerializer):
    class Meta:
        model = Disbursement
        fields = ("created", "id", "amount", "trade_unit")
        read_only_fields = ("created", "id", "amount", "trade_unit")


class ActivitySerializerAdmin(serializers.ModelSerializer):
    class Meta:
        model = Activity
        fields = ("created", "id", "activity_type", "object_id", "content_type", "description")
        read_only_fields = ("created", "id", "activity_type", "object_id", "content_type", "description")


class CarMaintenanceSerializerAdmin(serializers.ModelSerializer):
    spare_part_id = serializers.UUIDField(required=False)
    cost = serializers.DecimalField(required=False, help_text="Cost of the maintenance in case it is a misc expenses",
                                    max_digits=10, decimal_places=2)
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
            misc = MiscellaneousExpenses.objects.create(estimated_price=cost,
                                                        description=description, name=validated_data["name"])
            return CarMaintenance.objects.create(car=car, type=maintenance_type, cost=cost, maintenance=misc)
