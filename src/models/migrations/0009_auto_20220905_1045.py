# Generated by Django 3.2.4 on 2022-09-05 10:45

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0008_alter_otp_expiry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 9, 5, 11, 15, 33, 95690, tzinfo=utc), editable=False),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='amount',
            field=models.DecimalField(decimal_places=5, max_digits=20),
        ),
    ]
