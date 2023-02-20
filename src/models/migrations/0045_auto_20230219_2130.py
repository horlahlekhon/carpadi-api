# Generated by Django 3.2.4 on 2023-02-19 21:30

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0044_auto_20230208_1432'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='activity',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='assets',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='bankaccount',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='car',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='cardocuments',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='carfeature',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='carmaintenance',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='carmerchant',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='carproduct',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='carpurchaseoffer',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='disbursement',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='inspections',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='inspectionstage',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='loginsessions',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='miscellaneousexpenses',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='notifications',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='settings',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='spareparts',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='trade',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='transaction',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='vehicleinfo',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.AlterModelOptions(
            name='wallet',
            options={'get_latest_by': 'created', 'ordering': ('-created',)},
        ),
        migrations.RemoveField(
            model_name='carpurchaseoffer',
            name='car_condition',
        ),
        migrations.RemoveField(
            model_name='carpurchaseoffer',
            name='contact_preference',
        ),
        migrations.RemoveField(
            model_name='carpurchaseoffer',
            name='count_of_previous_users',
        ),
        migrations.RemoveField(
            model_name='carpurchaseoffer',
            name='custom_papers_availability',
        ),
        migrations.RemoveField(
            model_name='carpurchaseoffer',
            name='is_negotiable',
        ),
        migrations.RemoveField(
            model_name='carpurchaseoffer',
            name='note',
        ),
        migrations.RemoveField(
            model_name='carpurchaseoffer',
            name='price',
        ),
        migrations.AlterField(
            model_name='inspections',
            name='current_stage',
            field=models.CharField(
                choices=[
                    ('generic', 'Generic'),
                    ('exterior', 'Exterior'),
                    ('glass', 'Glass'),
                    ('wheels', 'Tyresandwheels'),
                    ('under_body', 'Underbody'),
                    ('under_hood', 'Underhood'),
                    ('interior', 'Interior'),
                    ('electrical_systems', 'Electricalsystems'),
                    ('road_test', 'Roadtest'),
                    ('completed', 'Completed'),
                    ('not_started', 'Notstarted'),
                ],
                default='not_started',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='inspectionstage',
            name='stage_name',
            field=models.CharField(
                choices=[
                    ('generic', 'Generic'),
                    ('exterior', 'Exterior'),
                    ('glass', 'Glass'),
                    ('wheels', 'Tyresandwheels'),
                    ('under_body', 'Underbody'),
                    ('under_hood', 'Underhood'),
                    ('interior', 'Interior'),
                    ('electrical_systems', 'Electricalsystems'),
                    ('road_test', 'Roadtest'),
                    ('completed', 'Completed'),
                    ('not_started', 'Notstarted'),
                ],
                max_length=40,
            ),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2023, 2, 19, 22, 0, 7, 588331, tzinfo=utc), editable=False),
        ),
    ]
