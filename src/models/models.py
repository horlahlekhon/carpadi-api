import contextlib
import datetime
import uuid
from decimal import Decimal
from typing import List

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, EmailValidator
from django.db import models
from django.db.models import Sum, Q
from django.db.transaction import atomic
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.signal_handlers import generate_aliases_global
from easy_thumbnails.signals import saved_file
from model_utils.models import UUIDModel, TimeStampedModel
from rest_framework import exceptions
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.tokens import RefreshToken

from src.carpadi_admin.utils import validate_inspector, checkout_transaction_validator, \
    disbursement_trade_unit_validator
from src.config.common import OTP_EXPIRY
import logging
from src.models.validators import PhoneNumberValidator, LicensePlateValidator

logger = logging.getLogger(__name__)


class InspectionStatus(models.TextChoices):
    Ongoing = "ongoing", _("Ongoing inspection")
    Completed = "completed", _("Completed inspection")
    Pending = "pending", _("New inspection")
    Expired = "expired", _("Inspection has been scheduled for" " more than a week without being ongoing or completed")


class Base(UUIDModel, TimeStampedModel):
    pass

    class Meta:
        abstract = True
        ordering = ('-created',)
        get_latest_by = "created"


class UserTypes(models.TextChoices):
    Admin = "admin", _(
        "admin",
    )
    CarMerchant = "merchant", _(
        "merchant",
    )
    CarSeller = "car_seller", _(
        "Car seller",
    )


class User(AbstractUser, Base):
    username_validator = UnicodeUsernameValidator()
    profile_picture = models.OneToOneField("Assets", on_delete=models.SET_NULL, null=True, blank=True)
    user_type = models.CharField(choices=UserTypes.choices, max_length=20)
    phone = models.CharField(
        max_length=15,
        unique=True,
        help_text="International format phone number",
        error_messages={
            'unique': _("A user with that phone number already exists."),
        },
    )
    username = models.CharField(max_length=50, validators=[username_validator], unique=True, null=True)
    email = models.EmailField(
        _('email address'),
        blank=False,
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        },
    )

    def get_tokens(self, imei):
        #  the token here doesnt container IMEI
        token = RefreshToken.for_user(self)
        token["device_imei"] = imei
        return {
            'refresh': str(token),
            'access': str(token.access_token),
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
    device_imei = models.CharField(max_length=100, null=True, blank=True)
    user = models.ForeignKey(get_user_model(), models.CASCADE)


class OtpStatus(models.TextChoices):
    Verified = "verified", _("Otp verified by user successfully")
    FailedVerification = "failed", _("User entered wrong otp until disabled")
    Expired = "expired", _("Otp was not entered before it expired")
    Pending = "pending", _("Otp is yet to expire or has expired and no one sent a verification request for it")


class OtpTypes(models.TextChoices):
    ConfirmUser = "conform_user"
    PasswordReset = "password_reset"


class Otp(Base):
    otp = models.CharField(max_length=6, editable=False)
    expiry = models.DateTimeField(editable=False, default=timezone.now() + datetime.timedelta(minutes=OTP_EXPIRY))
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="otps", null=True, blank=True)
    status = models.CharField(
        choices=OtpStatus.choices,
        max_length=20,
        default=OtpStatus.Pending,
        help_text="Keep track of weather " "the otp was later verified or expired or failed",
    )
    email = models.EmailField(null=True, blank=True, max_length=255)
    phone = models.CharField(null=True, blank=True, max_length=20)
    type = models.CharField(choices=OtpTypes.choices, default=OtpTypes.ConfirmUser, max_length=20)

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

    class Meta:
        unique_together = ('device_serial_number', 'pin')


class UserStatusFilterChoices(models.TextChoices):
    ActivelyTrading = "actively_trading", _("user is an active trading user")
    NotActivelyTrading = "not_actively_trading", _("user is not actively trading")


class MerchantStatusChoices(models.TextChoices):
    Disapproved = "disapproved", _("User approval was declined")
    Pending = "pending", _(" User is pending approval")
    Approved = "approved", _("User has been approved")


class CarMerchant(Base):
    user: User = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name="merchant")
    bvn = models.CharField(max_length=14, null=True, blank=False, default=None)
    phone_verified = models.BooleanField(default=False, null=False, blank=False)
    email_verified = models.BooleanField(default=False, null=False, blank=False)
    status = models.CharField(
        default=MerchantStatusChoices.Pending, null=False, blank=False, choices=MerchantStatusChoices.choices,
        max_length=30
    )

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.create_wallet()
        self.phone_verified = True
        super(CarMerchant, self).save(*args, **kwargs)

    def create_wallet(self):
        Wallet.objects.get_or_create(
            merchant=self,
            balance=Decimal(0),
            trading_cash=Decimal(0),
            withdrawable_cash=Decimal(0),
            unsettled_cash=Decimal(0),
            total_cash=Decimal(0),
        )


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
    trading_cash = models.DecimalField(decimal_places=2, max_digits=16, editable=True)  # cash across all pending trades
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
        unsettled = Disbursement.objects.filter(
            disbursement_status=DisbursementStates.Unsettled, transaction__wallet=self
        ).aggregate(total=Sum("amount")).get("total") or Decimal(0.00)
        return unsettled

    def get_trading_cash(self):
        trading = self.merchant.units.filter(
            trade__trade_status__in=(TradeStates.Purchased, TradeStates.Ongoing)).aggregate(
            total=Sum("unit_value")
        ).get("total") or Decimal(0.00)
        return trading

    def get_withdrawable_cash(self):
        return self.withdrawable_cash

    def get_total_cash(self):
        return self.get_trading_cash() + self.get_withdrawable_cash() + self.get_unsettled_cash()

    @atomic()
    def update_balance(self, tx: "Transaction"):
        update = WalletBalanceUpdate(tx, self)
        return update.resolve()


