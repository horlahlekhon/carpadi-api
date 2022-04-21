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
from django.db import transaction
from src.config.common import OTP_EXPIRY
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum


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
    WalletTransfer = "wallet_transfer", _("Wallet Transfer")
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
                                       editable=True)  # cash accross all pending trades
    withdrawable_cash = models.DecimalField(
        decimal_places=2, max_digits=16, editable=True
    )  # the money you can withdraw that is unattached to any trade
    unsettled_cash = models.DecimalField(
        decimal_places=2, max_digits=16, editable=True
    )  # money you requested to withdraw, i.e pending credit
    total_cash = models.DecimalField(decimal_places=2, max_digits=16, editable=True)  # accross all sections

    @transaction.atomic
    # TODO maybe we should do balance check here
    def update_balance(self, amount, transaction_type: TransactionTypes, transaction_kind: TransactionKinds):
        updated_fields = []
        if transaction_type == TransactionTypes.Debit and transaction_kind == TransactionKinds.Withdrawal:
            self.balance -= amount  # FIXME are we sure we arent drunk here.. what should we do if a withrdrawal is done
            self.withdrawable_cash -= amount
            updated_fields = ['balance', 'withdrawable_cash']
        elif transaction_type == TransactionTypes.Credit and transaction_kind == TransactionKinds.Deposit:
            self.balance += amount
            self.withdrawable_cash += amount
            updated_fields = ['balance', 'withdrawable_cash']
        elif transaction_type == TransactionTypes.Debit and transaction_kind == TransactionKinds.WalletTransfer:
            self.balance -= amount
            updated_fields = ['balance']
        else:
            raise ValueError(
                f"Invalid transaction type and kind combination {transaction_type} {transaction_kind}: Aborting"
            )
        self.save(update_fields=updated_fields)


class TransactionStatus(models.TextChoices):
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
            tx.wallet.update_balance(tx.amount, tx.transaction_type, tx.transaction_kind)
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


def validate_inspector(value: User):
    if not value.is_staff:
        raise ValidationError(
            _(f'user {value.username} is not an admin user'),
            params={'value': value},
        )


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
    pictures = models.URLField(help_text="url of the folder where the images for the car is located.", null=True,
                               blank=True)
    car_inspector = models.OneToOneField(
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


class Trade(Base):
    car = models.OneToOneField(Car, on_delete=models.CASCADE, related_name="trades")
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
    # traded_slots = models.IntegerField(default=0, help_text="number of slots that have been sold")
    # remaining_slots = models.PositiveIntegerField(default=0, help_text="slots that are still available for sale")
    # total_slots = models.IntegerField(default=10, help_text="total number of slots that are available for sale")
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

    def return_on_trade_calc(self):
        return self.car.resale_price - self.car.total_cost_calc()

    def return_on_trade_calc_percent(self):
        return self.return_on_trade_calc() / self.car.resale_price * 100

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

    def run_disbursement(self):
        if self.trade_status == TradeStates.Purchased:
            for unit in self.units.all():
                unit.disbursement()
        else:
            raise ValueError("Trade is not in purchased state")


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
    transaction = models.ForeignKey(Transaction, on_delete=models.PROTECT, related_name="trade_units", null=True,
                                    blank=True)

    class Meta:
        ordering = ["-slots_quantity"]

    def disbursement(self):
        return Disbursement.objects.create(self)


class DisbursementStates(models.TextChoices):
    Ongoing = "Ongoing"
    Completed = "Completed"


class Disbursement(Base):
    trade_unit = models.OneToOneField(TradeUnit, on_delete=models.CASCADE, related_name="trade_unit")
    amount = models.DecimalField(decimal_places=5, editable=False, max_digits=10)
    transaction = models.OneToOneField(Transaction, on_delete=models.PROTECT, related_name="disbursements", null=True,blank=True)
    disbursement_status = models.CharField(choices=DisbursementStates.choices, max_length=20, default=DisbursementStates.Ongoing)

    def save(self, *args, **kwargs):
        ref = f"cp-db-{self.id}"
        self.amount = self.trade_unit.estimated_rot
        self.transaction = Transaction.objects.create(
            wallet=self.trade_unit.merchant.wallet, amount=self.amount,
            transaction_type=TransactionTypes.Credit, transaction_reference=ref,
            transaction_status=TransactionStatus.Pending,
            transaction_kind=TransactionKinds.Disbursement)
        # TODO: initiate payment from flutterwave.. change the disbusement status
        #  to completed after payment is successful
        super().save(*args, **kwargs)


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
