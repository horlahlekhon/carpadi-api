# Generated by Django 3.2.4 on 2022-05-28 12:37

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0060_alter_otp_expiry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notifications',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 5, 28, 13, 7, 38, 461496, tzinfo=utc), editable=False),
        ),
    ]
