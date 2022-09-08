from django.template.loader import render_to_string
from fcm_django.models import FCMDevice

from src.models.models import User

from firebase_admin.messaging import Message, Notification


class FirebaseChannel:
    @staticmethod
    def send(context, html_template, subject, to: FCMDevice):
        data = render_to_string(html_template, context)
        no = Notification(title=subject, body=data)
        msg = Message(notification=no)
        resp = to.send_message(message=msg)
        print(resp)
