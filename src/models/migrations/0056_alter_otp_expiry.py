# Generated by Django 3.2.4 on 2023-03-22 21:19

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0055_alter_otp_expiry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2023, 3, 22, 21, 49, 34, 831892, tzinfo=utc), editable=False),
        ),
    ]