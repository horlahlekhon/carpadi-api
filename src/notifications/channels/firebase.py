import json
import logging
from pprint import pprint

from fcm_django.models import FCMDevice, FCMDeviceQuerySet, FirebaseResponseDict
from firebase_admin.messaging import Message, Notification

from src.common.utils import CustomJsonEncoder
from src.config.common import APP_ENV
from src.models.models import User

logger = logging.getLogger(__name__)


class FirebaseChannel:
    @staticmethod
    def send(context, to: str):
        # def send_notice():
        #
        # from src.common.tasks import send_notification_task
        # send_notification_task.delay(send_notice)
        # return
        pass

    @staticmethod
    def send_all(context):
        ...