class WalletBalanceUpdate:
    def __init__(self, transaction: "Transaction", wallet: "Wallet"):

        self.tx = transaction
        self.wallet = wallet
        self._updated_fields_wallet = []

    def resolve(self):
        if (
                self.tx.transaction_kind == TransactionKinds.Deposit
                and self.tx.transaction_type == TransactionTypes.Credit
                and self.tx.transaction_status == TransactionStatus.Success
        ):
            self.wallet.withdrawable_cash += self.tx.amount
            self._updated_fields_wallet.append("withdrawable_cash")
        elif self.tx.transaction_kind == TransactionKinds.Withdrawal and self.tx.transaction_type == TransactionTypes.Debit:
            self.handle_withdrawals()
        elif self.tx.transaction_kind == TransactionKinds.Disbursement and self.tx.transaction_type == TransactionTypes.Credit:
            self.handle_disbursement()
        elif (
                self.tx.transaction_kind == TransactionKinds.TradeUnitPurchases and self.tx.transaction_type == TransactionTypes.Debit
        ):
            self.handle_unit_purchase()
        else:
            raise ValidationError("Invalid transaction type and kind combination")
        self.tx.save(update_fields=["transaction_status"])
        self.wallet.save(update_fields=self._updated_fields_wallet)
        self.wallet.refresh_from_db()
        return self.wallet

    def handle_withdrawals(self):
        assert self.tx.transaction_status == TransactionStatus.Success, "Balance cannot be updated on unsuccessful transaction"
        balance_after_deduction = (
            Decimal(
                0.0) if self.wallet.withdrawable_cash - self.tx.amount < 0 else self.wallet.withdrawable_cash - self.tx.amount
        )
        self.wallet.withdrawable_cash = balance_after_deduction
        self._updated_fields_wallet.append("withdrawable_cash")

    def handle_unit_purchase(self):
        assert self.tx.transaction_status == TransactionStatus.Success, "Balance cannot be updated on unsuccessful transaction"
        self.wallet.withdrawable_cash = (
            Decimal(
                0.0) if self.wallet.withdrawable_cash - self.tx.amount < 0 else self.wallet.withdrawable_cash - self.tx.amount
        )
        self.wallet.trading_cash += self.tx.amount
        self._updated_fields_wallet.extend(["withdrawable_cash", "trading_cash"])
        self.tx.transaction_status = TransactionStatus.Success

    def handle_disbursement(self):
        assert self.tx.transaction_status in (
            TransactionStatus.Success,
            TransactionStatus.RolledBack,
            TransactionStatus.Unsettled,
        ), "Balance cannot be updated on unsuccessful transaction"
        db: "Disbursement" = self.tx.disbursement
        if db.disbursement_status == DisbursementStates.Unsettled:
            balance_after_deduction = (
                Decimal(0.0)
                if self.wallet.trading_cash - db.trade_unit.unit_value < 0
                else self.wallet.trading_cash - db.trade_unit.unit_value
            )
            self.wallet.unsettled_cash += self.tx.amount
            self.wallet.trading_cash = balance_after_deduction
            self._updated_fields_wallet += ["unsettled_cash", "trading_cash"]
            self.tx.transaction_status = TransactionStatus.Unsettled
        elif db.disbursement_status == DisbursementStates.Settled:
            balance_after_deduction = (
                Decimal(
                    0.0) if self.wallet.unsettled_cash - self.tx.amount < 0 else self.wallet.unsettled_cash - self.tx.amount
            )
            self.wallet.withdrawable_cash += self.tx.amount
            self.wallet.unsettled_cash = balance_after_deduction
            self._updated_fields_wallet += ["withdrawable_cash", "unsettled_cash"]
            self.tx.transaction_status = TransactionStatus.Success
        elif db.disbursement_status == DisbursementStates.RolledBack:
            self.wallet.trading_cash = db.trade_unit.unit_value
            self.wallet.unsettled_cash = self.wallet.unsettled_cash - db.amount
            self.tx.transaction_status = TransactionStatus.RolledBack
            self._updated_fields_wallet += ["unsettled_cash", "trading_cash"]
        else:
            raise ValidationError("Invalid disbursement status")


class TransactionStatus(models.TextChoices):
    Unsettled = "unsettled", _(
        "Transaction that are yet to be resolved due" " to a dispute or disbursement delay, typically pending credit"
    )
    Success = "success", _("Success")
    Failed = "failed", _("Failed")
    Cancelled = "cancelled", _("Payment cancelled by user")
    Pending = "pending", _("Pending")
    RolledBack = "rollback", _(" Rolled back disbursement transaction")


# Transactions
class Transaction(Base):
    amount = models.DecimalField(max_digits=30, decimal_places=10)
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="merchant_transactions",
        help_text="transactions carried out by merchant"
    )
    transaction_type = models.CharField(max_length=10, choices=TransactionTypes.choices)
    transaction_reference = models.CharField(max_length=50, null=False, blank=False)
    transaction_description = models.CharField(max_length=50, null=True, blank=True)
    transaction_status = models.CharField(max_length=10, choices=TransactionStatus.choices,
                                          default=TransactionStatus.Pending)
    transaction_response = models.JSONField(null=True, blank=True,
                                            help_text="Transaction response from payment gateway")
    transaction_kind = models.CharField(max_length=50, choices=TransactionKinds.choices,
                                        default=TransactionKinds.Deposit)
    transaction_payment_link = models.URLField(max_length=200, null=True, blank=True)
    transaction_fees = models.DecimalField(
        max_digits=10, decimal_places=4, default=0.0, help_text="Transaction fees for withdrawal transactions"
    )

    @classmethod
    def verify_deposit(cls, response, tx):
        data = response.json()
        resp = None
        if response.status_code == 200 and (data['status'] in ('success', "successful", 'SUCCESSFUL')):
            tx.transaction_status = TransactionStatus.Success
            tx.transaction_response = data
            tx.save(update_fields=['transaction_status', 'transaction_response'])
            tx.wallet.update_balance(tx)
            resp = {"message": "Payment Successful"}, 200
        else:
            tx.transaction_status = TransactionStatus.Failed
            tx.transaction_response = data
            tx.save(update_fields=['transaction_status', 'transaction_response'])
            resp = {"message": "Payment Failed"}, 400
        tx.refresh_from_db()
        cls.notify_on_transaction(tx)
        return resp

    @classmethod
    def notify_on_transaction(cls, transaction: "Transaction"):
        activity = Activity.objects.create(
            activity_type=ActivityTypes.Transaction,
            activity=transaction,
            description=f"Activity Type: Transaction, Status: {transaction.transaction_status},"
                        f" Description: {transaction.transaction_kind} of {transaction.amount} naira.",
            merchant=transaction.wallet.merchant,
        )
        Notifications.objects.create(
            notice_type=NotificationTypes.TransactionCompleted
            if transaction.transaction_status == TransactionStatus.Success
            else NotificationTypes.TransactionFailed,
            entity_id=transaction.id,
            user=transaction.wallet.merchant.user,
            message=f"Transaction {transaction.transaction_kind} of {transaction.amount} naira has {transaction.transaction_status}.",
            is_read=False,
        )


