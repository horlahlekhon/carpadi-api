import datetime

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
    device_imei = models.CharField(max_length=20)
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

class Wallet(Base):
    balance = models.DecimalField(decimal_places=10, max_digits=16, editable=True)
    merchant = models.OneToOneField(
        CarMerchant,
        on_delete=models.CASCADE,
        related_name="wallet",
        help_text="merchant user wallet that holds monetary balances",
    )
    trading_cash = models.DecimalField(decimal_places=10, max_digits=16,
                                       editable=True)  # cash accross all pending trades
    withdrawable_cash = models.DecimalField(decimal_places=10, max_digits=16,
                                            editable=True)  # the money you can withdraw that is unattached to any trade
    unsettled_cash = models.DecimalField(decimal_places=10, max_digits=16,
                                         editable=True)  # money you requested to withdraw, i.e pending credit
    total_cash = models.DecimalField(decimal_places=10, max_digits=16, editable=True)  # accross all sections

    @transaction.atomic
    def update_balance(self, amount, transaction_type: TransactionTypes, transaction_kind: TransactionKinds):
        if transaction_type == TransactionTypes.Debit and transaction_kind == TransactionKinds.Withdrawal:
            self.balance -= amount
            self.withdrawable_cash -= amount
        elif transaction_type == TransactionTypes.Credit and transaction_kind == TransactionKinds.Deposit:
            self.balance += amount
            self.withdrawable_cash += amount
        self.save(update_fields=['balance', 'withdrawable_cash'])




class TransactionStatus(models.TextChoices):
    Success = "success", _("Success")
    Failed = "failed", _("Failed")
    Pending = "pending", _("Pending")





# Transactions
class Transaction(Base):
    amount = models.DecimalField(max_digits=10, decimal_places=4)
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE,
        related_name="merchant_transactions",
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
        "available",
    )
    Bought = "bought", _(
        "bought",
    )
    Sold = "sold", _(
        "sold",
    )


def validate_inspector(value: User):
    if not value.is_staff:
        raise ValidationError(
            _(f'user {value.username} is not an admin user'),
            params={'value': value},
        )


class Car(Base):
    brand = models.ForeignKey(CarBrand, on_delete=models.SET_NULL, null=True)
    status = models.CharField(choices=CarStates.choices, max_length=30)
    vin = models.CharField(max_length=17)
    pictures = models.URLField(help_text="url of the folder where the images for the car is located.")
    partitions = models.IntegerField(default=10, null=False, blank=False)
    car_inspector = models.OneToOneField(get_user_model(),
                                         on_delete=models.SET_NULL,
                                         null=True, blank=False, validators=[validate_inspector, ])
    cost = models.DecimalField(
        decimal_places=10,
        editable=False,
        max_digits=10,
        max_length=10,
        help_text="cost of  purchasing the car",
        null=False,
        blank=False,
    )
    cost_of_repairs = models.DecimalField(
        decimal_places=10,
        editable=False,
        max_digits=10,
        max_length=10,
        help_text="Total cost of spare parts",
        null=False,
        blank=False,
    )
    total_cost = models.DecimalField(
        decimal_places=10,
        editable=False,
        null=False,
        blank=False,
        max_digits=10,
        max_length=10,
        help_text="Total cost = cost + cost_of_repairs + maintainance_cost + misc",
    )
    maintainance_cost = models.DecimalField(
        decimal_places=10,
        editable=False,
        max_digits=10,
        max_length=10,
        help_text="fuel, parking, mechanic workmanship costs",
        null=False,
        blank=False,
    )
    resale_price = models.DecimalField(
        decimal_places=10, max_digits=10, max_length=10, help_text="price presented to merchants", null=True, blank=True
    )
    # TODO change to a full fledge model
    inspection_report = models.TextField()
    buy_to_sale_time = models.IntegerField(editable=False)
    margin = models.DecimalField(
        decimal_places=10,
        editable=False,
        max_digits=10,
        max_length=10,
        help_text="The profit that was made from car " "after sales in percentage of the total cost",
    )
    car_type = models.CharField(choices=CarTypes.choices, max_length=30, null=False, blank=False)


class SpareParts(Base):
    name = models.CharField(max_length=100)
    car_brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=10)


class CarMaintainanceTypes(models.TextChoices):
    SparePart = "spare_part", _("Car spare parts i.e brake.")
    Expense = "expense", _("other expenses made on the car that doesnt directly relate to a physical parts.")


class CarMaintainance(Base):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="maintanances")
    type = models.CharField(choices=CarMaintainanceTypes.choices, max_length=20)


class TradeStates(models.TextChoices):
    Pending = "pending", _("Pending review")
    Ongoing = "ongoing", _("Slots are yet to be fully bought")
    Completed = "completed", _("Car has been sold and returns sorted to merchants")
    Purchased = "purchased", _("All slots have been bought by merchants")


class Trade(Base):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="trades")
    slots_available = models.IntegerField(default=0)
    slots_purchased = models.IntegerField(default=0)
    return_on_trade = models.DecimalField(decimal_places=10, editable=False, max_digits=10, max_length=10)
    expected_return_on_trade = models.DecimalField(decimal_places=10, editable=False, max_digits=10, max_length=10)
    traded_slots = models.IntegerField(default=0)
    remaining_slots = models.IntegerField(default=0)
    total_slots = models.IntegerField(default=0)
    price_per_slot = models.DecimalField(decimal_places=10, editable=False, max_digits=10, max_length=10)
    trade_status = models.CharField(choices=TradeStates.choices, max_length=20)


class TradeUnit(Base):
    trade = models.ForeignKey(Trade, on_delete=models.CASCADE, related_name="units")
    merchant = models.ForeignKey(CarMerchant, on_delete=models.CASCADE, related_name="units")
    share_percentage = models.DecimalField(decimal_places=10, editable=False, max_digits=10, max_length=10)

class Disbursement(Base):
    trade_unit = models.ForeignKey(TradeUnit, on_delete=models.CASCADE, related_name="disbursement")
    amount = models.DecimalField(decimal_places=5, editable=False, max_digits=15)

class ActivityTypes(models.TextChoices):
    Transaction = "transaction", _("transaction")
    TradeUnit = "trade_unit", _("trade_unit")
    Disbursement = "disbursement", _("disbursement")

class Activity(Base):
    activity_type = models.CharField(choices=ActivityTypes.choices, max_length=15)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    activity = GenericForeignKey("content_type", "object_id")
