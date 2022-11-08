from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import mailchimp_transactional as MailchimpTransactional
from mailchimp_transactional.api_client import ApiClientError


class EmailChannel:
    @staticmethod
    def send(context, html_template, subject, to):
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

    @staticmethod
    def send_mail_mailchimp(context, html_template, subject, to):
        email_html_message = render_to_string(html_template, context)
        message = {
            "from_email": settings.MAILCHIMP_FROM,
            "from_name": "Carpadi",
            "subject": subject,
            "html": email_html_message,
            "to": [{"email": to, "type": "to"}],
        }

        try:
            mailchimp = MailchimpTransactional.Client(settings.MAILCHIMP_API_KEY)
            response = mailchimp.messages.send({"message": message})
            print(response)
        except ApiClientError as error:
            print("An exception occurred: {}".format(error.text))
