import datetime
from decimal import Decimal
from email.policy import default
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.signal_handlers import generate_aliases_global
from easy_thumbnails.signals import saved_file
from model_utils.models import UUIDModel, TimeStampedModel
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.transaction import atomic

from src.carpadi_admin.utils import validate_inspector, checkout_transaction_validator, \
    disbursement_trade_unit_validator
from src.config.common import OTP_EXPIRY
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum
from rest_framework.exceptions import APIException

class Base(UUIDModel, TimeStampedModel):
    pass

    class Meta:
        abstract = True


class UserTypes(models.TextChoices):
    Admin = "admin", "admin"
    CarMerchant = "merchant", "merchant"


class User(AbstractUser, Base):
    username_validator = UnicodeUsernameValidator()
    profile_picture = models.URLField(blank=True, null=True)
    user_type = models.CharField(choices=UserTypes.choices, max_length=20)
    phone = models.CharField(max_length=15, unique=True, help_text="International format phone number")
    username = models.CharField(max_length=50, validators=[username_validator], unique=True, null=True)

    def get_tokens(self):
        refresh = RefreshToken.for_user(self)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def __str__(self):
        return self.username

    def is_merchant(self):
        return self.user_type == UserTypes.CarMerchant

    @staticmethod
    def update_last_login(user, **kwargs):
        """
        A signal receiver which updates the last_login date for
        the user logging in.
        """
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])
        LoginSessions.objects.create(device_imei=kwargs.get("device_imei"), user=user)


saved_file.connect(generate_aliases_global)


class LoginSessions(Base):
    device_imei = models.CharField(max_length=20, null=True, blank=True)
    user = models.ForeignKey(get_user_model(), models.CASCADE)


class OtpStatus(models.TextChoices):
    Verified = "verified", _("Otp verified by user successfully")
    FailedVerification = "failed", _("User entered wrong otp until disabled")
    Expired = "expired", _("Otp was not entered before it expired")
    Pending = "pending", _("Otp is yet to expire or has expired and no one sent a verification request for it")


class Otp(Base):
    otp = models.CharField(max_length=6, editable=False)
    expiry = models.DateTimeField(editable=False, default=timezone.now() + datetime.timedelta(minutes=OTP_EXPIRY))
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="otps")
    status = models.CharField(
        choices=OtpStatus.choices,
        max_length=20,
        default=OtpStatus.Pending,
        help_text="Keep track of weather " "the otp was later verified or expired or failed",
    )

    class Meta:
        get_latest_by = 'created'


class TransactionPinStatus(models.TextChoices):
    Expired = "expired", _("User already deleted device from device management")
    Active = "active", _("Transaction pin is still active")
    Deleted = "deleted", _("Transaction pin has been deleted")


class TransactionPin(Base):
    device_serial_number = models.CharField(max_length=50, unique=True)
    device_platform = models.CharField(max_length=20)
    status = models.CharField(max_length=10, choices=TransactionPinStatus.choices)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="transaction_pins")
    pin = models.CharField(max_length=200)
    device_name = models.CharField(max_length=50, help_text="The name of the device i.e Iphone x")


class CarMerchant(Base):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name="merchant")
    bvn = models.CharField(max_length=14, null=True, blank=False, default=None)

    # class Meta:


class TransactionTypes(models.TextChoices):
    Debit = "debit", _("Debit")
    Credit = "credit", _("Credit")


class TransactionKinds(models.TextChoices):
    Deposit = "deposit", _("Deposit")
    Withdrawal = "withdrawal", _("Withdrawal")
    Transfer = "transfer", _("Transfer")
    TradeUnitPurchases = "trade_unit_purchases", _("Wallet Deduction for trade unit purchases")
    Disbursement = "disbursement", _("Disbursement")


