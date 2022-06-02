# Generated by Django 3.2.4 on 2022-04-12 22:22

import datetime
from decimal import Decimal

from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):
    dependencies = [
        ('models', '0004_auto_20220412_1714'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='car',
            name='buy_to_sale_time',
        ),
        migrations.RemoveField(
            model_name='car',
            name='cost',
        ),
        migrations.AddField(
            model_name='car',
            name='offering_price',
            field=models.DecimalField(decimal_places=2, default=Decimal('0'),
                                      help_text='potential cost of  purchasing the car offered by the seller',
                                      max_digits=10, max_length=10),
        ),
        migrations.AlterField(
            model_name='car',
            name='car_type',
            field=models.CharField(blank=True, choices=[('suv', 'suv'), ('saloon', 'saloon'), ('minivan', 'minivan'),
                                                        ('convertible', 'convertible'), ('microcar', 'microcar'),
                                                        ('city_car', 'City car'), ('hatchback', 'Hatchback'),
                                                        ('sedan', 'sedan'), ('family_car', 'Family car'),
                                                        ('muscle_car', 'Muscle car'), ('roadstar', 'Roadstar'),
                                                        ('pickup', 'pickup'), ('coupe', 'coupe')], max_length=30,
                                   null=True),
        ),
        migrations.AlterField(
            model_name='car',
            name='cost_of_repairs',
            field=models.DecimalField(blank=True, decimal_places=2, editable=False,
                                      help_text='Total cost of spare parts', max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='car',
            name='inspection_report',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='car',
            name='maintainance_cost',
            field=models.DecimalField(blank=True, decimal_places=2, editable=False,
                                      help_text='fuel, parking, mechanic workmanship costs', max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='car',
            name='pictures',
            field=models.URLField(blank=True, help_text='url of the folder where the images for the car is located.',
                                  null=True),
        ),
        migrations.AlterField(
            model_name='car',
            name='total_cost',
            field=models.DecimalField(blank=True, decimal_places=2, editable=False,
                                      help_text='Total cost = cost + cost_of_repairs + maintainance_cost + misc',
                                      max_digits=10, null=True),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 4, 12, 22, 52, 55, 188470, tzinfo=utc),
                                       editable=False),
        ),
    ]
