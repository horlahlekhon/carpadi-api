from dataclasses import fields
from decimal import Decimal

from src.models.models import CarMerchant, Car, Wallet, Transaction, Trade, Disbursement, Activity, SpareParts, \
    CarProduct, CarFeature, CarStates, CarMaintenance, MiscellaneousExpenses, CarMaintenanceTypes, TradeStates, \
    DisbursementStates
from rest_framework import serializers
from django.db.transaction import atomic
from django.utils import timezone
from django.db.models import Sum
from rest_framework import exceptions


class SocialSerializer(serializers.Serializer):
    """
    Serializer which accepts an OAuth2 access token.
    """

    access_token = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )


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
            "price_per_slot"
        )
        extra_kwargs = {"car":
                            {"error_messages": {"required": "Car to trade on is required", "unique": "Car already "
                                                                                                     "traded"}}}

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
                    raise serializers \
                        .ValidationError("Please add resale price to the car first before completing the trade")
                if trade.trade_status != TradeStates.Purchased:
                    raise serializers.ValidationError(
                        "Cannot change trade status to {}, trade is {}".format(attr, trade.trade_status))
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
        car: Car = validated_data["car"]
        price_per_slot = self.calculate_price_per_slot(car.resale_price, validated_data["slots_available"])
        return Trade.objects.create(**validated_data, price_per_slot=price_per_slot)

    def complete_trade(self, trade: Trade):
        """
        Completes the trade by setting the trade status to completed and updating the car status.
        we also try to do some validation to make sure trade and its corresponding objects are valid
        :param trade: Trade object
        """
        successful_disbursements = trade \
            .units \
            .filter(disbursement__disbursement_status=DisbursementStates.Unsettled).count()
        query = trade.units.annotate(total_disbursed=Sum('disbursement__amount'))
        total_disbursed = query.aggregate(sum=Sum('total_disbursed')).get('sum') or Decimal(0)
        if successful_disbursements == trade.units.count() and total_disbursed == trade.total_payout():
            car: Car = trade.car
            car.update_on_sold()
        else:
            raise exceptions.APIException("Error, cannot complete trade, because calculated"
                                          " payout seems to be unbalanced with the disbursements")

    @atomic()
    def update(self, instance: Trade, validated_data):
        if instance.trade_status == TradeStates.Closed:
            raise serializers.ValidationError("Cannot update a closed trade.. Geez!!")
        if validated_data.get("trade_status") and validated_data.get("trade_status") == TradeStates.Completed:
            instance.run_disbursement()
            # check disbursements and update trade state
            self.complete_trade(instance)
        return super(TradeSerializerAdmin, self).update(instance, validated_data)


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


class SparePartsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpareParts
        fields = "__all__"


class CarFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarFeature
        fields = "__all__"


class CarProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarProduct
        fields = "__all__"