class Wallet(Base):
    balance = models.DecimalField(decimal_places=2, max_digits=16, editable=True)
    merchant = models.OneToOneField(
        CarMerchant,
        on_delete=models.CASCADE,
        related_name="wallet",
        help_text="merchant user wallet that holds monetary balances",
    )
    trading_cash = models.DecimalField(decimal_places=2, max_digits=16,
                                       editable=True)  # cash across all pending trades
    withdrawable_cash = models.DecimalField(
        decimal_places=2, max_digits=16, editable=True
    )  # the money you can withdraw that is unattached to any trade
    unsettled_cash = models.DecimalField(
        decimal_places=2, max_digits=16, editable=True
    )  # money you requested to withdraw, i.e pending credit
    total_cash = models.DecimalField(decimal_places=2, max_digits=16, editable=True)  # across all sections

    def get_unsettled_cash(self):
        """
        Right now unsettled cash are money used to
         buy a slot + the rot on the money when trade is in completed
         state because the money has not materialized for one reason or the other.
        """
        unsettled = Disbursement.objects \
                        .filter(disbursement_status=DisbursementStates.Unsettled, transaction__wallet=self) \
                        .aggregate(total=Sum("amount")) \
                        .get("total") or Decimal(0.00)
        return unsettled

    def get_trading_cash(self):
        trading = self.merchant.units \
                      .filter(trade__trade_status__in=(TradeStates.Purchased, TradeStates.Ongoing)) \
                      .aggregate(total=Sum("unit_value")).get("total") or Decimal(0.00)
        return trading


    def get_withdrawable_cash(self):
        return self.withdrawable_cash

    def get_total_cash(self):
        return self.get_trading_cash() + self.get_withdrawable_cash() + self.get_unsettled_cash()

    def update_balance(self, tx: "Transaction"):
        updated_fields_tx = []
        updated_fields_wallet = []
        if tx.transaction_kind == TransactionKinds.Deposit and tx.transaction_type == TransactionTypes.Credit:
            self.withdrawable_cash += tx.amount
            updated_fields_wallet.append("withdrawable_cash")
        #     FIXME we cant really determine the status of the transaction of withdrawal
        #      from here since there is third party integration. so we allow the caller to set it.
        elif tx.transaction_kind == TransactionKinds.Withdrawal and tx.transaction_type == TransactionTypes.Debit:
            balance_after_deduction = Decimal(0.0) if self.withdrawable_cash - tx.amount < 0 else self.withdrawable_cash - tx.amount
            self.withdrawable_cash = balance_after_deduction
            updated_fields_wallet.append("withdrawable_cash")
            tx.transaction_status = TransactionStatus.Pending
        elif tx.transaction_kind == TransactionKinds.Disbursement and tx.transaction_type == TransactionTypes.Credit:
            db: "Disbursement" = tx.disbursement
            if db.disbursement_status == DisbursementStates.Unsettled:
                balance_after_deduction = Decimal(0.0) if self.trading_cash - db.trade_unit.unit_value < 0 else self.trading_cash - db.trade_unit.unit_value
                self.unsettled_cash += tx.amount
                self.trading_cash = balance_after_deduction
                updated_fields_wallet = updated_fields_wallet + ["unsettled_cash", "trading_cash"]
                tx.transaction_status = TransactionStatus.Unsettled
            elif db.disbursement_status == DisbursementStates.Settled:
                balance_after_deduction = Decimal(0.0) if self.unsettled_cash - tx.amount < 0 else self.unsettled_cash - tx.amount
                self.withdrawable_cash += tx.amount
                self.unsettled_cash = balance_after_deduction
                updated_fields_wallet = updated_fields_wallet + ["withdrawable_cash", "unsettled_cash"]
                tx.transaction_status = TransactionStatus.Success
            else:
                raise ValidationError("Invalid disbursement status")
        elif tx.transaction_kind == TransactionKinds.TradeUnitPurchases and \
                tx.transaction_type == TransactionTypes.Debit:
            # self.trading_cash += tx.amount
            balance_after_deduction = Decimal(0.0)
            self.withdrawable_cash = Decimal(0.0) if self.withdrawable_cash - tx.amount < 0 else self.withdrawable_cash - tx.amount
            updated_fields_wallet.append("withdrawable_cash")
            tx.transaction_status = TransactionStatus.Success
        else:
            raise ValidationError("Invalid transaction type and kind combination")
        tx.save(update_fields=["transaction_status", ])
        self.save(update_fields=updated_fields_wallet)
        self.refresh_from_db()
        return self.save()


