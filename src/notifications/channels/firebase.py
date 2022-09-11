import json
import logging

from fcm_django.models import FCMDevice, FCMDeviceQuerySet, FirebaseResponseDict
from firebase_admin.messaging import Message, Notification

from src.config.common import APP_ENV
from src.models.models import User

logger = logging.getLogger(__name__)


class FirebaseChannel:
    @staticmethod
    def send(context, to: str):
        devices: FCMDeviceQuerySet = FCMDevice.objects.filter(user_id=to)
        no = Notification(title=context.get('title'), body=json.dumps(context))
        msg = Message(notification=no, data=context)
        resp: FirebaseResponseDict = devices.send_message(
            message=msg,
            dry_run=APP_ENV
            not in [
                "test",
            ],
        )
        print(f"Notification sent {resp}")

    @staticmethod
    def send_all(context):
        ...
