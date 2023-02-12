import datetime
import logging
from collections import defaultdict
from typing import List

from django.db.models import signals
from django_rest_passwordreset.models import ResetPasswordToken

from src.carpadi_api.serializers import TransactionSerializer, TradeUnitSerializer
from src.common.helpers import build_absolute_uri
from src.config.common import OTP_EXPIRY
from src.models.models import (
    Disbursement,
    TradeUnit,
    User,
    Otp,
    UserTypes,
    Transaction,
    TransactionStatus,
    Activity,
    ActivityTypes,
    Trade,
    TradeStates,
    Notifications,
    NotificationTypes,
    Car,
    Wallet,
    CarMerchant,
    MerchantStatusChoices,
    LoginSessions, TransactionKinds,
)
from src.notifications.channels.firebase import FirebaseChannel
from src.notifications.services import notify, USER_PHONE_VERIFICATION, ACTIVITY_USER_RESETS_PASS

logger = logging.getLogger(__name__)


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
    if kwargs.get("created") and user.user_type == UserTypes.CarMerchant:
        context = dict(
            username=user.get_full_name(), email=user.email, users=[user],
            firstname=user.first_name, lastname=user.last_name,
            phone=user.phone
        )
        notify("WELCOME_USER", **context)


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
    ResetPasswordToken.objects.filter(key="123456").delete()  # TOdo remember to remove this code abeg.
    # reset_password_token.key = "123456"  # TOdo remember to remove this coder abeg.
    # reset_password_token.save(update_fields=["key"])
    ResetPasswordToken.objects.create(  # TOdo remember to remove this coder abeg.
        user=reset_password_token.user,
        user_agent=reset_password_token.user_agent,
        ip_address=reset_password_token.ip_address,
        key="123456",
    )
    context = {
        'username': reset_password_token.user.username,
        'email': reset_password_token.user.email,
        'reset_password_url': build_absolute_uri(f'{reset_password_path}?token={reset_password_token.key}'),
        'token': "123456",  # reset_password_token.key,
        'user': reset_password_token.user.id,
    }

    notify(ACTIVITY_USER_RESETS_PASS, context=context, users=[reset_password_token.user])


def complete_transaction(sender, **kwargs):
    tx: Transaction = kwargs.get("instance")
    if kwargs.get("created"):
        if tx.transaction_status == TransactionStatus.Success:
            context = {
                'username': tx.wallet.merchant.user.username,
                'email': tx.wallet.merchant.user.email,
                'amount': tx.amount,
            }
            print("transaction successful")

            # notify(ACTIVITY_MERCHANT_PAYMENT_SUCCESS, context=context, email_to=[tx.wallet.merchant.user.email])
    # if tx.transaction_status in (
    #     TransactionStatus.Success,
    #     TransactionStatus.Failed,
    # ):
    #     activity = Activity.objects.create(
    #         activity_type=ActivityTypes.Transaction,
    #         activity=tx,
    #         description=f"Activity Type: Transaction, Status: {tx.transaction_status}, Description: {tx.transaction_kind} of {tx.amount} naira.",
    #         merchant=tx.wallet.merchant,
    #     )
    #     Notifications.objects.create(
    #         notice_type=NotificationTypes.TradeUnit,
    #         user=tx.wallet.merchant.user,
    #         message=f"Transaction {tx.transaction_kind} of {tx.amount} naira has {tx.transaction_status}.",
    #         is_read=False,
    #     )


def trade_unit_completed(sender, instance: TradeUnit, created, **kwargs):
    """
    Handles trade unit creation completion. it handles things like creation of activity for the trade unit
    check if trade has been fully purchased and update Trade state accordingly
    and also sends an email to the merchant
    """
    if created:
        activity = Activity.objects.create(
            activity_type=ActivityTypes.TradeUnit,
            activity=instance,
            merchant=instance.merchant,
            description=f"Activity Type: Purchase of Unit, Description: "
            f"{instance.slots_quantity} ({instance.share_percentage})  of \
                    {instance.trade.car.information.brand.name}"
            f" {instance.trade.car.information.brand.model}"
            f" VIN: {instance.trade.car.vin} valued at {instance.unit_value} naira only.",
        )
        Notifications.objects.create(
            notice_type=NotificationTypes.TradeUnit,
            user=instance.merchant.user,
            message=f"Activity Type: Purchase of Unit Description: "
            f"{instance.slots_quantity} ({instance.share_percentage})  of \
                                {instance.trade.car.information.brand.name}"
            f" {instance.trade.car.information.brand.model}"
            f" VIN: {instance.trade.car.vin} valued at {instance.unit_value} naira only.",
            is_read=False,
            entity_id=instance.id,
        )
        trade: Trade = instance.trade
        if trade.slots_available == trade.slots_purchased():
            trade.trade_status = TradeStates.Purchased
            trade.save(update_fields=["trade_status"])
        # ctx = dict(id=instance.id)
        # notify('TRADE_UNIT_PURCHASE', )


def disbursement_completed(disbursements: List[Disbursement]):
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
            user=dis.trade_unit.merchant.user
        )


#         update trade status

