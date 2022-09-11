import logging
from abc import ABC

from actstream import action
from fcm_django.models import FCMDevice

from src.models.models import User
from src.notifications.channels.email import EmailChannel
from src.notifications.channels.firebase import FirebaseChannel

logger = logging.getLogger(__name__)

ACTIVITY_USER_RESETS_PASS = 'started password reset process'
USER_PHONE_VERIFICATION = "VERIFY PHONE"
# PASSWORD_RESET_TOKEEN = "RESEET"
NOTIFICATIONS = {
    ACTIVITY_USER_RESETS_PASS: {
        "notice_type": "password_reset",
        'email': {
            'email_subject': 'Password Reset',
            'email_html_template': 'emails/user_reset_password.html',
        },
    },
    USER_PHONE_VERIFICATION: {
        "notice_type": "new_user",
        'email': {
            'email_subject': 'Verify phone',
            'email_html_template': 'emails/verify_phone.html',
        },
    },
    'TRADE_UNIT_PURCHASE': {
        "notice_type": "trade_unit",
        "in_app": {'message': 'You have successfully bought {} units from the car {}', "title": "New unit purchased"},
        "email": {
            'email_subject': 'New unit purchased',
            'email_html_template': 'emails/trade_unit_purchase.html',
        },
    },
    'NEW_TRADE': {
        "notice_type": "new_trade",
        "in_app": {'message': 'A new trade was just added', "title": "New trade"},
        "email": {
            'email_subject': 'New trade',
            'email_html_template': 'emails/new_trade.html',
        },
    },
    'DISBURSEMENT': {
        "notice_type": "disbursement",
        "in_app": {'message': 'You have a new return on trade disbursement', "title": "ROT disbursement"},
        "email": {
            'email_subject': 'ROT disbursement',
            'email_html_template': 'emails/disbursement.html',
        },
    }
    # PASSWORD_RESET_TOKEN
}


def _send_email(email_notification_config, context, to):
    email_html_template = email_notification_config.get('email_html_template')
    email_subject = email_notification_config.get('email_subject')
    EmailChannel.send(context=context, html_template=email_html_template, subject=email_subject, to=to)


def _send_firebase(notification_config, context):
    FirebaseChannel.send(context, context.get("user"))


def notify(verb, **kwargs):
    notification_config = NOTIFICATIONS.get(verb)
    if "email" in notification_config.keys():
        email_notification_config = notification_config.get('email')
        context = kwargs.get('context', {})
        email_to = kwargs.get('email_to', [])
        if not email_to:
            logger.debug('Please provide list of emails (email_to argument).')
        _send_email(email_notification_config, context, email_to)
    if "in_app" in notification_config.keys():
        _send_firebase(notification_config, kwargs)


# Use only with actstream activated
def send_action(sender, verb, action_object, target, **kwargs):
    action.send(sender=sender, verb=verb, action_object=action_object, target=target)
    notify(verb, **kwargs)
