import json
from pprint import pprint
from typing import Callable
from django.conf import settings

import mailchimp_transactional as MailchimpTransactional
from celery import task
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from fcm_django.models import FCMDeviceQuerySet, FCMDevice, FirebaseResponseDict
from firebase_admin.messaging import Notification, Message
from mailchimp_transactional.api_client import ApiClientError

# from django.core.mail import EmailMultiAlternatives
from src.common.utils import CustomJsonEncoder
from src.models.models import Transaction


@task(name='SendEmailNotification')
def send_email_notification_task(context, html_template, subject, to):
    try:
        if isinstance(to, str):
            to = [to]
        email_html_message = render_to_string(html_template, context)
        # if settings.TESTING:
        msg = EmailMultiAlternatives(
            subject,
            email_html_message,
            settings.EMAIL_FROM,
            to,
            alternatives=((email_html_message, 'text/html'),),
        )
        resp = msg.send()
        print(resp)
    except Exception as error:
        print(f"An exception occurred: {error}")


@task(name='SendPushNotification')
def send_push_notification_task(context, to: str):
    try:
        devices: FCMDeviceQuerySet = FCMDevice.objects.filter(user_id=to)
        body = json.loads(json.dumps(context, cls=CustomJsonEncoder))
        pprint(body)
        no = Notification(title=context.get('title'), body=context.get('title'))
        msg = Message(notification=no, data=body)
        pprint(f"sending: \n {str(msg)}")
        resp: FirebaseResponseDict = devices.send_message(
            message=msg,
        )
        print(f"Notification sent success: {resp.response.success_count}, failure: {resp.response.failure_count}")
        return f"Notification sent success: {resp.response.success_count}, failure: {resp.response.failure_count}"
    except Exception as error:
        print(f"An exception occurred: {error}")


def send_push_notification_taskp(context, to: str):
    try:
        devices: FCMDeviceQuerySet = FCMDevice.objects.filter(user_id=to)
        body = json.loads(json.dumps(context, cls=CustomJsonEncoder))
        pprint(body)
        no = Notification(title=context.get('title'), body=context.get('title'))
        msg = Message(notification=no, data=body)
        pprint(f"sending: \n {str(msg)}")
        resp: FirebaseResponseDict = devices.send_message(
            message=msg,
        )
        print(f"Notification sent success: {resp.response.success_count}, failure: {resp.response.failure_count}")
        return f"Notification sent success: {resp.response.success_count}, failure: {resp.response.failure_count}"
    except Exception as error:
        print(f"An exception occurred: {error}")


def send_email_notification_taskp(context, html_template, subject, to):
    try:
        if isinstance(to, str):
            to = [to]
        email_html_message = render_to_string(html_template, context)
        # if settings.TESTING:
        msg = EmailMultiAlternatives(
            subject,
            email_html_message,
            settings.EMAIL_FROM,
            to,
            alternatives=((email_html_message, 'text/html'),),
        )
        resp = msg.send()
        print(resp)
        return resp
    except Exception as error:
        print(f"An exception occurred: {error}")


@task(name='CloseTradeTask')
def close_trade(trade):
    ...
