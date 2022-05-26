# Generated by Django 3.2.4 on 2022-05-26 04:39

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0051_auto_20220524_0941'),
    ]

    operations = [
        migrations.AddField(
            model_name='car',
            name='name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 5, 26, 5, 9, 47, 87050, tzinfo=utc), editable=False),
        ),
    ]