class Banks(Base):
    bank_name = models.CharField(max_length=50, null=True, blank=True)
    bank_code = models.CharField(max_length=10, null=False, blank=False)
    bank_id = models.CharField(max_length=50, null=False, blank=False)

    def __str__(self):
        return self.bank_name

    def __repr__(self):
        return f"<Bank(bank_name={self.bank_name}, bank_code={self.bank_code})>"

    class Meta:
        unique_together = ('bank_name', 'bank_code')

    # def __eq__(self, other):
    #     return self.bank_name == other.bank_name and self.bank_code == other.bank_code


class BankAccount(Base):
    name = models.CharField(max_length=100, null=True, blank=True, help_text="An alias for the bank account")
    bank = models.ForeignKey(Banks, on_delete=models.CASCADE, related_name="bank_accounts")
    account_number = models.CharField(max_length=50, null=False, blank=False)
    merchant = models.ForeignKey(
        CarMerchant, on_delete=models.CASCADE, related_name="bank_accounts",
        help_text="Bank account to remit merchant money to"
    )
    is_default = models.BooleanField(default=False)


class CarBrand(Base):
    name = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()

    class Meta:
        unique_together = ("name", "model", "year")


class CarTypes(models.TextChoices):
    SUV = "suv", _(
        "SUV",
    )
    SALOON = "saloon", _(
        "Saloon",
    )
    MINIVAN = "minivan", _(
        "Minivan",
    )
    Convertible = "convertible", _(
        "Convertible",
    )
    Hatchback = "hatchback", _(
        "Hatchback",
    )

    PickUp = "pickup", _(
        "Pickup",
    )
    Coupe = "coupe", _(
        "Coupe",
    )

    def seats(self):
        if self.value == "coupe":
            return dict(seats_min=2, seats_max=4)
        elif self.value == "pickup":
            return dict(seats_min=2, seats_max=5)
        elif self.value in ("hatchback", "saloon"):
            return dict(seats_min=4, seats_max=5)
        elif self.value == "convertible":
            return dict(seats_min=2, seats_max=5)
        elif self.value in ("minivan", "suv"):
            return dict(seats_min=5, seats_max=7)
        else:
            raise TypeError(f"Invalid enum value for cartype: {self.value}")

    def to_dict(self):
        return dict(type=self.title(), **self.seats())

    @classmethod
    def to_array(cls):
        return [CarTypes(i[0]).to_dict() for i in CarTypes.choices]

    def __str__(self):
        return self.value


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
    PendingInspection = "pending_inspection", _("Inspection is yet to be started but has been assigned")
    OngoingInspection = "ongoing_inspection", _("Being inspected")
    New = "new", _("New car waiting to be inspected")

    Archived = "archived", _("Archived")


class CarTransmissionTypes(models.TextChoices):
    Manual = "manual", _(
        "Manual",
    )
    Automatic = "automatic", _(
        "Automatic",
    )
    Standard = "standard", _("Who knows")


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
    information = models.ForeignKey("VehicleInfo", on_delete=models.PROTECT, null=True)
    status = models.CharField(choices=CarStates.choices, null=True, max_length=30, default=CarStates.New)
    vin = models.CharField(max_length=17)
    pictures = GenericRelation("Assets")
    colour = models.CharField(max_length=50)
    bought_price = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        max_length=10,
        null=True,
        help_text="potential cost of  purchasing the car offered by the seller. "
                  "this should be changed to reflect the actual cost of the car when it is bought",
        validators=[MinValueValidator(Decimal(0.00))],
        default=Decimal(0.00),
    )
    cost_of_repairs = models.DecimalField(
        decimal_places=2, editable=False, max_digits=10, help_text="Total cost of spare parts", null=True, blank=True
    )
    total_cost = models.DecimalField(
        decimal_places=2,
        editable=False,
        null=True,
        blank=True,
        max_digits=10,
        help_text="Total cost = bought_price + cost_of_repairs + maintenance_cost + misc",
    )
    resale_price = models.DecimalField(
        decimal_places=2, max_digits=10, max_length=10, help_text="price presented to merchants", null=True, blank=True
    )
    margin = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        help_text="The profit that was made from car " "after sales in percentage of the total cost",
        null=True,
        blank=True,
    )
    description = models.TextField(null=True, blank=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    licence_plate = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        validators=[
            LicensePlateValidator,
        ],
    )

    def is_editable(self) -> bool:
        """
        figure out if this car should be editable
        a car cannot be editable if it has a completed or inactive trade attached.
        i.e a new car that has not be placed on trade
        """
        try:
            trade = self.trade
            disabled_states = TradeStates.Completed, TradeStates.Closed
            return trade.trade_status not in disabled_states
        except Exception:
            return True

    def maintenance_cost_calc(self):
        return sum(i.cost() for i in self.maintenances.all()) or Decimal(0.00)

    def total_cost_calc(self):
        return self.bought_price + self.maintenance_cost_calc()

    def margin_calc(self):
        return self.resale_price - self.total_cost_calc() if self.resale_price else None

    def update_on_sold(self):
        self.status = CarStates.Sold
        self.margin = self.margin_calc()
        self.total_cost = self.total_cost_calc()
        self.cost_of_repairs = self.maintenance_cost_calc()
        self.save(update_fields=["status", "margin", "total_cost", "cost_of_repairs"])

    def update_on_inspection_changes(self, inspection: "Inspections"):
        # if inspection.status == InspectionStatus.Completed and self.bought_price > Decimal(0.00):
        #     self.status = CarStates.Available
        # elif inspection.status == InspectionStatus.Completed:
        #     self.status = CarStates.Inspected
        # elif inspection.status == InspectionStatus.Ongoing:
        #     self.status = CarStates.OngoingInspection
        # elif inspection.status == InspectionStatus.Pending:
        #     self.status = CarStates.PendingInspection
        # else:
        #     self.status = CarStates.FailedInspection
        self.status = CarStates.Inspected  # inspection processing have been disabled for now
        self.save(update_fields=["status"])

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.vin = self.information.vin
            self.name = f"{self.information.brand.name}" f" {self.information.brand.model} {self.information.brand.year}"
        super().save(*args, **kwargs)


