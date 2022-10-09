# Generated by Django 3.2.4 on 2022-09-03 07:47

import datetime
from decimal import Decimal
import django.core.validators
from django.db import migrations, models
from django.utils.timezone import utc
import src.models.validators


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0004_auto_20220902_2250'),
    ]

    operations = [
        migrations.AddField(
            model_name='settings',
            name='bonus_percentage',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('50'),
                help_text='Percentage of the bonus that will go to the traders',
                max_digits=25,
            ),
        ),
        migrations.AddField(
            model_name='settings',
            name='carpadi_commision',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('50'),
                help_text='The amount of commission to deduct from rot of the trader after trade maturation',
                max_digits=25,
            ),
        ),
        migrations.AddField(
            model_name='trade',
            name='carpadi_bonus',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0'),
                help_text='Amount of bonus made by carpadi',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
            ),
        ),
        migrations.AddField(
            model_name='trade',
            name='carpadi_commission',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0'),
                help_text='The commision of carpadi on this trade',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
            ),
        ),
        migrations.AddField(
            model_name='trade',
            name='total_carpadi_rot',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0'),
                help_text='The total amount of money made by carpadi on this trade',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
            ),
        ),
        migrations.AddField(
            model_name='trade',
            name='traders_bonus_per_slot',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0'),
                help_text='The amount of allocated bonus per slot',
                max_digits=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
            ),
        ),
        migrations.AlterField(
            model_name='car',
            name='licence_plate',
            field=models.CharField(
                blank=True, max_length=20, null=True, validators=[src.models.validators.LicensePlateValidator]
            ),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 9, 3, 8, 17, 8, 495251, tzinfo=utc), editable=False),
        ),
        migrations.AlterField(
            model_name='settings',
            name='merchant_trade_rot_percentage',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('5'),
                help_text='The percentage of the car value that will be the return on trade. this is used to calculate the rot when buying slots, like `car_value * merchant_trade_rot_percentage / slot_to_buy`',
                max_digits=25,
            ),
        ),
    ]