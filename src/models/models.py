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
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Sum
from django.db.transaction import atomic
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from easy_thumbnails.signal_handlers import generate_aliases_global
from easy_thumbnails.signals import saved_file
from model_utils.models import UUIDModel, TimeStampedModel
from rest_framework import exceptions
from rest_framework.exceptions import APIException
from rest_framework_simplejwt.tokens import RefreshToken

from src.carpadi_admin.utils import validate_inspector, checkout_transaction_validator, disbursement_trade_unit_validator
from src.config.common import OTP_EXPIRY
from src.models.validators import PhoneNumberValidator


class InspectionStatus(models.TextChoices):
    Ongoing = "ongoing", _("Ongoing inspection")
    Completed = "completed", _("Completed inspection")
    Pending = "pending", _("New inspection")
    Expired = "expired", _("Inspection has been scheduled for" " more than a week without being ongoing or completed")


class Base(UUIDModel, TimeStampedModel):
    pass

    class Meta:
        abstract = True


class UserTypes(models.TextChoices):
    Admin = "admin", "admin"
    CarMerchant = "merchant", "merchant"


class User(AbstractUser, Base):
    username_validator = UnicodeUsernameValidator()
    profile_picture = models.OneToOneField("Assets", on_delete=models.SET_NULL, null=True, blank=True)
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

    class Meta:
        unique_together = ('device_serial_number', 'pin')


class UserStatusFilterChoices(models.TextChoices):
    ActivelyTrading = "actively_trading", _("user is an active trading user")
    NotActivelyTrading = "not_actively_trading", _("user is not actively trading")


class CarMerchant(Base):
    user: User = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name="merchant")
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
        trading = self.merchant.units.filter(trade__trade_status__in=(TradeStates.Purchased, TradeStates.Ongoing)).aggregate(
            total=Sum("unit_value")
        ).get("total") or Decimal(0.00)
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
            balance_after_deduction = (
                Decimal(0.0) if self.withdrawable_cash - tx.amount < 0 else self.withdrawable_cash - tx.amount
            )
            self.withdrawable_cash = balance_after_deduction
            updated_fields_wallet.append("withdrawable_cash")
            tx.transaction_status = TransactionStatus.Pending
        elif tx.transaction_kind == TransactionKinds.Disbursement and tx.transaction_type == TransactionTypes.Credit:
            db: "Disbursement" = tx.disbursement
            if db.disbursement_status == DisbursementStates.Unsettled:
                balance_after_deduction = (
                    Decimal(0.0)
                    if self.trading_cash - db.trade_unit.unit_value < 0
                    else self.trading_cash - db.trade_unit.unit_value
                )
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
        elif tx.transaction_kind == TransactionKinds.TradeUnitPurchases and tx.transaction_type == TransactionTypes.Debit:
            self.withdrawable_cash = (
                Decimal(0.0) if self.withdrawable_cash - tx.amount < 0 else self.withdrawable_cash - tx.amount
            )
            updated_fields_wallet.append("withdrawable_cash")
            tx.transaction_status = TransactionStatus.Success
        else:
            raise ValidationError("Invalid transaction type and kind combination")
        tx.save(
            update_fields=[
                "transaction_status",
            ]
        )
        self.save(update_fields=updated_fields_wallet)
        self.refresh_from_db()
        return self.save()


class TransactionStatus(models.TextChoices):
    Unsettled = "unsettled", _(
        "Transaction that are yet to be resolved due" " to a dispute or disbursement delay, typically pending credit"
    )
    Success = "success", _("Success")
    Failed = "failed", _("Failed")
    Pending = "pending", _("Pending")


