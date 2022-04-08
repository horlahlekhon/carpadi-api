import datetime
import random
from collections import defaultdict
from django.db.models import signals

from src.common.helpers import build_absolute_uri
from src.models.models import Activity, ActivityTypes, User, Otp, UserTypes
from src.notifications.services import notify, USER_PHONE_VERIFICATION, ACTIVITY_USER_RESETS_PASS
from django_rest_passwordreset.models import ResetPasswordToken
from src.config.common import OTP_EXPIRY


class DisableSignals(object):
    """
    A class used to disable signals on the enclosed block of code.
    Usage:
      with DisableSignals():
        ...
    """

    def __init__(self, disabled_signals=None):
        self.stashed_signals = defaultdict(list)
        self.disabled_signals = disabled_signals or [
            signals.pre_init,
            signals.post_init,
            signals.pre_save,
            signals.post_save,
            signals.pre_delete,
            signals.post_delete,
            signals.pre_migrate,
            signals.post_migrate,
            signals.m2m_changed,
        ]

    def __enter__(self):
        for signal in self.disabled_signals:
            self.disconnect(signal)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for signal in list(self.stashed_signals):
            self.reconnect(signal)

    def disconnect(self, signal):
        self.stashed_signals[signal] = signal.receivers
        signal.receivers = []

    def reconnect(self, signal):
        signal.receivers = self.stashed_signals.get(signal, [])
        del self.stashed_signals[signal]


from django_rest_passwordreset.tokens import RandomNumberTokenGenerator


def complete_user_registeration(sender, **kwargs):
    user: User = kwargs.get("instance")
    if kwargs.get("created"):
        if user.user_type == UserTypes.CarMerchant:
            # otp = RandomNumberTokenGenerator(min_number=100000, max_number=999999).generate_token()
            expiry = datetime.datetime.now() + datetime.timedelta(minutes=OTP_EXPIRY)
            ot = Otp.objects.create(otp="123456", expiry=expiry, user=user)
            context = dict(username=user.username, otp=ot.otp)
            # notify(
            #     USER_PHONE_VERIFICATION,
            #     context=context,
            #     email_to=[
            #         user.email,
            #     ],
            # )


# def send_reset_password_token(sender, **kwargs):
#     token: ResetPasswordToken = kwargs.get("reset_password_token")
#     if token:
#         otp = random.randrange(100000, 999999)
#         token.key = otp
#         token.save(update_fields=["key"])
#         context = dict(username=user.username, otp=ot.otp)
#         notify(PASSWORD_RESET_TOKEEN, context=context, email_to=[user.email, ])
from django.urls import reverse


def password_reset_token_created(sender, instance, reset_password_token: ResetPasswordToken, *args, **kwargs):
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    """
    # otp = random.randrange(100000, 999999)
    # reset_password_token.key = otp
    # reset_password_token.save(update_fields=["key"])
    # reset_password_token.refresh_from_db()
    reset_password_path = reverse('password_reset:reset-password-confirm')
    ResetPasswordToken.objects.filter(key="123456").delete() # TOdo remember to remove this coder abeg.
    # reset_password_token.key = "123456"  # TOdo remember to remove this coder abeg.
    # reset_password_token.save(update_fields=["key"])
    ResetPasswordToken.objects.create( # TOdo remember to remove this coder abeg.
        user=reset_password_token.user,
        user_agent=reset_password_token.user_agent,
        ip_address=reset_password_token.ip_address,
        key="123456",
    )
    context = {
        'username': reset_password_token.user.username,
        'email': reset_password_token.user.email,
        'reset_password_url': build_absolute_uri(f'{reset_password_path}?token={reset_password_token.key}'),
        'token': "123456"  # reset_password_token.key,
    }

    # notify(ACTIVITY_USER_RESETS_PASS, context=context, email_to=[reset_password_token.user.email])

# Signals for post_save signal for activity
def transaction_completed(sender, instance):
    Activity.activity_type = ActivityTypes.Transaction
    Activity.activity = instance
    Activity.save()

def trade_unit_completed(sender, instance, **kwargs):
    Activity.activity_type = ActivityTypes.TradeUnit
    Activity.activity = instance
    Activity.save()

def disbursement_completed(sender, instance, **kwargs):
    Activity.activity_type = ActivityTypes.Disbursement
    Activity.activity = instance
    Activity.save()

# Signals for post_save signal for activity End
