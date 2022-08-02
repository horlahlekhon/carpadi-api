# Generated by Django 3.2.4 on 2022-05-21 17:20

import datetime
import uuid

import django.utils.timezone
import model_utils.fields
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):
    dependencies = [
        ('models', '0041_alter_otp_expiry'),
    ]

    operations = [
        migrations.CreateModel(
            name='VehicleInfo',
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
                ('vin', models.CharField(max_length=17, unique=True)),
                ('engine', models.TextField()),
                (
                    'transmission_type',
                    models.CharField(choices=[('manual', 'Manual'), ('automatic', 'Automatic')], max_length=15),
                ),
                (
                    'car_type',
                    models.CharField(
                        blank=True,
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
                        max_length=30,
                        null=True,
                    ),
                ),
                (
                    'fuel_type',
                    models.CharField(
                        choices=[
                            ('petrol', 'Petrol'),
                            ('diesel', 'Diesel'),
                            ('cng', 'CNG'),
                            ('lpg', 'LPG'),
                            ('electric', 'Electric'),
                            ('hybrid', 'Hybrid'),
                        ],
                        max_length=30,
                    ),
                ),
                ('mileage', models.IntegerField(blank=True, null=True)),
                ('age', models.IntegerField(blank=True, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('trim', models.CharField(max_length=50, null=True)),
                ('year', models.PositiveIntegerField()),
                ('model', models.CharField(max_length=100)),
                ('manufacturer', models.CharField(max_length=50)),
                ('make', models.CharField(max_length=50)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='car',
            name='brand',
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 5, 21, 17, 50, 42, 701924, tzinfo=utc), editable=False),
        ),
        migrations.AddField(
            model_name='car',
            name='information',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='models.vehicleinfo'),
        ),
    ]