class TransactionStatus(models.TextChoices):
    Unsettled = "unsettled", _("Transaction that are yet to be resolved due"
                               " to a dispute or disbursement delay, typically pending credit")
    Success = "success", _("Success")
    Failed = "failed", _("Failed")
    Pending = "pending", _("Pending")


# Transactions
class Transaction(Base):
    amount = models.DecimalField(max_digits=10, decimal_places=4)
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="merchant_transactions",
        help_text="transactions carried out by merchant"
    )
    transaction_type = models.CharField(max_length=10, choices=TransactionTypes.choices)
    transaction_reference = models.CharField(max_length=50, null=False, blank=False)
    transaction_description = models.CharField(max_length=50, null=True, blank=True)
    transaction_status = models.CharField(max_length=10, choices=TransactionStatus.choices,
                                          default=TransactionStatus.Pending)
    transaction_response = models.JSONField(null=True, blank=True)
    transaction_kind = models.CharField(max_length=50, choices=TransactionKinds.choices,
                                        default=TransactionKinds.Deposit)
    transaction_payment_link = models.URLField(max_length=200, null=True, blank=True)

    @classmethod
    def verify_transaction(cls, response, tx):
        data = response.json()
        if response.status_code == 200 and data['status'] == 'success':
            tx.transaction_status = TransactionStatus.Success
            tx.transaction_response = data
            tx.save(update_fields=['transaction_status', 'transaction_response'])
            tx.wallet.update_balance(tx)
            return {"message": "Payment Successful"}, 200
        else:
            tx.transaction_status = TransactionStatus.Failed
            tx.transaction_response = data
            tx.save(update_fields=['transaction_status', 'transaction_response'])
            return {"message": "Payment Failed"}, 400


class BankAccount(Base):
    name = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=50)
    account_number = models.CharField(max_length=10)
    merchant = models.ForeignKey(
        CarMerchant, on_delete=models.CASCADE, related_name="bank_accounts",
        help_text="Bank account to remit merchant money to"
    )


class CarBrand(Base):
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()

    class Meta:
        unique_together = ("name", "model", "year")


class CarTypes(models.TextChoices):
    SUV = "suv", _(
        "suv",
    )
    SALOON = "saloon", _(
        "saloon",
    )
    MINIVAN = "minivan", _(
        "minivan",
    )
    Convertible = "convertible", _(
        "convertible",
    )
    MicroCar = "microcar", _(
        "microcar",
    )
    CityCar = "city_car", _(
        "City car",
    )
    Hatchback = "hatchback", _(
        "Hatchback",
    )
    Sedan = "sedan", _(
        "sedan",
    )
    FamilyCar = "family_car", _(
        "Family car",
    )
    MuscleCar = "muscle_car", _("Muscle car")
    Roadster = "roadstar", _(
        "Roadstar",
    )
    PickUp = "pickup", _(
        "pickup",
    )
    Coupe = "coupe", _(
        "coupe",
    )


class CarStates(models.TextChoices):
    FailedInspection = "failed_inspection", _(
        "Failed Inspection",
    )
    Inspected = "inspected", _(
        "inspected",
    )
    Available = "available", _(
        "available for trading and sale",
    )
    OngoingTrade = "ongoing_trade", _("Car is an ongoing trade")
    Bought = "bought", _(
        "bought",
    )
    Sold = "sold", _(
        "sold",
    )
    New = "new", _("New car waiting to be inspected")


class CarTransmissionTypes(models.TextChoices):
    Manual = "manual", _(
        "Manual",
    )
    Automatic = "automatic", _(
        "Automatic",
    )


class FuelTypes(models.TextChoices):
    Petrol = "petrol", _(
        "Petrol",
    )
    Diesel = "diesel", _(
        "Diesel",
    )
    CNG = "cng", _(
        "CNG",
    )
    LPG = "lpg", _(
        "LPG",
    )
    Electric = "electric", _(
        "Electric",
    )
    Hybrid = "hybrid", _(
        "Hybrid",
    )


