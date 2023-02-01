# Generated by Django 3.2.4 on 2023-01-30 11:08

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0040_auto_20230121_1207'),
    ]

    operations = [
        migrations.AddField(
            model_name='inspections',
            name='current_stage',
            field=models.CharField(
                choices=[
                    ('generic', 'Generic'),
                    ('exterior', 'Exterior'),
                    ('glass', 'Glass'),
                    ('wheels', 'Wheels'),
                    ('under_body', 'Underbody'),
                    ('under_hood', 'Underhood'),
                    ('interior', 'Interior'),
                    ('electrical_systems', 'Electricalsystems'),
                    ('road_test', 'Roadtest'),
                    ('completed', 'Completed'),
                    ('not_started', 'Notstarted'),
                ],
                default='not_started',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='inspections',
            name='inspection_score',
            field=models.DecimalField(
                blank=True, decimal_places=2, help_text='The score of the inspection after completion', max_digits=5, null=True
            ),
        ),
        migrations.AlterField(
            model_name='assets',
            name='entity_type',
            field=models.CharField(
                choices=[
                    ('car_product', 'Pictures of a car on the sales platform'),
                    ('car', 'car picture'),
                    ('merchant', 'user profile picture'),
                    ('trade', 'Trade pictures of a car'),
                    ('car_inspection_stage', 'Picture taken for a particular stage during inspection'),
                    ('feature', 'Picture of a feature of a car'),
                    ('inspection_report', 'Pdf report of an inspected vehicle'),
                    ('spare_part', 'Images of spare parts'),
                    ('car_docs', 'Credentials and documents attached to the car'),
                    ('inspection_images', 'Inspection images that doesnt relate to any stage'),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='inspections',
            name='owners_review',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='inspectionstage',
            name='stage_name',
            field=models.CharField(
                choices=[
                    ('generic', 'Generic'),
                    ('exterior', 'Exterior'),
                    ('glass', 'Glass'),
                    ('wheels', 'Wheels'),
                    ('under_body', 'Underbody'),
                    ('under_hood', 'Underhood'),
                    ('interior', 'Interior'),
                    ('electrical_systems', 'Electricalsystems'),
                    ('road_test', 'Roadtest'),
                    ('completed', 'Completed'),
                    ('not_started', 'Notstarted'),
                ],
                max_length=40,
            ),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2023, 1, 30, 11, 38, 9, 212439, tzinfo=utc), editable=False),
        ),
    ]
