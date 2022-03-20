import datetime
import random
from collections import defaultdict
from django.db.models import signals

from src.models.models import User, Otp, CarMerchant, UserTypes
from src.notifications.services import notify, USER_PHONE_VERIFICATION


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


def complete_user_registeration(sender, **kwargs):
    user: User = kwargs.get("instance")
    if kwargs.get("created"):
        if user.user_type == UserTypes.CarMerchant:
            otp = random.randrange(100000, 999999)
            expiry = datetime.datetime.now() + datetime.timedelta(minutes=10)
            ot = Otp.objects.create(otp=otp, expiry=expiry, user=user)
            context = dict(username=user.username, otp=ot.otp)
            CarMerchant.objects.create(user=user)
            notify(
                USER_PHONE_VERIFICATION,
                context=context,
                email_to=[
                    user.email,
                ],
            )