class Car(Base):
    brand = models.ForeignKey(CarBrand, on_delete=models.SET_NULL, null=True)
    status = models.CharField(choices=CarStates.choices, max_length=30, default=CarStates.New)
    vin = models.CharField(max_length=17)
    # TODO try upload_to to upload to the car folder using ImageField
    pictures = models.URLField(help_text="url of the folder where the images for the car is located.", null=True,
                                 blank=True)
    car_inspector = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=False,
        validators=[
            validate_inspector,
        ],
    )
    colour = models.CharField(max_length=50)
    transmission_type = models.CharField(max_length=15, choices=CarTransmissionTypes.choices)

    offering_price = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        max_length=10,
        help_text="potential cost of  purchasing the car offered by the seller. "
                  "this should be changed to reflect the actual cost of the car when it is bought",
        validators=[MinValueValidator(Decimal(0.00))],
        default=Decimal(0.00),
    )
    cost_of_repairs = models.DecimalField(
        decimal_places=2,
        editable=False,
        max_digits=10,
        help_text="Total cost of spare parts",
        null=True, blank=True
    )
    total_cost = models.DecimalField(
        decimal_places=2,
        editable=False,
        null=True, blank=True,
        max_digits=10,
        help_text="Total cost = offering_price + cost_of_repairs + maintainance_cost + misc",
    )
    # maintainance_cost = models.DecimalField(
    #     decimal_places=2,
    #     editable=False,
    #     max_digits=10,
    #     help_text="fuel, parking, mechanic workmanship costs",
    #     null=True, blank=True
    # )
    resale_price = models.DecimalField(
        decimal_places=2, max_digits=10, max_length=10, help_text="price presented to merchants", null=True, blank=True
    )
    # TODO change to a full fledge model
    inspection_report = models.TextField(null=True, blank=True)
    margin = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        help_text="The profit that was made from car " "after sales in percentage of the total cost",
        null=True, blank=True
    )
    car_type = models.CharField(choices=CarTypes.choices, max_length=30, null=False, blank=False)
    fuel_type = models.CharField(choices=FuelTypes.choices, max_length=30, null=False, blank=False)
    mileage = models.IntegerField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)

    def maintenance_cost_calc(self):
        return self.maintenances.all().aggregate(sum=Sum("cost")).get("sum") or Decimal(0.00)

    def total_cost_calc(self):
        return self.offering_price + self.maintenance_cost_calc()

    def margin_calc(self):
        return self.total_cost_calc() - self.offering_price

    def update_on_sold(self):
        self.status = CarStates.Sold
        self.margin = self.margin_calc()
        self.save(update_fields=["status", "margin"])


class SpareParts(Base):
    name = models.CharField(max_length=100)
    car_brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2)


class MiscellaneousExpenses(Base):
    name = models.CharField(max_length=100)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, blank=True)


class CarMaintenanceTypes(models.TextChoices):
    SparePart = "spare_part", _("Car spare parts i.e brake.")
    Expense = "expense", _("other expenses made on the car that doesnt directly relate to a physical parts.")


class CarMaintenance(Base):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="maintenances", null=False, blank=False)
    type = models.CharField(choices=CarMaintenanceTypes.choices, max_length=20)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    maintenance = GenericForeignKey("content_type", "object_id")
    cost = models.DecimalField(max_digits=10, decimal_places=2,
                               help_text="cost of the maintenance a the time of the maintenance.. "
                                         "cost on the maintenance might change, i.e spare parts. "
                                         "the cost here is the correct one to use when calculating "
                                         "total cost of car maintenance")


class TradeStates(models.TextChoices):
    Pending = "pending", _("Pending review")
    Ongoing = "ongoing", _("Slots are yet to be fully bought")
    Completed = "completed", _("Car has been sold and returns sorted to merchants")
    Purchased = "purchased", _("All slots have been bought by merchants")
    Closed = "closed", _("All slots have been bought by merchants, car has been sold and disbursements made")