class SpareParts(Base):
    name = models.CharField(max_length=100)
    car_brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2)
    repair_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal(0.00))

    # class Meta:
    #     unique_together = ('name', 'car_brand')

    @property
    def cost(self) -> Decimal:
        return Decimal(self.estimated_price) + Decimal(self.repair_cost)


class MiscellaneousExpenses(Base):
    name = models.CharField(max_length=100)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, blank=True)

    @property
    def cost(self):
        return self.estimated_price


class CarMaintenanceTypes(models.TextChoices):
    SparePart = "spare_part", _("Car spare parts i.e brake.")
    Expense = "expense", _("other expenses made on the car that doesnt directly relate to a physical parts.")


class CarMaintenance(Base):
    car = models.ForeignKey(Car, on_delete=models.CASCADE, related_name="maintenances", null=False, blank=False)
    type = models.CharField(choices=CarMaintenanceTypes.choices, max_length=20)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.UUIDField(null=True, blank=True)
    maintenance = GenericForeignKey("content_type", "object_id")

    # cost = models.DecimalField(
    #     max_digits=10,
    #     decimal_places=2,
    #     help_text="cost of the maintenance a the time of the maintenance.. "
    #     "cost on the maintenance might change, i.e spare parts. "
    #     "the cost here is the correct one to use when calculating "
    #     "total cost of car maintenance",
    # )

    def cost(self):
        return self.maintenance.cost


class TradeStates(models.TextChoices):
    Pending = "pending", _("Pending review")
    Ongoing = "ongoing", _("Slots are yet to be fully bought")
    Completed = "completed", _("Car has been sold and returns sorted to merchants")
    Purchased = "purchased", _("All slots have been bought by merchants")
    Closed = "closed", _("All slots have been bought by merchants, car has been sold and disbursements made")
    Expired = "expired", _(
        "An expired trade has passed the specified " "trading duration and all money will be returned to the users",
    )


