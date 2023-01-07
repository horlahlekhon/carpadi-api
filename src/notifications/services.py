import logging

from actstream import action
from django.conf import settings

from src.common.tasks import send_email_notification_taskp, send_push_notification_taskp
from src.models.models import User

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
        'text_messages': {
            'email_subject': 'Verify phone',
            'email_html_template': 'text_messages/verify_phone.html',
        },
    },
    "USER_EMAIL_VERIFICATION": {
        "notice_type": "email_verification",
        'email': {
            'email_subject': 'Email verification',
            'email_html_template': 'emails/verify_email.html',
        },
    },
    "WELCOME_USER": {
        "notice_type": "new_user",
        'email': {
            'email_subject': 'Welcome To Carpadi',
            'email_html_template': 'emails/user_welcome.html',
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
    },
    'TRANSACTION_COMPLETED': {
        "notice_type": "transaction",
        "in_app": {'message': 'Your Transaction have been completed', "title": "Transaction completed"},
        "email": {
            'email_subject': 'Transaction completed',
            'email_html_template': 'emails/transactions.html',
        },
    },
    'TRANSACTION_FAILED': {
        "notice_type": "transaction",
        "in_app": {'message': 'Your Transaction have failed', "title": "Transaction failure"},
        "email": {
            'email_subject': 'Transaction completed',
            'email_html_template': 'emails/transactions.html',
        },
    }
    # PASSWORD_RESET_TOKEN
}


def _send_email(email_notification_config, context):
    to = context.get("email_to")
    if not to:
        raise Exception("Please provide email addresses to send email to")
    email_html_template = email_notification_config.get('email_html_template')
    email_subject = email_notification_config.get('email_subject')
    from src.common.tasks import send_email_notification_task

    # send_email_notification_task.delay(context, email_html_template, email_subject, to)
    send_email_notification_taskp(context, email_html_template, email_subject, to)


def _send_firebase(notification_config, context):
    from src.common.tasks import send_push_notification_task

    send_push_notification_task.delay(context, context.get("user"))
    # send_push_notification_taskp(context, context.get("user"))

# fixme review the configuration of this function, especially how email recipient
#  is beeing supplied. compose it, there is too much variants. probably consider
#  passing a receipeint resolution function. that get the receipient given a notification action
def notify(verb, **kwargs):
    notification_config = NOTIFICATIONS.get(verb)
    if not settings.TESTING:
        if "email" in notification_config.keys():
            email_notification_config = notification_config.get('email')
            if usr := kwargs.get('user'):
                email_to = User.objects.filter(id=usr).first().email
                if not email_to:
                    raise Exception(f"User with Id: {usr} does not exist")
            elif email := kwargs.get('email'):
                email_to = email
            elif to := kwargs.get("email_to"):
                email_to = to
            else:
                raise Exception("Could not determine who to send email to from. please contact the admin")
            if not email_to:
                logger.debug('Please provide list of emails (email_to argument).')
            kwargs["email_to"] = email_to
            _send_email(email_notification_config, kwargs)
        if "in_app" in notification_config.keys():
            _send_firebase(notification_config, kwargs)
    return None


# Use only with actstream activated
def send_action(sender, verb, action_object, target, **kwargs):
    action.send(sender=sender, verb=verb, action_object=action_object, target=target)
    notify(verb, **kwargs)
