# Generated by Django 3.2.4 on 2022-03-19 15:44

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.utils.timezone import utc
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0008_auto_20220318_1152'),
    ]

    operations = [
        migrations.CreateModel(
            name='Wallets',
            fields=[
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('id', model_utils.fields.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('merchant', models.UUIDField(default=uuid.uuid4, editable=False)),
                ('balance', models.DecimalField(decimal_places=10, max_digits=16)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='carmerchant',
            name='bvn',
            field=models.CharField(max_length=14, null=True),
        ),
        migrations.AlterField(
            model_name='carmerchant',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='merchant', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 3, 19, 16, 4, 4, 896017, tzinfo=utc), editable=False),
        ),
        migrations.AlterField(
            model_name='user',
            name='user_type',
            field=models.CharField(choices=[('admin', 'admin'), ('merchant', 'merchant')], max_length=20),
        ),
    ]
