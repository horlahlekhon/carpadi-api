# Generated by Django 3.2.4 on 2022-05-16 03:50

import datetime
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
from django.utils.timezone import utc
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('models', '0033_alter_otp_expiry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='car',
            name='status',
            field=models.CharField(
                choices=[
                    ('failed_inspection', 'Failed Inspection'),
                    ('inspected', 'inspected'),
                    ('available', 'available for trading and sale'),
                    ('ongoing_trade', 'Car is an ongoing trade'),
                    ('bought', 'bought'),
                    ('sold', 'sold'),
                    ('new', 'New car waiting to be inspected'),
                    ('archived', 'Archived'),
                ],
                default='new',
                max_length=30,
            ),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 5, 16, 4, 20, 37, 867535, tzinfo=utc), editable=False),
        ),
        migrations.CreateModel(
            name='Pictures',
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
                ('asset', models.ImageField(blank=True, null=True, upload_to='pictures')),
                ('object_id', models.UUIDField()),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AlterField(
            model_name='car',
            name='pictures',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='models.pictures'),
        ),
        migrations.AlterField(
            model_name='user',
            name='profile_picture',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='models.pictures'),
        ),
    ]