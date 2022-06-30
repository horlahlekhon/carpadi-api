from celery import task
# from django.core.mail import EmailMultiAlternatives




@task(name='SendEmailTask')
def send_email_task(subject, to, email_html_message, default_from="admin@carpadi.com"):
    ...


@task(name='CloseTradeTask')
def close_trade(trade):
    ...

