# Generated by Django 3.2.4 on 2022-06-17 07:15

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0072_alter_otp_expiry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 6, 17, 7, 45, 24, 733085, tzinfo=utc), editable=False),
        ),
    ]
