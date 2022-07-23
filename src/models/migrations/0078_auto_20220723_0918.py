# Generated by Django 3.2.4 on 2022-07-23 09:18

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0077_alter_otp_expiry'),
    ]

    operations = [
        migrations.AddField(
            model_name='carproduct',
            name='highlight',
            field=models.CharField(default='', help_text='A short description of the vehicle', max_length=100),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 7, 23, 9, 48, 9, 350616, tzinfo=utc), editable=False),
        ),
    ]