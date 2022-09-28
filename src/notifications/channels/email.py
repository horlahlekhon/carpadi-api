from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class EmailChannel:
    @staticmethod
    def send(context, html_template, subject, to):

        pass
        # from src.common.tasks import send_notification_task
        #
        # send_notification_task.delay(subject, to, settings.EMAIL_FROM, email_html_message)
        # return
