# Generated by Django 3.2.4 on 2022-09-07 00:52

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0014_auto_20220907_0032'),
    ]

    operations = [
        migrations.AddField(
            model_name='cardocuments',
            name='description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 9, 7, 1, 22, 15, 173505, tzinfo=utc), editable=False),
        ),
    ]