class Trade(Base):
    car = models.OneToOneField(Car, on_delete=models.CASCADE, related_name="trade")
    slots_available = models.PositiveIntegerField(default=0)
    return_on_trade = models.DecimalField(
        decimal_places=2,
        max_digits=10,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal(0.00))],
        help_text="The actual profit that was made from car ",
    )
    estimated_return_on_trade = models.DecimalField(
        decimal_places=2,
        default=Decimal(0.00),
        validators=[MinValueValidator(Decimal(0.00))],
        max_digits=10,
        help_text="The estimated profit that can be made from car sale",
    )
    price_per_slot = models.DecimalField(
        decimal_places=2,
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
        help_text="min price at which the car can be sold, given the expenses we already made. "
                  "this should be determined by calculating how much maintanance is done + total disbursement at the end of trade",
    )
    estimated_sales_duration = models.PositiveIntegerField(help_text="estimated sales duration in days", default=30)
    bts_time = models.IntegerField(default=0, help_text="time taken to buy to sale in days", null=True, blank=True)
    date_of_sale = models.DateField(null=True, blank=True)
    carpadi_commission = models.DecimalField(
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0.00))],
        max_digits=10,
        default=Decimal(0.00),
        help_text="The commision of carpadi on this trade",
    )
    carpadi_bonus = models.DecimalField(
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0.00))],
        max_digits=10,
        default=Decimal(0.00),
        help_text="Amount of bonus made by carpadi",
    )
    traders_bonus_per_slot = models.DecimalField(
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0.00))],
        max_digits=10,
        default=Decimal(0.00),
        help_text="The amount of allocated bonus per slot",
    )
    total_carpadi_rot = models.DecimalField(
        decimal_places=2,
        validators=[MinValueValidator(Decimal(0.00))],
        max_digits=10,
        default=Decimal(0.00),
        help_text="The total amount of money made by carpadi on this trade",
    )

    @property
    def resale_price(self) -> Decimal:
        """
        This will be the minimum sale price before the car is sold
        """
        if not self.car.resale_price or (self.car.resale_price <= Decimal(0.00)):
            return self.min_sale_price
        return self.car.resale_price

    def margin_calc(self) -> Decimal:
        return self.resale_price - self.car.total_cost_calc()

    def return_on_trade_calc(self) -> Decimal:
        """return on trade for the entire trade; analysed thus:
        Projected rot at the time of creating trade is a percentage of the car value typically;
        `self.car.total_cost_calc() * settings.merchant_trade_rot_percentage / 100`
        """
        settings: Settings = Settings.objects.first()
        return self.car.total_cost_calc() * (settings.merchant_trade_rot_percentage / 100)

    def bonus_calc(self) -> Decimal:
        """Bonus only happens when there is some money left after
        rot and carpadi commission have been deducted from margin
        """
        bonus = self.margin_calc() - self.return_on_trade_calc()
        return bonus if bonus >= Decimal(0) else Decimal(0)

    def traders_bonus(self) -> Decimal:
        """This is the portion of the bonus that will go to the traders
        typically a percentage of the bonus defined in settings
        """
        settings: Settings = Settings.objects.first()
        return self.bonus_calc() * settings.bonus_percentage / 100

    def return_on_trade_calc_percent(self):
        settings: Settings = Settings.objects.first()
        return settings.merchant_trade_rot_percentage

    @property
    def return_on_trade_per_slot(self) -> Decimal:
        settings: Settings = Settings.objects.first()
        return (self.return_on_trade_calc() / self.slots_available) * settings.carpadi_commision / 100

    def return_on_trade_per_slot_percent(self) -> Decimal:
        settings: Settings = Settings.objects.first()
        return settings.merchant_trade_rot_percentage

    def slots_purchased(self):
        # TODO: this is a hack, fix it using annotations
        return sum(unit.slots_quantity for unit in self.units.all())

    def carpadi_commission_calc(self) -> Decimal:
        """Carpadi commission is basically some percentage of the rot of each trader that bought unit on the trade
        commission: self.return_on_trade_calc() * settings.carpadi_commission /100
        """
        settings: Settings = Settings.objects.first()
        return self.return_on_trade_calc() * settings.carpadi_commision / 100

    def carpadi_commission_per_slot(self):
        settings: Settings = Settings.objects.first()
        return self.return_on_trade_per_slot * settings.carpadi_commision / 100

    def carpadi_bonus_calc(self):
        return self.bonus_calc() - self.traders_bonus()

    def deficit_balance(self):
        """
        This basically happens when we have a trade that we run loss on,
         i.e the car_value is greater than resale_price.
        The directive is to deduct the deficit from their investment and disburse the rest
        """
        return abs(self.margin_calc()) if self.margin_calc() < 0 else Decimal(0)

    def carpadi_rot_calc(self) -> Decimal:
        """The return on trade for carpadi on this trade, they are:
        1. if the trade has been completed,
            if the margin_calc is greater than self.return_on_trade_calc()
                i. excess_margin: margin - (car_value * fixed rot percentage / 100) - self.traders_bonus()
                ii. carpadi_commission: self.return_on_trade_calc * settings.carpadi_commission /100
            if the margin_calc is equal to self.return_on_trade_calc()
                i. carpadi_commission: self.return_on_trade_calc * settings.carpadi_commission /100
            if margin_calc is less than or equal to 0:
                i. No commission
        2. if the trade is not yet sold
        """
        if self.trade_status in (
                TradeStates.Completed, TradeStates.Closed) and self.car.bought_price and self.resale_price:
            settings: Settings = Settings.objects.first()
            if self.margin_calc() > self.return_on_trade_calc():
                excess = self.carpadi_bonus_calc()
                commission = self.return_on_trade_calc() * settings.carpadi_commision / 100
                return Decimal(commission + excess)
            elif self.margin_calc() == self.return_on_trade_calc():
                commission = self.return_on_trade_calc() * settings.carpadi_commision / 100
                return Decimal(commission)
            else:
                return Decimal(0)
        return Decimal(0)

    def remaining_slots(self):
        slots_purchased = sum(unit.slots_quantity for unit in self.units.all())
        return self.slots_available - slots_purchased

    def total_payout(self):
        """
        Total payout for the trade. cumulative of
        total amount of initial investment i.e trade_unit.unit_value
        and total amount of return on trade i.e trade_unit.return_on_trade and bonuses
        across all units
        """
        if self.trade_status != TradeStates.Completed:
            raise APIException(detail="Trade is not yet completed")
        return sum(unit.payout() for unit in self.units.all())

    def min_sale_price_calc(self):
        """
        The minimum amount that this car can be sold. it is a culmination of

        car_value + (car_value * fixed_rot_percentage)
        """
        return self.car.total_cost_calc() + self.return_on_trade_calc()

    def run_disbursement(self):
        if self.trade_status != TradeStates.Completed:
            raise ValueError(f"Trade is in {self.trade_status} state")
        for unit in self.units.all():
            unit.disburse()

    def calculate_price_per_slot(self):
        return self.car.total_cost_calc() / self.slots_available

    def get_trade_merchants(self):
        return self.units.values_list('merchant', flat=True).distinct()

    def sold_slots_price(self):
        return self.units.aggregate(s=Sum("unit_value")).get("s") or Decimal(0.0)

    def estimated_carpadi_rot(self):
        settings = Settings.objects.first()
        return (self.return_on_trade_calc() * settings.carpadi_commision) / 100

    def notify_on_trade_close(self, disbursements: List["Disbursement"]):
        for dis in disbursements:
            Activity.objects.create(
                activity_type=ActivityTypes.Disbursement,
                activity=dis,
                merchant=dis.trade_unit.merchant,
                description=f"Activity Type: Disbursement, Description: Disbursed {dis.amount} "
                            f"naira for {dis.trade_unit.slots_quantity} units \
                        owned in {dis.trade_unit.trade.car.information.brand.name}"
                            f" {dis.trade_unit.trade.car.information.brand.model} VIN: {dis.trade_unit.trade.car.vin}",
            )
            Notifications.objects.create(
                notice_type=NotificationTypes.Disbursement,
                is_read=False,
                message=f"Disbursed {dis.amount} naira for {dis.trade_unit.slots_quantity} units "
                        f"owned in {dis.trade_unit.trade.car.name}"
                        f" VIN: {dis.trade_unit.trade.car.vin}",
                entity_id=dis.id,
                user=dis.trade_unit.merchant.user,
            )

    @atomic()
    def close(self):
        units = self.units.all()
        disbursements = []
        for unit in units:
            unit.disbursement.settle()
            disbursements.append(unit.disbursement)
        self.trade_status = TradeStates.Closed
        self.save(update_fields=["trade_status"])
        self.notify_on_trade_close(disbursements)
        return None

    @atomic()
    def save(self, *args, **kwargs):
        if self._state.adding:
            self.price_per_slot = self.calculate_price_per_slot()
            self.min_sale_price = self.min_sale_price_calc()
            self.estimated_return_on_trade = self.return_on_trade_calc()
        return super(Trade, self).save(*args, **kwargs)

    @atomic()
    def check_updates(self):
        if self.trade_status == TradeStates.Completed:
            self.date_of_sale = timezone.now()
            self.traders_bonus_per_slot = self.traders_bonus() / self.slots_available
            self.carpadi_commission = self.carpadi_commission_calc()
            self.carpadi_bonus = self.carpadi_bonus_calc()
            self.total_carpadi_rot = self.carpadi_rot_calc()
            self.return_on_trade = self.return_on_trade_calc()
            self.run_disbursement()
            self.complete_trade()
            update_fields = ["date_of_sale", "traders_bonus_per_slot", "carpadi_commission", "carpadi_bonus",
                             "total_carpadi_rot"]
            self.save(update_fields=update_fields)

    def complete_trade(self):
        """
        Completes the trade by setting the trade status to completed and updating the car status.
        we also try to do some validation to make sure trade and its corresponding objects are valid
        """
        successful_disbursements = self.units.filter(
            disbursement__disbursement_status=DisbursementStates.Unsettled).count()
        query = self.units.annotate(total_disbursed=Sum('disbursement__amount'))
        total_disbursed = query.aggregate(sum=Sum('total_disbursed')).get('sum') or Decimal(0)
        if successful_disbursements != self.units.count() or total_disbursed != self.total_payout():
            # TODO send notification for this, seems fatal
            raise exceptions.APIException(
                detail="Error, cannot complete trade, because calculated " "payout seems to be unbalanced with the disbursements"
            )
        car: Car = self.car
        car.update_on_sold()

    def __repr__(self):
        return (
            f"<Trade(car={self.car}, slots_available={self.slots_available},"
            f" status={self.trade_status}, date_of_sale={self.date_of_sale})>"
        )

    @atomic()
    def rollback(self):
        self.trade_status = TradeStates.Purchased
        for disbursement in Disbursement.objects.filter(trade_unit__trade_id=self.id):
            disbursement.rollback()
        self.carpadi_bonus = Decimal(0.00)
        self.total_carpadi_rot = Decimal(0.00)
        self.traders_bonus_per_slot = Decimal(0.00)
        self.save(update_fields=["trade_status", "carpadi_bonus", "total_carpadi_rot", "traders_bonus_per_slot"])
        car = self.car
        car.status = CarStates.OngoingTrade
        car.margin = Decimal(0.00)
        car.total_cost = car.total_cost_calc()
        car.cost_of_repairs = Decimal(0.00)
        car.save(update_fields=["status", "margin", "total_cost", "cost_of_repairs"])


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
        Transaction,
        on_delete=models.PROTECT,
        related_name="trade_units_buy",
        null=False,
        blank=False,
        help_text="the transaction that bought this unit",
    )
    checkout_transaction = models.ForeignKey(
        Transaction,
        on_delete=models.PROTECT,
        related_name="trade_units_checkout",
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal(0.00)), checkout_transaction_validator],
        help_text="the transaction that materialized out this unit",
    )
    trade_bonus = models.DecimalField(
        decimal_places=2,
        editable=False,
        validators=[MinValueValidator(Decimal(0.00))],
        max_digits=10,
        default=Decimal(0.00),
        help_text="The bonus that the trade unit got if any",
    )

    class Meta:
        ordering = ["-slots_quantity"]

    def disburse(self):
        self.trade_bonus = self.trade.traders_bonus_per_slot * self.slots_quantity
        dis = Disbursement.objects.create(
            trade_unit=self,
            disbursement_status=DisbursementStates.Unsettled,
            amount=self.payout(),
        )
        self.checkout_transaction = dis.transaction
        self.save(update_fields=["trade_bonus", "checkout_transaction"])
        return dis

    def payout(self):
        """The amount of money that will be payout for this unit after this trade is completed
        this should take into account deficits and bonus
        """
        if self.trade.trade_status not in (TradeStates.Completed, TradeStates.Closed):
            return None
        deficit = Decimal(0)
        if self.trade.deficit_balance() > Decimal(0):
            deficit = (self.trade.deficit_balance() / self.trade.slots_available) * self.slots_quantity
        base_rot_minus_carpadi_commission = self.trade.return_on_trade_per_slot * self.slots_quantity  # noqa
        base_payout = (
                base_rot_minus_carpadi_commission
                + self.unit_value
                + (self.trade.traders_bonus_per_slot * self.slots_quantity)  # noqa
        )
        return base_payout - deficit

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.share_percentage = self.slots_quantity / self.trade.slots_available * 100
            self.unit_value = self.trade.price_per_slot * self.slots_quantity
            self.estimated_rot = self.trade.return_on_trade_per_slot * self.slots_quantity
        return super().save(*args, **kwargs)


