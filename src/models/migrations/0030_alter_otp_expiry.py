# Generated by Django 3.2.4 on 2022-05-15 19:29

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0029_alter_otp_expiry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 5, 15, 19, 59, 18, 125772, tzinfo=utc), editable=False),
        ),
    ]
