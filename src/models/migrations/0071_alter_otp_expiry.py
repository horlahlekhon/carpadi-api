# Generated by Django 3.2.4 on 2022-06-17 07:14

import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):
    dependencies = [
        ('models', '0070_auto_20220617_0713'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 6, 17, 7, 43, 59, 169064, tzinfo=utc), editable=False),
        ),
    ]