# Transactions
class Transaction(Base):
    amount = models.DecimalField(max_digits=10, decimal_places=4)
    wallet = models.ForeignKey(
        Wallet, on_delete=models.CASCADE, related_name="merchant_transactions", help_text="transactions carried out by merchant"
    )
    transaction_type = models.CharField(max_length=10, choices=TransactionTypes.choices)
    transaction_reference = models.CharField(max_length=50, null=False, blank=False)
    transaction_description = models.CharField(max_length=50, null=True, blank=True)
    transaction_status = models.CharField(max_length=10, choices=TransactionStatus.choices, default=TransactionStatus.Pending)
    transaction_response = models.JSONField(null=True, blank=True, help_text="Transaction response from payment gateway")
    transaction_kind = models.CharField(max_length=50, choices=TransactionKinds.choices, default=TransactionKinds.Deposit)
    transaction_payment_link = models.URLField(max_length=200, null=True, blank=True)
    transaction_fees = models.DecimalField(
        max_digits=10, decimal_places=4, default=0.0, help_text="Transaction fees for withdrawal transactions"
    )

    @classmethod
    def verify_deposit(cls, response, tx):
        data = response.json()
        if response.status_code == 200 and (data['status'] in ('success', "successful", 'SUCCESSFUL')):
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
        CarMerchant, on_delete=models.CASCADE, related_name="bank_accounts", help_text="Bank account to remit merchant money to"
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
    Standar = "standard", _("Who knows")


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
    information = models.OneToOneField("VehicleInfo", on_delete=models.SET_NULL, null=True)
    status = models.CharField(choices=CarStates.choices, null=True, max_length=30, default=CarStates.New)
    # TODO validate vin from vin api
    vin = models.CharField(max_length=17)
    pictures = GenericRelation("Assets")
    # car_inspection = models.OneToOneField(
    #     "Inspections",
    #     on_delete=models.SET_NULL,
    #     null=True,
    #     blank=False,
    #     validators=[
    #         validate_inspector,
    #     ],
    #     related_name="car_inspection"
    # )
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
    licence_plate = models.CharField(max_length=20, null=True, blank=True)

    def maintenance_cost_calc(self):
        return self.maintenances.all().aggregate(sum=Sum("cost")).get("sum") or Decimal(0.00)

    def total_cost_calc(self):
        return self.bought_price + self.maintenance_cost_calc()

    def margin_calc(self):
        return self.resale_price - self.total_cost_calc() if self.resale_price else None

    def update_on_sold(self):
        self.status = CarStates.Sold
        self.margin = self.margin_calc()
        self.save(update_fields=["status", "margin"])

    def update_on_inspection_changes(self, inspection: "Inspections"):
        if inspection.status == InspectionStatus.Completed:
            self.status = CarStates.Inspected
        elif inspection.status in (
            InspectionStatus.Ongoing,
            InspectionStatus.Pending,
        ):
            self.status = CarStates.OngoingInspection
        else:
            self.status = CarStates.FailedInspection
        self.save(update_fields=["status"])

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.name = f"{self.information.brand.name}" f" {self.information.brand.model} {self.information.brand.year}"
        super().save(*args, **kwargs)


