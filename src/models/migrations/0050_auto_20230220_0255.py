# Generated by Django 3.2.4 on 2023-02-20 02:55

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0049_auto_20230220_0254'),
    ]

    operations = [
        migrations.RenameField(
            model_name='carpurchaseoffer',
            old_name='user',
            new_name='seller',
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2023, 2, 20, 3, 24, 52, 450798, tzinfo=utc), editable=False),
        ),
    ]
