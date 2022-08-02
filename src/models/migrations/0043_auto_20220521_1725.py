# Generated by Django 3.2.4 on 2022-05-21 17:25

import datetime

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):
    dependencies = [
        ('models', '0042_auto_20220521_1720'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='car',
            name='age',
        ),
        migrations.RemoveField(
            model_name='car',
            name='car_type',
        ),
        migrations.RemoveField(
            model_name='car',
            name='fuel_type',
        ),
        migrations.RemoveField(
            model_name='car',
            name='mileage',
        ),
        migrations.RemoveField(
            model_name='car',
            name='transmission_type',
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 5, 21, 17, 55, 22, 876642, tzinfo=utc), editable=False),
        ),
    ]
