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
        "type": "email",
        'email': {
            'email_subject': 'Password Reset',
            'email_html_template': 'emails/user_reset_password.html',
        },
    },
    USER_PHONE_VERIFICATION: {
        "type": "email",
        'email': {
            'email_subject': 'Verify phone',
            'email_html_template': 'emails/verify_phone.html',
        },
    },
    'TRADE_UNIT_PURCHASE': {
        "type": "in_app",
        "notice_type": "trade_unit",
        'firebase': {'message': 'You have successfully bought {} units from the car {}'},
    }
    # PASSWORD_RESET_TOKEEN
}


def _send_email(email_notification_config, context, to):
    email_html_template = email_notification_config.get('email_html_template')
    email_subject = email_notification_config.get('email_subject')
    EmailChannel.send(context=context, html_template=email_html_template, subject=email_subject, to=to)


def _send_firebase(notification_config, context):
    # to: User = context.get("user")
    subject = notification_config.get("message")
    context["notice_type"] = notification_config.get("notice_type")
    device = FCMDevice.objects.get(user_id=context.get("user"))
    FirebaseChannel.send(context, subject, device)


def notify(verb, **kwargs):
    if notification_config := NOTIFICATIONS.get(verb):
        if notification_config.get('type') == "email":
            email_notification_config = notification_config.get('email')
            context = kwargs.get('context', {})
            email_to = kwargs.get('email_to', [])
            if not email_to:
                logger.debug('Please provide list of emails (email_to argument).')
            _send_email(email_notification_config, context, email_to)
        elif notification_config.get('type') == "in_app":
            _send_firebase(notification_config, kwargs.get("context"))


# Use only with actstream activated
def send_action(sender, verb, action_object, target, **kwargs):
    action.send(sender=sender, verb=verb, action_object=action_object, target=target)
    notify(verb, **kwargs)
