from decimal import Decimal
from pprint import pprint
from typing import Union

from celery import task, Celery, shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from fcm_django.models import FCMDeviceQuerySet, FCMDevice
from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import Notification, Message, SendResponse, AndroidConfig, AndroidNotification

# from django.core.mail import EmailMultiAlternatives
from src.models.models import Car, CarStates, CarDocuments
from src.notifications.channels.email import EmailChannel
from src.notifications.channels.firebase import FirebaseChannel

logger = get_task_logger(__name__)


@task(name='SendEmailNotification')
def send_email_notification_task(context, html_template, subject, to):
    try:
        return EmailChannel.send_mail_mailchimp(context, html_template, subject, to)
    except Exception as error:
        logger.error(f"An exception occurred: {error}")


@task(name='SendPushNotification')
def send_push_notification_task(context, to: str):
    try:
        return FirebaseChannel.send(context, to)
    except Exception as error:
        logger.error(f"An exception occurred: {error}")


def send_push_notification_taskp(context, to: list):
    try:
        return FirebaseChannel.send(context, to)
    except Exception as error:
        print(f"An exception occurred: {error}")
        raise


def send_email_notification_taskp(context, html_template, subject, to):
    try:
        EmailChannel.send_mail_mailchimp(context, html_template, subject, to)
    except Exception as error:
        print(f"An exception occurred: {error}")


@task(name='CloseTradeTask')
def close_trade(trade):
    ...


@shared_task
def check_cars_with_completed_documentations():
    cars = Car.objects.filter(status__in=(CarStates.Inspected,))
    updated = 0
    for car in cars:
        docs = CarDocuments.documentation_completed(car.id)
        if docs and car.bought_price > Decimal(0.00):
            car.status = CarStates.Available
            car.save(update_fields=["status"])
            updated += 1
    logger.info(f"Updated {updated} cars to available for trade....")
    return updated
