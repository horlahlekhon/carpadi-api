# Generated by Django 3.2.4 on 2022-05-22 09:18

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0047_auto_20220522_0909'),
    ]

    operations = [
        migrations.AlterField(
            model_name='carfeature',
            name='car',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='features', to='models.carproduct'),
        ),
        migrations.AlterField(
            model_name='carproduct',
            name='car',
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, related_name='product', to='models.vehicleinfo'
            ),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 5, 22, 9, 48, 51, 481703, tzinfo=utc), editable=False),
        ),
    ]
