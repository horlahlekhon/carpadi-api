# Generated by Django 3.2.4 on 2023-02-20 16:08

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0051_alter_otp_expiry'),
    ]

    operations = [
        migrations.AddField(
            model_name='otp',
            name='type',
            field=models.CharField(
                choices=[('conform_user', 'Confirmuser'), ('password_reset', 'Passwordreset')],
                default='conform_user',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='carsellers',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2023, 2, 20, 16, 38, 20, 354415, tzinfo=utc), editable=False),
        ),
    ]