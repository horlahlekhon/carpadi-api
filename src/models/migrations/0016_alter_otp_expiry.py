# Generated by Django 3.2.4 on 2022-05-13 05:09

import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):
    dependencies = [
        ('models', '0015_auto_20220506_0531'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 5, 13, 5, 39, 30, 746852, tzinfo=utc), editable=False),
        ),
    ]
