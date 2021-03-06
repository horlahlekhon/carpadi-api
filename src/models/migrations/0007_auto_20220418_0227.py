# Generated by Django 3.2.4 on 2022-04-18 02:27

import datetime
import uuid
from decimal import Decimal

import django.core.validators
import django.utils.timezone
import model_utils.fields
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):
    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('models', '0006_auto_20220412_2227'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarMaintenance',
            fields=[
                (
                    'created',
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name='created'
                    ),
                ),
                (
                    'modified',
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name='modified'
                    ),
                ),
                ('id', model_utils.fields.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    'type',
                    models.CharField(
                        choices=[
                            ('spare_part', 'Car spare parts i.e brake.'),
                            ('expense', 'other expenses made on the car that doesnt directly relate to a physical parts.'),
                        ],
                        max_length=20,
                    ),
                ),
                ('object_id', models.UUIDField()),
                (
                    'cost',
                    models.DecimalField(
                        decimal_places=2,
                        help_text='cost of the maintenance a the time of the maintenance.. cost on the maintenance might change, i.e spare parts. the cost here is the correct one to use when calculating total cost of car maintenance',
                        max_digits=10,
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MiscellaneousExpenses',
            fields=[
                (
                    'created',
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name='created'
                    ),
                ),
                (
                    'modified',
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name='modified'
                    ),
                ),
                ('id', model_utils.fields.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=100)),
                ('estimated_price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('description', models.TextField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='car',
            name='car_type',
            field=models.CharField(
                choices=[
                    ('suv', 'suv'),
                    ('saloon', 'saloon'),
                    ('minivan', 'minivan'),
                    ('convertible', 'convertible'),
                    ('microcar', 'microcar'),
                    ('city_car', 'City car'),
                    ('hatchback', 'Hatchback'),
                    ('sedan', 'sedan'),
                    ('family_car', 'Family car'),
                    ('muscle_car', 'Muscle car'),
                    ('roadstar', 'Roadstar'),
                    ('pickup', 'pickup'),
                    ('coupe', 'coupe'),
                ],
                default='expense',
                max_length=30,
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='car',
            name='bought_price',
            field=models.DecimalField(
                decimal_places=2,
                default=Decimal('0'),
                help_text='potential cost of  purchasing the car offered by the seller. this should be changed to reflect the actual cost of the car when it is bought',
                max_digits=10,
                max_length=10,
                validators=[django.core.validators.MinValueValidator(Decimal('0'))],
            ),
        ),
        migrations.AlterField(
            model_name='car',
            name='status',
            field=models.CharField(
                choices=[
                    ('failed_inspection', 'Failed Inspection'),
                    ('inspected', 'inspected'),
                    ('available', 'available for trading and sale'),
                    ('bought', 'bought'),
                    ('sold', 'sold'),
                    ('new', 'New car waiting to be inspected'),
                ],
                default='new',
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name='car',
            name='total_cost',
            field=models.DecimalField(
                blank=True,
                decimal_places=2,
                editable=False,
                help_text='Total cost = bought_price + cost_of_repairs + maintainance_cost + misc',
                max_digits=10,
                null=True,
            ),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 4, 18, 2, 57, 0, 652971, tzinfo=utc), editable=False),
        ),
        migrations.DeleteModel(
            name='CarMaintainance',
        ),
        migrations.AddField(
            model_name='carmaintenance',
            name='car',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintenances', to='models.car'),
        ),
        migrations.AddField(
            model_name='carmaintenance',
            name='content_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
    ]
