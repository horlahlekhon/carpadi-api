# Generated by Django 3.2.4 on 2023-02-19 21:30

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0045_auto_20230219_2130'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2023, 2, 19, 22, 0, 37, 55939, tzinfo=utc), editable=False),
        ),
    ]
