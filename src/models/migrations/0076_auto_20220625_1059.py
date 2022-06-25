# Generated by Django 3.2.4 on 2022-06-25 10:59

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0075_alter_otp_expiry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assets',
            name='entity_type',
            field=models.CharField(
                choices=[
                    ('car_product', 'Pictures of a car on the sales platform'),
                    ('car', 'car picture'),
                    ('merchant', 'user profile picture'),
                    ('trade', 'Trade pictures of a car'),
                    ('car_inspection', 'Car inspection pictures'),
                    ('feature', 'Picture of a feature of a car'),
                    ('inspection_report', 'Pdf report of an inspected vehicle'),
                    ('profile_picture', 'Profile picture of a user'),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 6, 25, 11, 29, 15, 212572, tzinfo=utc), editable=False),
        ),
        migrations.AlterField(
            model_name='transactionpin',
            name='device_serial_number',
            field=models.CharField(max_length=50),
        ),
        migrations.AlterUniqueTogether(
            name='transactionpin',
            unique_together={('device_serial_number', 'pin', 'user')},
        ),
    ]
