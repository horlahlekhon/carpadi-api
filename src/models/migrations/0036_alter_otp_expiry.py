# Generated by Django 3.2.4 on 2022-11-11 11:05

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0035_alter_otp_expiry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 11, 11, 11, 35, 23, 671728, tzinfo=utc), editable=False),
        ),
    ]