class DisbursementStates(models.TextChoices):
    RolledBack = "rolled_back", _("A disbursement that was rolledback")
    Ongoing = "Ongoing"
    Completed = "Completed"
    Unsettled = "Unsettled", _("Unsettled. The disbursement has been created but not yet settled by the admin")
    Settled = "Settled", _("Settled. The disbursement has been settled by the admin")


class Disbursement(Base):
    trade_unit = models.OneToOneField(
        TradeUnit,
        on_delete=models.CASCADE,
        related_name="disbursement",
        validators=[disbursement_trade_unit_validator],
        help_text="the trade unit that this disbursement is for",
    )
    amount = models.DecimalField(decimal_places=10, editable=False, max_digits=30)
    transaction = models.OneToOneField(Transaction, on_delete=models.PROTECT, related_name="disbursement", null=True,
                                       blank=True)
    disbursement_status = models.CharField(
        choices=DisbursementStates.choices, max_length=20, default=DisbursementStates.Unsettled
    )

    def settle(self):
        if self.disbursement_status == DisbursementStates.Unsettled:
            self.disbursement_status = DisbursementStates.Settled
            self.save(update_fields=["disbursement_status"])
            self.transaction.wallet.update_balance(self.transaction)
            return True
        raise ValueError("Disbursement is not in unsettled state, so why are you tryna settle it?")

    def rollback(self):
        self.disbursement_status = DisbursementStates.RolledBack
        self.save(update_fields=["disbursement_status"])
        wallet = self.trade_unit.merchant.wallet
        tranx = self.transaction
        tranx.transaction_status = TransactionStatus.RolledBack
        tranx.save(update_fields=['transaction_status'])
        wallet.update_balance(tranx)
        self.delete()  # FIXME should we ?

    def __str__(self):
        return f"Disbursement for {self.trade_unit.trade.id} - {self.trade_unit.merchant.user.username}"

    def __repr__(self):
        return (
            f"<Disbursement(trade_unit={self.trade_unit.id}, "
            f"amount={self.amount}, status={self.disbursement_status}, transaction={self.transaction.id})> "
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            ref = f"cp-db-{self.id}"
            self.transaction = Transaction.objects.create(
                wallet=self.trade_unit.merchant.wallet,
                amount=self.amount,
                transaction_type=TransactionTypes.Credit,
                transaction_reference=ref,
                transaction_status=TransactionStatus.Unsettled,
                transaction_kind=TransactionKinds.Disbursement,
            )
            self.transaction.wallet.update_balance(self.transaction)
        return super().save(*args, **kwargs)


class ActivityTypes(models.TextChoices):
    Transaction = "transaction", _("transaction")
    TradeUnit = "trade_unit", _("trade_unit")
    Disbursement = "disbursement", _("disbursement")
    CarCreation = "car_creation", _("car_creation")
    NewUser = "new_user", _("new user")


class Activity(Base):
    activity_type = models.CharField(choices=ActivityTypes.choices, max_length=15)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    activity = GenericForeignKey("content_type", "object_id")
    description = models.TextField(default="")
    merchant = models.ForeignKey(CarMerchant, on_delete=models.CASCADE, null=True, blank=True)


class AssetEntityType(models.TextChoices):
    CarProduct = "car_product", _("Pictures of a car on the sales platform")
    Car = "car", _("car picture")
    Merchant = "merchant", _("user profile picture")
    Trade = "trade", _("Trade pictures of a car")
    InspectionPart = "car_inspection_stage", _("Picture taken for a particular stage during inspection")
    Features = "feature", _("Picture of a feature of a car")
    InspectionReport = "inspection_report", _("Pdf report of an inspected vehicle")
    CarSparePart = "spare_part", _("Images of spare parts")
    CarDocument = "car_docs", _("Credentials and documents attached to the car")
    Inspection = "inspection_images", _("Inspection images that doesnt relate to any stage")


class Assets(Base):
    asset = models.URLField(null=False, blank=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")
    entity_type = models.CharField(choices=AssetEntityType.choices, max_length=20)

    @classmethod
    def create_many(cls, images: List[str], feature, entity_type: AssetEntityType):
        if isinstance(images, list) and images:
            ims = [Assets(id=uuid.uuid4(), content_object=feature, asset=image, entity_type=entity_type) for image in
                   images]
            return Assets.objects.bulk_create(objs=ims)

    def __str__(self):
        return self.asset


class VehicleInfo(Base):
    vin = models.CharField(max_length=17, unique=True, db_index=True)
    engine = models.TextField()
    transmission = models.CharField(max_length=15, choices=CarTransmissionTypes.choices)
    car_type = models.CharField(max_length=50, null=True, blank=True)
    fuel_type = models.CharField(max_length=30, null=False, blank=False)
    mileage = models.PositiveIntegerField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    trim = models.CharField(max_length=50, null=True, blank=False)
    manufacturer = models.CharField(max_length=50)
    brand = models.ForeignKey(CarBrand, on_delete=models.SET_NULL, null=True, blank=True)
    specifications = models.CharField(max_length=20, null=True, blank=True)
    drive_type = models.CharField(max_length=20, null=True, blank=True)
    last_service_date = models.DateField(null=True, blank=True)
    last_service_mileage = models.PositiveIntegerField(null=True, blank=True)
    previous_owners = models.PositiveIntegerField(null=True, blank=True)
    num_of_cylinders = models.PositiveIntegerField(null=True, blank=True)
    engine_power = models.CharField(null=True, blank=True, max_length=20)
    torque = models.CharField(null=True, blank=True, max_length=20)
    raw_data = models.JSONField(null=True, blank=True)


class CarProductStatus(models.TextChoices):
    Active = "active", _(
        "Car is still in the market",
    )
    Sold = "sold", _("Car has been sold")
    Inactive = "inactive", _(
        "Car has been recalled due to" " fault or other issues, or just added and not made active yet")


class CarProduct(Base):
    car = models.OneToOneField(Car, on_delete=models.CASCADE, related_name="product")
    selling_price = models.DecimalField(decimal_places=2, max_digits=25)
    highlight = models.CharField(max_length=260, help_text="A short description of the vehicle")
    status = models.CharField(choices=CarProductStatus.choices, default=CarProductStatus.Active, max_length=10)

    def save(self, *args, **kwargs):
        if self._state.adding and not self.highlight:
            self.highlight = (
                f"{self.car.information.manufacturer}"
                f" | {self.car.information.brand.name}"
                f" | {self.car.information.brand.model} "
                f"| {self.car.information.brand.year}"
            )
        return super(CarProduct, self).save(args, kwargs)


class CarFeature(Base):
    car = models.ForeignKey(CarProduct, on_delete=models.CASCADE, related_name="features")
    name = models.CharField(max_length=100)


class NotificationTypes(models.TextChoices):
    TransactionCompleted = "transaction_completed", _(
        "Transaction completed",
    )
    TransactionFailed = "transaction_failed", _(
        "Transaction failed",
    )
    NewTrade = "new_trade", _("New Trade")
    PasswordReset = "password_reset", _("Password Reset")
    ProfileUpdate = "profile_update", _("Profile Update")
    Disbursement = "disbursement", _("Disbursement")
    TradeUnit = "trade_unit", _("Trade Unit")


class Notifications(Base):
    # notification with None as User are for the whole users
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=False)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notice_type = models.CharField(choices=NotificationTypes.choices, max_length=50)
    entity_id = models.UUIDField(null=True, blank=True)
    title = models.CharField(max_length=50, null=False, blank=False, default="New notification")

    @atomic()
    def save(self, *args, **kwargs):
        if self._state.adding:
            self.title = self.get_title()
        return super().save(*args, **kwargs)

    def get_title(self):
        if self.notice_type == NotificationTypes.TradeUnit:
            return "New Unit purchased"
        elif self.notice_type == NotificationTypes.NewTrade:
            return "New trade available"
        elif self.notice_type == NotificationTypes.PasswordReset:
            return "Password reset success"
        elif self.notice_type == NotificationTypes.Disbursement:
            return "ROT disbursed"
        else:
            return "New notice"


class InspectionVerdict(models.TextChoices):
    Great = "great", _("Average rating above 90 percentile")
    Good = "good", _("Average rating above 60 percentile up to 89")
    Fair = "fair", _("Average rating above 40 percentile up to 60")
    Bad = "bad", _("Average rating below 39 percentile")
    NA = "not_available", _("The default status for newly created inspection which is still pending.")


class Stages(models.TextChoices):
    Generic = "generic"
    Exterior = "exterior"
    Glass = "glass"
    TyresAndWheels = "wheels"
    UnderBody = "under_body"
    UnderHood = "under_hood"
    Interior = "interior"
    ElectricalSystems = "electrical_systems"
    RoadTest = "road_test"
    Completed = "completed"
    NotStarted = "not_started"


class Inspections(Base):
    owners_name = models.CharField(max_length=100)
    inspection_date = models.DateTimeField()
    owners_phone = models.CharField(
        max_length=20,
        validators=[
            PhoneNumberValidator,
        ],
    )
    owners_review = models.TextField(null=True, blank=True)
    address = models.TextField()
    status = models.CharField(choices=InspectionStatus.choices, max_length=20, default=InspectionStatus.Pending)
    inspection_verdict = models.CharField(
        choices=InspectionVerdict.choices,
        max_length=15,
        default=InspectionVerdict.NA,
        help_text="Verdict of the inspection after taking into account all"
                  " the stages and their scores. should be calculated by the system",
    )
    inspector = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name="inspections",
        blank=False,
        help_text="The person to undertake this inspection",
    )
    inspection_assignor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name="inspections_assigned",
        blank=False,
        help_text="The user who assigned this inspection to the inspector. should be set automatically",
    )
    car = models.OneToOneField(Car, on_delete=models.CASCADE)
    inspection_score = models.DecimalField(
        null=True, blank=True, decimal_places=2, max_digits=5, help_text="The score of the inspection after completion"
    )
    pictures = GenericRelation("Assets")
    current_stage = models.CharField(choices=Stages.choices, max_length=20, default=Stages.NotStarted)

    def save(self, *args, **kwargs):
        if self._state.adding:
            return super(Inspections, self).save(*args, **kwargs)
        updated_fields = kwargs.get("updated_fields", [])
        self.car.update_on_inspection_changes(self)
        super(Inspections, self).save(*args, **kwargs)


