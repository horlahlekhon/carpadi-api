import mailchimp_transactional as MailchimpTransactional
from celery import task
from mailchimp_transactional.api_client import ApiClientError


# from django.core.mail import EmailMultiAlternatives


@task(name='SendEmailTask')
def send_email_task(subject, to, default_from, email_html_message):
    try:
        mailchimp = MailchimpTransactional.Client("ncTkaSqq5KLZH0Ddux7V4w")
        response = mailchimp.messages.send(
            {
                "message": dict(
                    html=email_html_message,
                    subject=subject,
                    from_email=default_from,
                    from_name="Hello from Carpadi",
                    to=[{"email": to}],
                )
            }
        )
        print(response)
    except ApiClientError as error:
        print("An exception occurred: {}".format(error.text))


@task(name='CloseTradeTask')
def close_trade(trade):
    ...
