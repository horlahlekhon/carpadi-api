from pprint import pprint

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
import mailchimp_transactional as MailchimpTransactional
from mailchimp_transactional.api_client import ApiClientError
import time
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException


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
            "to": [{"email": i, "type": "to"} for i in to],
        }
        try:
            mailchimp = MailchimpTransactional.Client(settings.MAILCHIMP_API_KEY)
            response = mailchimp.messages.send({"message": message})
            print(response)
        except ApiClientError as error:
            print("An exception occurred: {}".format(error.text))

    @staticmethod
    def send_mail_sib(context, html_template, subject, to):
        configuration = sib_api_v3_sdk.Configuration()
        email_html_message = render_to_string(html_template, context)
        configuration.api_key[
            'api-key'] = settings.SIB_API_KEY
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(sib_api_v3_sdk.ApiClient(configuration))
        sender = sib_api_v3_sdk.CreateSender(name="Carpadi", email="admin@carpadi.com")
        to = [sib_api_v3_sdk.SendSmtpEmailTo(email=i, name=i) for i in to]
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(to=to, html_content=email_html_message, subject=subject,
                                                       sender=sender)
        try:
            # Send a transactional email
            api_response = api_instance.send_transac_email(send_smtp_email)
            print(api_response)
        except ApiException as e:
            print("Exception when calling TransactionalEmailsApi->send_transac_email: %s\n" % e)
