# Generated by Django 3.2.4 on 2023-02-20 02:53

import datetime
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.utils.timezone import utc
import model_utils.fields
import src.models.validators
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0047_auto_20230219_2133'),
    ]

    operations = [
        migrations.CreateModel(
            name='CarSellers',
            fields=[
                (
                    'created',
                    model_utils.fields.AutoCreatedField(
                        default=django.utils.timezone.now, editable=False, verbose_name='created'
                    ),
                ),
                (
                    'modified',
                    model_utils.fields.AutoLastModifiedField(
                        default=django.utils.timezone.now, editable=False, verbose_name='modified'
                    ),
                ),
                ('id', model_utils.fields.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
                ('phone', models.CharField(max_length=20, validators=[src.models.validators.PhoneNumberValidator])),
            ],
            options={
                'ordering': ('-created',),
                'get_latest_by': 'created',
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2023, 2, 20, 3, 23, 4, 650957, tzinfo=utc), editable=False),
        ),
        migrations.AlterField(
            model_name='carpurchaseoffer',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='models.carsellers'),
        ),
    ]
