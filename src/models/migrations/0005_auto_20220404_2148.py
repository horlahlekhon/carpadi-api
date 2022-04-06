# Generated by Django 3.2.4 on 2022-04-04 21:48

import datetime
from decimal import Decimal
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0004_auto_20220331_2258'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='tradeunit',
            options={'ordering': ['-slots_quantity']},
        ),
        migrations.RemoveField(
            model_name='trade',
            name='expected_return_on_trade',
        ),
        migrations.RemoveField(
            model_name='trade',
            name='total_slots',
        ),
        migrations.RemoveField(
            model_name='trade',
            name='traded_slots',
        ),
        migrations.AddField(
            model_name='trade',
            name='estimated_return_on_trade',
            field=models.DecimalField(decimal_places=10, default=Decimal('0'), max_digits=10, max_length=10),
        ),
        migrations.AddField(
            model_name='trade',
            name='max_sale_price',
            field=models.DecimalField(decimal_places=10, default=Decimal('0'), help_text='max price at which the car can be sold', max_digits=10, max_length=10),
        ),
        migrations.AddField(
            model_name='trade',
            name='min_sale_price',
            field=models.DecimalField(decimal_places=10, default=Decimal('0'), help_text='min price at which the car can be sold', max_digits=10, max_length=10),
        ),
        migrations.AddField(
            model_name='tradeunit',
            name='estimated_rot',
            field=models.DecimalField(decimal_places=10, default=Decimal('0'), editable=False, help_text='the estimated return on trade', max_digits=10, max_length=10),
        ),
        migrations.AddField(
            model_name='tradeunit',
            name='slots_quantity',
            field=models.IntegerField(default=1),
        ),
        migrations.AddField(
            model_name='tradeunit',
            name='transaction',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='trade_units', to='models.transaction'),
        ),
        migrations.AddField(
            model_name='tradeunit',
            name='unit_value',
            field=models.DecimalField(decimal_places=10, default=Decimal('0'), editable=False, help_text='The amount to be paid given the slots quantity x trade.price_per_slot', max_digits=10, max_length=10),
        ),
        migrations.AddField(
            model_name='tradeunit',
            name='vat_percentage',
            field=models.DecimalField(blank=True, decimal_places=10, default=Decimal('0'), editable=False, help_text='the percentage of vat to be paid. calculated in relation to share percentage of tradeUnit in trade', max_digits=10, max_length=10, null=True),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 4, 4, 22, 18, 6, 427880, tzinfo=utc), editable=False),
        ),
        migrations.AlterField(
            model_name='trade',
            name='price_per_slot',
            field=models.DecimalField(decimal_places=10, default=Decimal('0'), editable=False, help_text='price per slot', max_digits=10, max_length=10),
        ),
        migrations.AlterField(
            model_name='trade',
            name='remaining_slots',
            field=models.IntegerField(default=0, help_text='slots that are still available for sale'),
        ),
        migrations.AlterField(
            model_name='trade',
            name='return_on_trade',
            field=models.DecimalField(decimal_places=10, default=Decimal('0'), max_digits=10, max_length=10),
        ),
        migrations.AlterField(
            model_name='tradeunit',
            name='share_percentage',
            field=models.DecimalField(decimal_places=10, default=Decimal('0'), editable=False, help_text='the percentage of this unit in the trade', max_digits=10, max_length=10),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_kind',
            field=models.CharField(choices=[('deposit', 'Deposit'), ('withdrawal', 'Withdrawal'), ('transfer', 'Transfer'), ('wallet_transfer', 'Wallet Transfer')], default='deposit', max_length=50),
        ),
    ]
