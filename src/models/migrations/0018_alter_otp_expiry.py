# Generated by Django 3.2.4 on 2022-05-14 22:16

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0017_auto_20220514_0827'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 5, 14, 22, 46, 13, 917436, tzinfo=utc), editable=False),
        ),
    ]