class SpareParts(Base):
    name = models.CharField(max_length=100)
    car_brand = models.ForeignKey(CarBrand, on_delete=models.CASCADE)
    estimated_price = models.DecimalField(max_digits=10, decimal_places=2)

    # class Meta:
    #     unique_together = ('name', 'car_brand')


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
    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="cost of the maintenance a the time of the maintenance.. "
        "cost on the maintenance might change, i.e spare parts. "
        "the cost here is the correct one to use when calculating "
        "total cost of car maintenance",
    )


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

    @property
    def resale_price(self):
        """
        This will be the minimum sale price before the car is sold
        """
        if not self.car.resale_price or (self.car.resale_price <= Decimal(0.00)):
            return self.min_sale_price
        return self.car.resale_price

    def return_on_trade_calc(self):
        return self.resale_price - self.car.total_cost_calc()

    def return_on_trade_calc_percent(self):
        return self.return_on_trade_calc() / self.resale_price * 100

    @property
    def return_on_trade_per_slot(self) -> Decimal:
        settings: Settings = Settings.objects.first()
        return Decimal(self.price_per_slot * settings.merchant_trade_rot_percentage / 100)

    def return_on_trade_per_slot_percent(self):
        settings: Settings = Settings.objects.first()
        return settings.merchant_trade_rot_percentage

    def slots_purchased(self):
        # TODO: this is a hack, fix it using annotations
        return sum(unit.slots_quantity for unit in self.units.all())

    @property
    def carpadi_rot(self):
        settings: Settings = Settings.objects.first()
        return Decimal(self.car.total_cost_calc() * settings.carpadi_trade_rot_percentage / 100)

    def remaining_slots(self):
        slots_purchased = sum(unit.slots_quantity for unit in self.units.all())
        return self.slots_available - slots_purchased

    def total_payout(self):
        """
        Total payout for the trade. cumulative of
        total amount of initial investment i.e trade_unit.unit_value
        and total amount of return on trade i.e trade_unit.return_on_trade
        across all units
        """
        if total_unit_value := self.units.aggregate(total=Sum('unit_value')).get('total'):
            return self.return_on_trade_per_slot * self.slots_available + total_unit_value
        else:
            raise APIException(detail="No units have been sold yet")

    def min_sale_price_calc(self):
        """
        The minimum amount that this car can be sold. it is a culmination of
        car_value + total units rot + (car_value * minimum_carpadi_commision / 100)
        """
        settings: Settings = Settings.objects.first()
        total_slots_rot = self.return_on_trade_per_slot * self.slots_available
        carpadi_rot = self.car.total_cost_calc() * settings.carpadi_trade_rot_percentage / 100
        return self.car.total_cost_calc() + total_slots_rot + carpadi_rot

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

    @atomic()
    def close(self):
        units = self.units.all()
        for unit in units:
            unit.disbursement.settle()
        self.trade_status = TradeStates.Closed
        self.save(update_fields=["trade_status"])
        return None

    @atomic()
    def save(self, *args, **kwargs):
        if self._state.adding:
            self.price_per_slot = self.calculate_price_per_slot()
            self.min_sale_price = self.min_sale_price_calc()
            self.estimated_return_on_trade = self.return_on_trade_calc()
        else:
            self.check_updates(kwargs.get("update_fields", []))
        return super().save(*args, **kwargs)

    def check_updates(self, update_fields):
        if "trade_status" in update_fields and self.trade_status == TradeStates.Completed:
            if self.trade_status == TradeStates.Completed:
                self.date_of_sale = timezone.now()
                self.run_disbursement()
                self.complete_trade()
        return None

    def complete_trade(self):
        """
        Completes the trade by setting the trade status to completed and updating the car status.
        we also try to do some validation to make sure trade and its corresponding objects are valid
        """
        successful_disbursements = self.units.filter(disbursement__disbursement_status=DisbursementStates.Unsettled).count()
        query = self.units.annotate(total_disbursed=Sum('disbursement__amount'))
        total_disbursed = query.aggregate(sum=Sum('total_disbursed')).get('sum') or Decimal(0)
        if successful_disbursements != self.units.count() or total_disbursed != self.total_payout():
            # TODO send notification for this, seems fatal
            raise exceptions.APIException(
                "Error, cannot complete trade, because calculated " "payout seems to be unbalanced with the disbursements"
            )
        car: Car = self.car
        car.update_on_sold()

    def __repr__(self):
        return (
            f"<Trade(car={self.car}, slots_available={self.slots_available},"
            f" status={self.trade_status}, date_of_sale={self.date_of_sale})>"
        )


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

    class Meta:
        ordering = ["-slots_quantity"]

    def disburse(self):
        return Disbursement.objects.create(
            trade_unit=self,
            disbursement_status=DisbursementStates.Unsettled,
            amount=self.trade.return_on_trade_per_slot * self.slots_quantity + self.unit_value,
        )

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.share_percentage = self.slots_quantity / self.trade.slots_available * 100
        return super().save(*args, **kwargs)


class DisbursementStates(models.TextChoices):
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
    amount = models.DecimalField(decimal_places=5, editable=False, max_digits=10)
    transaction = models.OneToOneField(Transaction, on_delete=models.PROTECT, related_name="disbursement", null=True, blank=True)
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
    Inspection = "car_inspection", _("Car inspection pictures")
    Features = "feature", _("Picture of a feature of a car")
    InspectionReport = "inspection_report", _("Pdf report of an inspected vehicle")
    CarSparePart = "spare_part", _("Images of spare parts")


