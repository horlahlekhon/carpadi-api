# Generated by Django 3.2.4 on 2022-08-10 14:47

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0006_alter_otp_expiry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 8, 10, 15, 17, 46, 252497, tzinfo=utc), editable=False),
        ),
    ]