import json

from django.template.loader import render_to_string
from fcm_django.models import FCMDevice

from src.models.models import User

from firebase_admin.messaging import Message, Notification


class FirebaseChannel:
    @staticmethod
    def send(context, subject, to: FCMDevice):
        # data = render_to_string(html_template, context)
        no = Notification(title=subject, body=json.dumps(context))
        msg = Message(notification=no)
        resp = to.send_message(message=msg)
        print(resp)
        # {
        #     "notice_type": "trade_unit",
        #     "entity_id": "id",
        #     "message": "2 units have been bought from Acura MDX"
        # }
