# Generated by Django 3.2.4 on 2022-05-03 07:03

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc
import src.carpadi_admin.utils


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0012_auto_20220429_0152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='disbursement',
            name='trade_unit',
            field=models.OneToOneField(help_text='the trade unit that this disbursement is for', on_delete=django.db.models.deletion.CASCADE, related_name='disbursement', to='models.tradeunit', validators=[src.carpadi_admin.utils.disbursement_trade_unit_validator]),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 5, 3, 7, 32, 36, 431745, tzinfo=utc), editable=False),
        ),
        migrations.AlterField(
            model_name='tradeunit',
            name='buy_transaction',
            field=models.ForeignKey(help_text='the transaction that bought this unit', on_delete=django.db.models.deletion.PROTECT, related_name='trade_units_buy', to='models.transaction'),
        ),
    ]