# def notify(sender, instance: Notifications, created, **kwargs):
#     if created:
#         if instance.notice_type == NotificationTypes.PasswordReset:
#             trade = Trade.objects.get(id=instance.entity_id)
#             context = {
#                 'username': trade.merchant.user.username,
#                 'email': trade.merchant.user.email,
#                 'amount': trade.amount,


def trade_created(sender, instance: Trade, created, **kwargs):
    if created:
        Notifications.objects.create(
            notice_type=NotificationTypes.NewTrade,
            user=None,
            message=f" new trade for {instance.car.information.brand.name} {instance.car.information.brand.model}"
            f" VIN: {instance.car.vin} with estimated ROT of {instance.return_on_trade_per_slot}",
            is_read=False,
            entity_id=instance.id,
        )


def car_created(sender, instance: Car, created, **kwargs):
    if created:
        activity = Activity.objects.create(
            activity_type=ActivityTypes.CarCreation,
            activity=instance,
            merchant=None,
            description=f"Activity Type: Car Creation, Description: Created Car - {instance.description}"
            f"with information {instance.information}"
            f"VIN {instance.vin}",
        )


def wallet_created(sender, instance: Wallet, created, **kwargs):
    if created:
        Activity.objects.create(
            activity_type=ActivityTypes.NewUser,
            activity=instance,
            merchant=instance.merchant,
            description=f"Activity Type: New user, Description: {instance.merchant.user.username} just joined carpadi",
        )


def notifications(sender, instance: Notifications, created, **kwargs):
    if created:
        #  TODO add more specific context based on the notification,
        #   i.e disbursement will render a receipt, so data needs to be more than this
        context = dict(
            notice_type=instance.notice_type,
            title=instance.title,
            notice_id=str(instance.id),
            entity=str(instance.entity_id),
            message=instance.message,
            users=[],
        )
        if instance.notice_type == NotificationTypes.TradeUnit:
            unit = TradeUnit.objects.get(id=instance.entity_id)
            context["slot_quantity"] = unit.slots_quantity
            context["car"] = unit.trade.car.name
            context["total"] = unit.unit_value
            context["users"] = [instance.user]
            context["trade_start_date"] = unit.trade.created
            notify('TRADE_UNIT_PURCHASE', **context)
        elif instance.notice_type == NotificationTypes.NewTrade:
            users = {i.user for i in LoginSessions.objects.order_by("device_imei").distinct("device_imei")}
            context["users"] = users
            notify('NEW_TRADE', **context)
        elif instance.notice_type == NotificationTypes.Disbursement:
            disburse = Disbursement.objects.get(id=instance.entity_id)
            context["slot_quantity"] = disburse.trade_unit.slots_quantity
            context["amount"] = disburse.amount
            context["trade_start_date"] = disburse.trade_unit.trade.created
            context["trade_completion_date"] = disburse.created
            duration = disburse.created - disburse.trade_unit.trade.created
            context["duration"] = duration.days
            context["disbursement_date"] = disburse.created
            context["car"] = disburse.trade_unit.trade.car.name
            context["users"] = [instance.user]
            # context["rot"] = disburse
            notify('DISBURSEMENT', **context)
        elif instance.notice_type == NotificationTypes.TransactionCompleted:
            transaction = Transaction.objects.get(id=instance.entity_id)
            context["transaction_amount"] = transaction.amount
            context["transaction_status"] = transaction.transaction_status
            context["transaction_kind"] = transaction.transaction_kind
            context["transaction_type"] = transaction.transaction_type
            context["transaction_description"] = transaction.transaction_description
            context["transaction_fees"] = transaction.transaction_fees
            context["transaction_date"] = transaction.created
            context["ref"] = transaction.transaction_reference
            context["users"] = [instance.user]
            if transaction.transaction_kind == TransactionKinds.Deposit and transaction.transaction_status ==  TransactionStatus.Success: # noqa
                notify("WALLET_DEPOSIT", **context)
            elif transaction.transaction_kind == TransactionKinds.Withdrawal and transaction.transaction_status ==  TransactionStatus.Success: # noqa
                notify("WALLET_WITHDRAWAL", **context)
            elif transaction.transaction_status ==  TransactionStatus.Failed:
                notify('TRANSACTION_FAILED', **context)
            else:
                notify('TRANSACTION_COMPLETED', **context)
        else:
            logger.info("Notification type is not implemented yet")



class Anonymous:

    def __init__(self, email, phone=None, username=None):
        self.email = email
        self.username = username
        self.phone = phone


def send_otp(sender, instance: Otp, created, **kwargs):
    if created and instance:
        user = instance.user
        notice = "USER_EMAIL_VERIFICATION"
        context = dict(otp=instance.otp, users=[user or Anonymous(email=instance.email, phone=instance.phone)])
        if instance.user:
            context["username"] = user.username
            context["email"] = user.email
        # TODO uncomment this when we impl sms
        # elif instance.phone:
        #     context["phone"] = instance.phone
        #     notice = USER_PHONE_VERIFICATION
        else:
            context["email"] = instance.email
        notify(notice, **context)
