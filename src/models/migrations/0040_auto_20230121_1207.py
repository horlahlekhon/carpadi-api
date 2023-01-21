# Generated by Django 3.2.4 on 2023-01-21 12:07

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0039_auto_20230107_0942'),
    ]

    operations = [
        migrations.AddField(
            model_name='carpurchaseoffer',
            name='decline_reason',
            field=models.TextField(default=''),
        ),
        migrations.AddField(
            model_name='carpurchaseoffer',
            name='status',
            field=models.CharField(choices=[('accepted', 'Car purchase offer was accepted'), ('declined', 'Purchase offer declined based on some reason'), ('pending', 'Yet to be processed')], default='pending', max_length=40),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2023, 1, 21, 12, 37, 37, 327801, tzinfo=utc), editable=False),
        ),
        migrations.AlterField(
            model_name='vehicleinfo',
            name='car_type',
            field=models.CharField(blank=True, choices=[('suv', 'SUV'), ('saloon', 'Saloon'), ('minivan', 'Minivan'), ('convertible', 'Convertible'), ('hatchback', 'Hatchback'), ('pickup', 'Pickup'), ('coupe', 'Coupe')], max_length=30, null=True),
        ),
    ]
