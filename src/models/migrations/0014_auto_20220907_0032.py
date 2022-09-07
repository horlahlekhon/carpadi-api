# Generated by Django 3.2.4 on 2022-09-07 00:32

import datetime
from django.db import migrations, models
import django.db.models.deletion
from django.utils.timezone import utc
import django.utils.timezone
import model_utils.fields
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0013_alter_otp_expiry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assets',
            name='entity_type',
            field=models.CharField(
                choices=[
                    ('car_product', 'Pictures of a car on the sales platform'),
                    ('car', 'car picture'),
                    ('merchant', 'user profile picture'),
                    ('trade', 'Trade pictures of a car'),
                    ('car_inspection', 'Car inspection pictures'),
                    ('feature', 'Picture of a feature of a car'),
                    ('inspection_report', 'Pdf report of an inspected vehicle'),
                    ('spare_part', 'Images of spare parts'),
                    ('car_docs', 'Credentials and documents attached to the car'),
                ],
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='disbursement',
            name='disbursement_status',
            field=models.CharField(
                choices=[
                    ('rolled_back', 'A disbursement that was rolledback'),
                    ('Ongoing', 'Ongoing'),
                    ('Completed', 'Completed'),
                    ('Unsettled', 'Unsettled. The disbursement has been created but not yet settled by the admin'),
                    ('Settled', 'Settled. The disbursement has been settled by the admin'),
                ],
                default='Unsettled',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='otp',
            name='expiry',
            field=models.DateTimeField(default=datetime.datetime(2022, 9, 7, 1, 2, 8, 245382, tzinfo=utc), editable=False),
        ),
        migrations.AlterField(
            model_name='trade',
            name='trade_status',
            field=models.CharField(
                choices=[
                    ('pending', 'Pending review'),
                    ('ongoing', 'Slots are yet to be fully bought'),
                    ('completed', 'Car has been sold and returns sorted to merchants'),
                    ('purchased', 'All slots have been bought by merchants'),
                    ('closed', 'All slots have been bought by merchants, car has been sold and disbursements made'),
                    (
                        'expired',
                        'An expired trade has passed the specified trading duration and all money will be returned to the users',
                    ),
                ],
                default='ongoing',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='transaction_status',
            field=models.CharField(
                choices=[
                    (
                        'unsettled',
                        'Transaction that are yet to be resolved due to a dispute or disbursement delay, typically pending credit',
                    ),
                    ('success', 'Success'),
                    ('failed', 'Failed'),
                    ('cancelled', 'Payment cancelled by user'),
                    ('pending', 'Pending'),
                    ('rollback', ' Rolled back disbursement transaction'),
                ],
                default='pending',
                max_length=10,
            ),
        ),
        migrations.CreateModel(
            name='CarDocuments',
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
                ('is_verified', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=50)),
                (
                    'asset',
                    models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='models.assets'),
                ),
                ('car', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='models.car')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
