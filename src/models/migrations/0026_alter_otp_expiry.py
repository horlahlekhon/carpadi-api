# Generated by Django 3.2.4 on 2022-05-15 07:12

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0025_alter_otp_expiry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 5, 15, 7, 42, 36, 623908, tzinfo=utc), editable=False),
        ),
    ]