class Trade(Base):
    car = models.OneToOneField(Car, on_delete=models.CASCADE, related_name="trade")
    slots_available = models.PositiveIntegerField(default=0)
    # slots_purchased = models.PositiveIntegerField(default=0)
    return_on_trade = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        default=Decimal(0.00),
        validators=[MinValueValidator(Decimal(0.00))], help_text="The actual profit that was made from car ",
    )
    estimated_return_on_trade = models.DecimalField(
        decimal_places=2, default=Decimal(0.00), validators=[MinValueValidator(Decimal(0.00))], max_digits=10,
        help_text="The estimated profit that can be made from car sale"
    )
    price_per_slot = models.DecimalField(
        decimal_places=2,
        editable=False,
        validators=[MinValueValidator(Decimal(0.00))],
        max_digits=10,
        default=Decimal(0.00),
        help_text="price per slot",
    )
    trade_status = models.CharField(choices=TradeStates.choices, default=TradeStates.Ongoing, max_length=20)
    min_sale_price = models.DecimalField(
        validators=[MinValueValidator(Decimal(0.00))],
        decimal_places=2,
        max_digits=10,
        default=Decimal(0.00),
        help_text="min price at which the car " "can be sold",
    )
    max_sale_price = models.DecimalField(
        validators=[MinValueValidator(Decimal(0.00))],
        decimal_places=2,
        max_digits=10,
        default=Decimal(0.00),
        help_text="max price at which the car " "can be sold",
    )
    bts_time = models.IntegerField(default=0, help_text="time taken to buy to sale in days")
    date_of_sale = models.DateField(null=True, blank=True)

    @property
    def resale_price(self):
        return self.car.resale_price if self.car.resale_price else self.min_sale_price

    def return_on_trade_calc(self):
        return self.resale_price - self.car.total_cost_calc()

    def return_on_trade_calc_percent(self):
        return self.return_on_trade_calc() / self.resale_price * 100

    def return_on_trade_per_slot(self):
        return self.return_on_trade_calc() / self.slots_available

    def return_on_trade_per_slot_percent(self):
        return self.return_on_trade_calc_percent() / self.slots_available

    def slots_purchased(self):
        # TODO: this is a hack, fix it using annotations
        slots_purchased = sum([unit.slots_quantity for unit in self.units.all()])
        return slots_purchased

    def remaining_slots(self):
        slots_purchased = sum([unit.slots_quantity for unit in self.units.all()])
        return self.slots_available - slots_purchased

    def total_payout(self):
        """
        Total payout for the trade. cummulative of
        total amount of initial investment i.e trade_unit.unit_value
        and total amount of return on trade i.e trade_unit.return_on_trade
        across all units
        """
        total_unit_value = self.units.aggregate(total=Sum('unit_value')).get('total')
        if not total_unit_value:
            raise APIException(detail="No units have been sold yet")
        return (self.return_on_trade_per_slot() * self.slots_available) + total_unit_value

    def run_disbursement(self):
        if self.trade_status == TradeStates.Purchased:
            for unit in self.units.all():
                unit.disburse()
        else:
            raise ValueError("Trade is not in completed state")

    @atomic()
    def close(self):
        units = self.units.all()
        for unit in units:
            unit.disbursement.settle()
        self.trade_status = TradeStates.Closed
        self.save(update_fields=["trade_status"])
        return None