class Score(models.IntegerChoices):
    Good = 20
    Fair = 10
    Poor = 0


class InspectionStage(Base):
    inspection = models.ForeignKey(Inspections, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(choices=Score.choices)
    part_name = models.CharField(max_length=50)
    stage_name = models.CharField(choices=Stages.choices, max_length=40)
    review = models.TextField(null=True, blank=True)
    picture = GenericRelation("Assets")


class Settings(Base):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    # carpadi_trade_rot_percentage = models.DecimalField(decimal_places=2, max_digits=25)
    merchant_trade_rot_percentage = models.DecimalField(
        decimal_places=2,
        max_digits=25,
        default=Decimal(5.00),
        help_text="The percentage of the car value that will be the return on trade."
                  " this is used to calculate the rot when buying slots,"
                  " like `car_value * merchant_trade_rot_percentage / slot_to_buy`",
    )
    transfer_fee = models.DecimalField(decimal_places=2, max_digits=25, default=Decimal(0.00))
    close_trade_fee = models.DecimalField(decimal_places=2, max_digits=25, default=Decimal(0.00))
    carpadi_commision = models.DecimalField(
        decimal_places=2,
        max_digits=25,
        default=Decimal(50.00),
        help_text="The amount of commission to deduct from rot of the trader after trade maturation",
    )
    bonus_percentage = models.DecimalField(
        decimal_places=2, max_digits=25, default=Decimal(50.00),
        help_text="Percentage of the bonus that will go to the traders"
    )

    def save(self, *args, **kwargs):
        if self._state.adding:
            if exists := Settings.objects.first():
                return exists
        return super(Settings, self).save(*args, **kwargs)


class File(models.Model):
    THUMBNAIL_SIZE = (360, 360)

    file = models.FileField(blank=False, null=False)
    thumbnail = models.ImageField(blank=True, null=True)
    author = models.ForeignKey(User, related_name='files', on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)


class CarDocumentsTypes(models.TextChoices):
    ProofOfOwnership = "proof_of_ownership", _("Proof of ownership document")
    AllocationOfLicensePlate = "allocation_of_licence_plate", _(
        "Allocation of plate number",
    )
    VehicleLicense = "vehicle_license", _(
        "Vehicle license",
    )
    CustomPapersOrPurchaseReceipt = "custom_papers_or_purchase_receipt", _(
        "Customs paper if car was imported or Receipt of purchase documents"
        " if the car was bought brand new from an accredited dealer",
    )
    PoliceCMR = "police_CMR", _(
        "Police CMR",
    )
    Insurance = "insurance", _(
        "Insurance papers",
    )
    RoadWorthiness = "road_worthiness", _("Road worthiness permit")
    CarOwnerIdentification = "owner_identification", _("Car Owner's document of identity")
    Others = "others", _("Other custom documents that are not required")


class CarDocuments(Base):
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    is_verified = models.BooleanField(default=False)
    name = models.CharField(max_length=50)
    asset = models.OneToOneField(Assets, on_delete=models.SET_NULL, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    document_type = models.CharField(max_length=40, choices=CarDocumentsTypes.choices)

    @classmethod
    def documentation_completed(cls, car: str) -> bool:
        docs = (
            CarDocuments.objects.filter(car__id=car, is_verified=True).filter(
                ~Q(document_type=CarDocumentsTypes.Others)).count()
        )
        return len(CarDocumentsTypes.choices) - 1 == docs


class CarConditionsTypes(models.TextChoices):
    Good = "good", _(
        "Car is in good condition",
    )
    Great = "great", _(
        "Car is in great condition",
    )
    Fair = "fair", _(
        "Car is fairly good",
    )
    poor = "poor", _("car is not in good condition")


class ContactPreference(models.TextChoices):
    Email = "email", _(
        "Email",
    )
    Phone = "phone", _(
        "Phone",
    )
    Whatsapp = "whatsapp", _(
        "Whatsapp",
    )


class CarPurchasesStatus(models.TextChoices):
    Accepted = "accepted", _("Car purchase offer was accepted")
    Declined = "declined", _("Purchase offer declined based on some reason")
    Pending = "pending", _("Yet to be processed")


class DealPreferences(models.TextChoices):
    Swap = "swap", _("A car for a car")
    Outright = "outright", _("Outright buying of car")


class CarSellers(Base):
    name = models.CharField(max_length=50, null=False, blank=False)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(
        validators=[
            PhoneNumberValidator,
        ],
        max_length=20,
    )


class CarPurchaseOffer(Base):
    """
    This represents the details of the offer to sell a car to us
    """

    vehicle_info = models.ForeignKey(
        VehicleInfo, on_delete=models.SET_NULL, null=True, blank=False, related_name="purchase_offers"
    )
    car = models.OneToOneField(Car, null=True, on_delete=models.SET_NULL)
    licence_plate = models.CharField(null=False, blank=False, validators=[LicensePlateValidator], max_length=15)
    registeration_state = models.CharField(max_length=40, null=False, blank=False)
    current_usage_timeframe_by_user = models.PositiveIntegerField(
        help_text="how long has this user used the car in months")
    mileage = models.PositiveIntegerField(help_text="the current mileage of the car on the dashboard")
    seller = models.ForeignKey(CarSellers, on_delete=models.SET_NULL, null=True, default=None)
    inspection_location = models.CharField(max_length=40, null=False, blank=False)
    status = models.CharField(choices=CarPurchasesStatus.choices, default=CarPurchasesStatus.Pending, max_length=40)
    decline_reason = models.TextField(default="")
    deal_preference = models.CharField(choices=DealPreferences.choices, max_length=20, default=DealPreferences.Outright)


class Waitlists(Base):
    email = models.EmailField(unique=True, validators=[EmailValidator, ])
