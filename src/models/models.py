from statistics import mode
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

from src.common.helpers import build_absolute_uri
from src.notifications.services import notify, ACTIVITY_USER_RESETS_PASS


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


class Base(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ts_created = models.DateTimeField(auto_created=True, auto_now_add=True)
    ts_updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class User(AbstractUser, Base):
    # id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile_picture = ThumbnailerImageField('ProfilePicture', upload_to='profile_pictures/', blank=True, null=True)

    def get_tokens(self):
        refresh = RefreshToken.for_user(self)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }

    def __str__(self):
        return self.username


saved_file.connect(generate_aliases_global)


# class Car(Base):

class CarBrand(Base):
    name = models.TextField(max_length=80)
    year = models.IntegerField()
    model = models.TextField(max_length=80)

    def __str__(self):
        return self.name + " " + self.model


class Car(Base):
    type = models.TextField(max_length=80)
    brand = models.ForeignKey(CarBrand)
    status = models.enums
    vin = models.TextField(max_length=80)
    costOfCar = models.FloatField()
    projectedSalePrice = models.FloatField()
    sharesAvailable = models.IntegerField()
    sharesPurchased = models.IntegerField()

    def __str__(self):
        return self.brand