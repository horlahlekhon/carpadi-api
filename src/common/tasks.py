from celery import task
# from django.core.mail import EmailMultiAlternatives

import mailchimp_transactional as MailchimpTransactional
from mailchimp_transactional.api_client import ApiClientError


@task(name='SendEmailTask')
def send_email_task(subject, to, default_from="admin@carpadi.com", email_html_message):
    try:
        mailchimp = MailchimpTransactional.Client("ncTkaSqq5KLZH0Ddux7V4w")
        response = client.messages.send({"message": {html = email_html_message,
                                                     subject = subject,
                                                     from_email = default_from,
                                                     from_name = "Hello from Carpadi",
                                                     to = [{
                                                        email = to
                                                     }]}})
        print(response)
    except ApiClientError as error:
        print("An exception occurred: {}".format(error.text))


@task(name='CloseTradeTask')
def close_trade(trade):
    ...