class TradeUnit(Base):
    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, related_name="units")
    merchant = models.ForeignKey(CarMerchant, on_delete=models.CASCADE, related_name="units")
    share_percentage = models.DecimalField(
        decimal_places=2,
        editable=False,
        default=Decimal(0.00),
        max_digits=10,
        help_text="the percentage of this unit in the trade",
    )
    slots_quantity = models.PositiveIntegerField(default=1)
    unit_value = models.DecimalField(
        decimal_places=2,
        editable=False,
        default=Decimal(0.00),
        max_digits=10,
        help_text="The amount to be paid given the slots quantity x trade.price_per_slot",
    )
    vat_percentage = models.DecimalField(
        null=True,
        blank=True,
        decimal_places=2,
        editable=False,
        default=Decimal(0.00),
        max_digits=10,
        help_text="the percentage of vat to be paid. calculated in relation to share " "percentage of tradeUnit in trade",
    )
    estimated_rot = models.DecimalField(
        decimal_places=2,
        editable=False,
        validators=[MinValueValidator(Decimal(0.00))],
        max_digits=10,
        default=Decimal(0.00),
        help_text="the estimated return on trade",
    )
    buy_transaction = models.ForeignKey(
        Transaction, on_delete=models.PROTECT,
        related_name="trade_units_buy", null=False, blank=False, help_text="the transaction that bought this unit")
    checkout_transaction = models.ForeignKey(
        Transaction, on_delete=models.PROTECT,
        related_name="trade_units_checkout",
        null=True, blank=True, validators=[MinValueValidator(Decimal(0.00)), checkout_transaction_validator],
        help_text="the transaction that materialized out this unit")

    class Meta:
        ordering = ["-slots_quantity"]

    def disburse(self):
        disbursement = Disbursement.objects \
            .create(trade_unit=self,
                    disbursement_status=DisbursementStates.Unsettled,
                    amount=self.trade.return_on_trade_per_slot() * self.slots_quantity + self.unit_value)
        return disbursement
        # self.checkout_transaction = disbursement.transaction


class DisbursementStates(models.TextChoices):
    Ongoing = "Ongoing"
    Completed = "Completed"
    Unsettled = "Unsettled", _("Unsettled. The disbursement has been created but not yet settled by the admin")
    Settled = "Settled", _("Settled. The disbursement has been settled by the admin")


class Disbursement(Base):
    trade_unit = models.OneToOneField(
        TradeUnit, on_delete=models.CASCADE, related_name="disbursement",
        validators=[disbursement_trade_unit_validator],
        help_text="the trade unit that this disbursement is for")
    amount = models.DecimalField(decimal_places=5, editable=False, max_digits=10)
    transaction = models.OneToOneField(Transaction, on_delete=models.PROTECT, related_name="disbursement", null=True,
                                       blank=True)
    disbursement_status = models.CharField(choices=DisbursementStates.choices, max_length=20,
                                           default=DisbursementStates.Unsettled)

    def settle(self):
        if self.disbursement_status == DisbursementStates.Unsettled:
            self.disbursement_status = DisbursementStates.Settled
            self.save(update_fields=["disbursement_status"])
            self.transaction.wallet.update_balance(self.transaction)
            return True
        raise ValueError("Disbursement is not in unsettled state, so why are you tryna settle it?")

    def __str__(self):
        return f"Disbursement for {self.trade_unit.trade.id} - {self.trade_unit.merchant.user.username}"

    def __repr__(self):
        return f"<Disbursement(trade_unit={self.trade_unit.id}, " \
               f"amount={self.amount}, status={self.disbursement_status}, transaction={self.transaction.id})> "

    def save(self, *args, **kwargs):
        if self._state.adding:
            ref = f"cp-db-{self.id}"
            self.transaction = Transaction.objects.create(
                wallet=self.trade_unit.merchant.wallet, amount=self.amount,
                transaction_type=TransactionTypes.Credit, transaction_reference=ref,
                transaction_status=TransactionStatus.Unsettled,
                transaction_kind=TransactionKinds.Disbursement)
            self.transaction.wallet \
                .update_balance(self.transaction)
        return super().save(*args, **kwargs)


class ActivityTypes(models.TextChoices):
    Transaction = "transaction", _("transaction")
    TradeUnit = "trade_unit", _("trade_unit")
    Disbursement = "disbursement", _("disbursement")


class Activity(Base):
    activity_type = models.CharField(choices=ActivityTypes.choices, max_length=15)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    activity = GenericForeignKey("content_type", "object_id")
    description = models.TextField(default="")



class CarProduct(Base):
    car = models.OneToOneField(Car, on_delete=models.CASCADE, related_name="product")
    selling_price = models.DecimalField(decimal_places=5, editable=False, max_digits=10)
    highlights = models.ForeignKey(CarFeature, on_delete=models.CASCADE)
    sales_image = models.URLField(help_text="url of the folder where the sales images for the car is located.", blank=True)


class CarFeature(Base):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="feature")
    name = models.CharField(max_length=100)
    image = models.URLField(help_text="url of the folder where the feature image for the car is located.", blank=True)