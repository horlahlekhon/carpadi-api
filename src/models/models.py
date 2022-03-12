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


class CarMerchant(Base):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name="merchant")
    bvn = models.CharField(max_length=14)

    # class Meta:


class BankAccount(Base):
    name = models.CharField(max_length=100)
    bank_name = models.CharField(max_length=50)
    account_number = models.CharField(max_length=10)
    merchant = models.ForeignKey(
        CarMerchant, on_delete=models.CASCADE, related_name="bank_accounts", help_text="Bank account to remit merchant money to"
    )

class Wallet(Base):
    merchant = models.ForeignKey(CarMerchant, on_delete=models.PROTECT, help_text='the merchant that owns the wallet')
    balance = models.DecimalField(decimal_places=6, max_digits=16, editable=True)


class Transactions(Base):
    wallet = models.ForeignKey(Wallet,on_delete=models.PROTECT, help_text='the wallet which is used to carryout the transactions')
    amount = models.DecimalField(decimal_places=6, max_digits=16, editable=False)
