# Generated by Django 3.2.4 on 2022-09-22 05:28

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0020_auto_20220920_2112'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 9, 22, 5, 58, 1, 865308, tzinfo=utc), editable=False),
        ),
    ]
