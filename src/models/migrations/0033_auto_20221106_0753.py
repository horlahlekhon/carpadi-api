# Generated by Django 3.2.4 on 2022-11-06 07:53

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0032_auto_20221106_0750'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carmerchant',
            name='status',
            field=models.CharField(
                choices=[
                    ('disapproved', 'User approval was declined'),
                    ('pending', ' User is pending approval'),
                    ('approved', 'User has been approved'),
                ],
                default='pending',
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 11, 6, 8, 23, 27, 338649, tzinfo=utc), editable=False),
        ),
    ]
