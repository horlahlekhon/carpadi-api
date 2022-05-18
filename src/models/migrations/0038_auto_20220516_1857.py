# Generated by Django 3.2.4 on 2022-05-16 18:57

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc
import django.utils.timezone
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('models', '0037_auto_20220516_0413'),
    ]

    operations = [
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 5, 16, 19, 27, 19, 107304, tzinfo=utc), editable=False),
        ),
        migrations.CreateModel(
            name='Assets',
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
                ('asset', models.URLField()),
                ('object_id', models.UUIDField()),
                (
                    'entity_type',
                    models.CharField(
                        choices=[
                            ('car', 'car picture'),
                            ('merchant', 'user profile picture'),
                            ('trade', 'Trade pictures of a car'),
                            ('car_inspection', 'Car inspection pictures'),
                            ('feature', 'Picture of a feature of a car'),
                            ('inspection_report', 'Pdf report of an inspected vehicle'),
                        ],
                        max_length=20,
                    ),
                ),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='car',
            name='pictures',
            field=models.ForeignKey(
                null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assets', to='models.assets'
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='profile_picture',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='models.assets'),
        ),
        migrations.DeleteModel(
            name='Pictures',
        ),
    ]
