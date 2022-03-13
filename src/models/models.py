import uuid
from django.db import models
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from rest_framework_simplejwt.tokens import RefreshToken
from easy_thumbnails.fields import ThumbnailerImageField
from django.urls import reverse
from django_rest_passwordreset.signals import reset_password_token_created
from easy_thumbnails.signals import saved_file
from easy_thumbnails.signal_handlers import generate_aliases_global
from model_utils.models import UUIDModel, TimeStampedModel

from src.common.helpers import build_absolute_uri
from src.notifications.services import notify, ACTIVITY_USER_RESETS_PASS
from django.contrib.auth import get_user_model

from django.utils.translation import gettext_lazy as _

@receiver(reset_password_token_created)
def password_reset_token_created(sender, instance, reset_password_token, *args, **kwargs):
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    """
    reset_password_path = reverse('password_reset:reset-password-confirm')
    context = {
        'username': reset_password_token.user.username,
        'email': reset_password_token.user.email,
        'reset_password_url': build_absolute_uri(f'{reset_password_path}?token={reset_password_token.key}'),
    }

    notify(ACTIVITY_USER_RESETS_PASS, context=context, email_to=[reset_password_token.user.email])


class Base(UUIDModel, TimeStampedModel):
    pass

    class Meta:
        abstract = True


class UserTypes(models.TextChoices):
    Admin = "admin", "admin"
    CarMerchant = "merchant", "merchant"


class User(AbstractUser, Base):
    profile_picture = ThumbnailerImageField('ProfilePicture', upload_to='profile_pictures/', blank=True, null=True)
    user_type = models.CharField(choices=UserTypes.choices, max_length=20, default=UserTypes.CarMerchant)

    def get_tokens(self):
        refresh = RefreshToken.for_user(self)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def __str__(self):
        return self.username


saved_file.connect(generate_aliases_global)


# Transactions
class Transactions(Base):
    wallet = models.UUIDField(default=uuid.uuid4, editable=False)
    amount = models.DecimalField(decimal_places=10, max_digits=10, editable=False)


# Wallet
class Wallets(Base):
    merchant = models.UUIDField(default=uuid.uuid4, editable=False)
    balance = models.DecimalField(decimal_places=10,  max_digits=16, editable=True)


class CarMerchant(Base):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="merchant")
    bvn = models.CharField(max_length=14)

    # class Meta:


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
    SUV = "suv", _("suv",)
    SALOON = "saloon", _("saloon",)
    MINIVAN = "minivan", _("minivan",)
    Convertible = "convertible", _("convertible",)
    MicroCar = "microcar", _("microcar",)
    CityCar = "city_car", _("City car",)
    Hatchback = "hatchback", _("Hatchback",)
    Sedan = "sedan", _("sedan",)
    FamilyCar = "family_car", _("Family car",)
    MuscleCar = "muscle_car", _("Muscle car")
    Roadster = "roadstar", _("Roadstar",)
    PickUp = "pickup", _("pickup",)
    Coupe = "coupe", _("coupe",)


class CarStates(models.TextChoices):
    FailedInspection = "failed_inspection", _("Failed Inspection",)
    Inspected = "inspected", _("inspected",)
    Available = "available", _("available",)
    Bought = "bought", _("bought",)
    Sold = "sold", _("sold",)


class Car(Base):
    brand = models.ForeignKey(CarBrand, on_delete=models.SET_NULL, null=True)
    status = models.CharField(choices=CarStates.choices, max_length=30)
    vin = models.CharField(max_length=17)
    pictures = models.URLField(help_text="url of the folder where the images for the car is located.")
    partitions = models.IntegerField(default=10, null=False, blank=False)
    car_inspector = models.OneToOneField(get_user_model(), on_delete=models.SET_NULL, null=True, blank=False)
    cost = models.DecimalField(decimal_places=10, editable=False, max_digits=10, max_length=10,
                               help_text="cost of  purchasing the car", null=False, blank=False)
    cost_of_repairs = models.DecimalField(decimal_places=10, editable=False, max_digits=10, max_length=10,
                                          help_text="Total cost of spare parts",  null=False, blank=False)
    total_cost = models.DecimalField(decimal_places=10, editable=False, null=False, blank=False, max_digits=10, max_length=10,
                                     help_text="Total cost = cost + cost_of_repairs + maintainance_cost + misc")
    maintainance_cost = models.DecimalField(decimal_places=10, editable=False, max_digits=10, max_length=10,
                                            help_text="fuel, parking, mechanic workmanship costs", null=False, blank=False)
    resale_price = models.DecimalField(decimal_places=10, max_digits=10, max_length=10,
                                       help_text="price presented to merchants", null=True, blank=True)
    # TODO change to a full fledge model
    inspection_report = models.TextField()
    buy_to_sale_time = models.IntegerField(editable=False)
    margin = models.DecimalField(decimal_places=10, editable=False, max_digits=10, max_length=10,
                                 help_text="The profit that was made from car "
                                           "after sales in percentage of the total cost")
    car_type = models.CharField(choices=CarTypes.choices, max_length=30, null=False, blank=False)


