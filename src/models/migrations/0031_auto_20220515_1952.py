# Generated by Django 3.2.4 on 2022-05-15 19:52

import datetime
from decimal import Decimal

import django.core.validators
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):
    dependencies = [
        ('models', '0030_alter_otp_expiry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 5, 15, 20, 22, 2, 765816, tzinfo=utc), editable=False),
        ),
        migrations.AlterField(
            model_name='trade',
            name='min_sale_price',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0'),
                help_text='min price at which the car can be sold, given the expenses we already made. this should be determined by who is creating the sales by checking the expenses made on the car',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
            ),
        ),
    ]
