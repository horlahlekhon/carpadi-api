import json
import logging
from pprint import pprint
from typing import Union

from fcm_django.models import FCMDevice, FCMDeviceQuerySet, FirebaseResponseDict
from firebase_admin.messaging import Message, Notification

from src.common.utils import CustomJsonEncoder
from src.config.common import APP_ENV
from src.models.models import User, LoginSessions

logger = logging.getLogger(__name__)
from fcm_django.models import FCMDeviceQuerySet, FCMDevice
from firebase_admin.exceptions import FirebaseError
from firebase_admin.messaging import Notification, Message, SendResponse, AndroidConfig, AndroidNotification


class FirebaseChannel:
    @staticmethod
    def send(context, to: list):
        sessions = {LoginSessions.objects.filter(user=i).latest("created").device_imei for i in to}
        devices = []
        for sess in sessions:
            if dev := FCMDevice.objects.filter(device_id=sess, active=True).order_by("date_created").first():
                devices.append(dev)
        context["sender"] = "Emeka from Carpadi"
        body = {k: str(v) for k, v in context.items()}
        no = AndroidNotification(
            click_action="FLUTTER_NOTIFICATION_CLICK",
        )
        android = AndroidConfig(
            notification=no,
        )
        notice = Notification(title=context.get('title'), body=context.get("message"))
        success = 0
        failed = 0
        for device in devices:
            msg = Message(token=device.registration_id, android=android, notification=notice, data=body)
            logger.info(f"sending: \n {str(msg)}")
            resp: Union[SendResponse, None, FirebaseError] = device.send_message(
                message=msg,
            )
            if isinstance(resp, FirebaseError):
                logger.info(f"Notification sending failed : {resp}")
                failed += 1
            if isinstance(resp, SendResponse) and resp.success:
                logger.info(f"Notification sent success: {resp.success}")
                success += 1
            else:
                logger.info(f"invalid response type: {resp}, but we are gonna go with failed and move on")
                failed += 1
        return f"Notification sent:  success => {success}, failure: {failed}"

    @staticmethod
    def send_all(context):
        ...