class Assets(Base):
    asset = models.URLField(null=False, blank=False)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey("content_type", "object_id")
    entity_type = models.CharField(choices=AssetEntityType.choices, max_length=20)

    @classmethod
    def create_many(cls, images: List[str], feature, entity_type: AssetEntityType):
        if isinstance(images, list) and images:
            ims = [Assets(id=uuid.uuid4(), content_object=feature, asset=image, entity_type=entity_type) for image in images]
            return Assets.objects.bulk_create(objs=ims)

    def __str__(self):
        return self.asset


class VehicleInfo(Base):
    vin = models.CharField(max_length=17, unique=True)
    engine = models.TextField()
    transmission = models.CharField(max_length=15, choices=CarTransmissionTypes.choices)
    car_type = models.CharField(choices=CarTypes.choices, max_length=30, null=True, blank=True)
    fuel_type = models.CharField(choices=FuelTypes.choices, max_length=30, null=False, blank=False)
    mileage = models.PositiveIntegerField(null=True, blank=True)
    age = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    trim = models.CharField(max_length=50, null=True, blank=False)
    manufacturer = models.CharField(max_length=50)
    brand = models.ForeignKey(CarBrand, on_delete=models.SET_NULL, null=True, blank=True)


class CarProductStatus(models.TextChoices):
    Active = "active", _(
        "Car is still in the market",
    )
    Sold = "sold", _("Car has been sold")
    Inactive = "inactive", _("Car has been recalled due to" " fault or other issues, or just added and not made active yet")


class CarProduct(Base):
    car = models.OneToOneField(Car, on_delete=models.CASCADE, related_name="product")
    selling_price = models.DecimalField(decimal_places=2, max_digits=25)
    highlight = models.CharField(max_length=100, help_text="A short description of the vehicle")
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
    notice_type = models.CharField(choices=NotificationTypes.choices, max_length=20)
    entity_id = models.UUIDField(null=True, blank=True)

    @atomic()
    def save(self, *args, **kwargs):
        return super().save(*args, **kwargs)


class InspectionVerdict(models.TextChoices):
    Great = "great", _("Average rating above 90 percentile")
    Good = "good", _("Average rating above 60 percentile up to 89")
    Fair = "fair", _("Average rating above 40 percentile up to 60")
    Bad = "bad", _("Average rating below 39 percentile")
    NA = "not_available", _("The default status for newly created inspection which is still pending.")


class Inspections(Base):
    owners_name = models.CharField(max_length=100)
    inspection_date = models.DateTimeField()
    owners_phone = models.CharField(
        max_length=20,
        validators=[
            PhoneNumberValidator,
        ],
    )
    owners_review = models.CharField(max_length=50, null=True, blank=True)
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


class Score(models.IntegerChoices):
    Good = 20
    Fair = 10
    Poor = 0


class Stages(models.TextChoices):
    Generic = "generic"
    Exterior = "exterior"
    Glass = "glass"
    Wheels = "wheels"
    UnderBody = "under_body"
    UnderHood = "under_hood"
    Interior = "interior"
    ElectricalSystems = "electrical_systems"
    RoadTest = "road_test"


class InspectionStage(Base):
    inspection = models.ForeignKey(Inspections, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(choices=Score.choices)
    part_name = models.CharField(max_length=50)
    stage_name = models.CharField(choices=Stages.choices, max_length=40)
    review = models.TextField(null=True, blank=True)


class Settings(Base):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    carpadi_trade_rot_percentage = models.DecimalField(decimal_places=2, max_digits=25)
    merchant_trade_rot_percentage = models.DecimalField(decimal_places=2, max_digits=25)
    transfer_fee = models.DecimalField(decimal_places=2, max_digits=25, default=Decimal(0.00))
    close_trade_fee = models.DecimalField(decimal_places=2, max_digits=25, default=Decimal(0.00))


class File(models.Model):
    THUMBNAIL_SIZE = (360, 360)

    file = models.FileField(blank=False, null=False)
    thumbnail = models.ImageField(blank=True, null=True)
    author = models.ForeignKey(User, related_name='files', on_delete=models.DO_NOTHING)
    created_at = models.DateTimeField(auto_now_add=True)
