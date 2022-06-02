# Generated by Django 3.2.4 on 2022-04-12 17:14

import datetime
from decimal import Decimal

import django.core.validators
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):
    dependencies = [
        ('models', '0003_alter_otp_expiry'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='car',
            name='partitions',
        ),
        migrations.RemoveField(
            model_name='trade',
            name='remaining_slots',
        ),
        migrations.AddField(
            model_name='trade',
            name='date_of_sale',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='car',
            name='cost',
            field=models.DecimalField(decimal_places=2, editable=False, help_text='cost of  purchasing the car',
                                      max_digits=10, max_length=10),
        ),
        migrations.AlterField(
            model_name='car',
            name='cost_of_repairs',
            field=models.DecimalField(decimal_places=2, editable=False, help_text='Total cost of spare parts',
                                      max_digits=10),
        ),
        migrations.AlterField(
            model_name='car',
            name='maintainance_cost',
            field=models.DecimalField(decimal_places=2, editable=False,
                                      help_text='fuel, parking, mechanic workmanship costs', max_digits=10),
        ),
        migrations.AlterField(
            model_name='car',
            name='margin',
            field=models.DecimalField(decimal_places=2, editable=False,
                                      help_text='The profit that was made from car after sales in percentage of the total cost',
                                      max_digits=10),
        ),
        migrations.AlterField(
            model_name='car',
            name='resale_price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text='price presented to merchants',
                                      max_digits=10, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='car',
            name='total_cost',
            field=models.DecimalField(decimal_places=2, editable=False,
                                      help_text='Total cost = cost + cost_of_repairs + maintainance_cost + misc',
                                      max_digits=10),
        ),
        migrations.AlterField(
            model_name='disbursement',
            name='amount',
            field=models.DecimalField(decimal_places=5, editable=False, max_digits=10),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 4, 12, 17, 44, 45, 860676, tzinfo=utc),
                                       editable=False),
        ),
        migrations.AlterField(
            model_name='spareparts',
            name='estimated_price',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AlterField(
            model_name='trade',
            name='estimated_return_on_trade',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'),
                                      help_text='The estimated profit that can be made from car sale', max_digits=10,
                                      validators=[django.core.validators.MinValueValidator(Decimal('0'))]),
        ),
        migrations.AlterField(
            model_name='trade',
            name='max_sale_price',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'),
                                      help_text='max price at which the car can be sold', max_digits=10,
                                      validators=[django.core.validators.MinValueValidator(Decimal('0'))]),
        ),
        migrations.AlterField(
            model_name='trade',
            name='min_sale_price',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'),
                                      help_text='min price at which the car can be sold', max_digits=10,
                                      validators=[django.core.validators.MinValueValidator(Decimal('0'))]),
        ),
        migrations.AlterField(
            model_name='trade',
            name='price_per_slot',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), editable=False,
                                      help_text='price per slot', max_digits=10,
                                      validators=[django.core.validators.MinValueValidator(Decimal('0'))]),
        ),
        migrations.AlterField(
            model_name='trade',
            name='return_on_trade',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'),
                                      help_text='The actual profit that was made from car ', max_digits=10,
                                      validators=[django.core.validators.MinValueValidator(Decimal('0'))]),
        ),
        migrations.AlterField(
            model_name='trade',
            name='trade_status',
            field=models.CharField(
                choices=[('pending', 'Pending review'), ('ongoing', 'Slots are yet to be fully bought'),
                         ('completed', 'Car has been sold and returns sorted to merchants'),
                         ('purchased', 'All slots have been bought by merchants')], default='ongoing', max_length=20),
        ),
        migrations.AlterField(
            model_name='tradeunit',
            name='estimated_rot',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), editable=False,
                                      help_text='the estimated return on trade', max_digits=10,
                                      validators=[django.core.validators.MinValueValidator(Decimal('0'))]),
        ),
        migrations.AlterField(
            model_name='tradeunit',
            name='share_percentage',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), editable=False,
                                      help_text='the percentage of this unit in the trade', max_digits=10),
        ),
        migrations.AlterField(
            model_name='tradeunit',
            name='unit_value',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'), editable=False,
                                      help_text='The amount to be paid given the slots quantity x trade.price_per_slot',
                                      max_digits=10),
        ),
        migrations.AlterField(
            model_name='tradeunit',
            name='vat_percentage',
            field=models.DecimalField(blank=True, decimal_places=2, default=Decimal('0'), editable=False,
                                      help_text='the percentage of vat to be paid. calculated in relation to share percentage of tradeUnit in trade',
                                      max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='wallet',
            name='balance',
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name='wallet',
            name='total_cash',
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name='wallet',
            name='trading_cash',
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name='wallet',
            name='unsettled_cash',
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
        migrations.AlterField(
            model_name='wallet',
            name='withdrawable_cash',
            field=models.DecimalField(decimal_places=2, max_digits=16),
        ),
    ]
