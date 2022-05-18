# Generated by Django 3.2.4 on 2022-04-21 00:20

import datetime

import django.db.models.deletion
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):
    dependencies = [
        ('models', '0008_auto_20220420_0518'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='car',
            name='maintainance_cost',
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 4, 21, 0, 50, 45, 15456, tzinfo=utc), editable=False),
        ),
        migrations.AlterField(
            model_name='trade',
            name='car',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='trades', to='models.car'),
        ),
    ]
