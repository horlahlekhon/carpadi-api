# Generated by Django 3.2.4 on 2022-09-08 16:52

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0016_alter_otp_expiry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 9, 8, 17, 22, 7, 574323, tzinfo=utc), editable=False),
        ),
    ]
