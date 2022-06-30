from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

import mailchimp_transactional as MailchimpTransactional
from mailchimp_transactional.api_client import ApiClientError

from src.config.common import EMAIL_FROM
from src.config.common import EMAIL_API_KEY

class EmailChannel:
    @staticmethod
    def send(context, html_template, subject, to):
        if isinstance(to, str):
            to = [{"email": to, "type": "to"}]

        email_html_message = render_to_string(html_template, context)

        if settings.TESTING:
            try:
                mailchimp = MailchimpTransactional.Client(EMAIL_API_KEY)
                response = mailchimp.messages.send({"message": {
                                                                "from_email": EMAIL_FROM,
                                                                "from_name": "Carpadi Admin",
                                                                "subject": subject,
                                                                "html": email_html_message,
                                                                "to": to
                                                            }})
                                                            
                print(response)
            except ApiClientError as error:
                print("An exception occurred: {}".format(error.text))

        # from src.common.tasks import send_email_task

        # send_email_task.delay(subject, to, settings.EMAIL_FROM, email_html_message)
        # return
