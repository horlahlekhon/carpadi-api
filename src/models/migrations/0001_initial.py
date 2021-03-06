# Generated by Django 3.2.4 on 2022-04-11 16:03

import datetime
import uuid
from decimal import Decimal

import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.utils.timezone
import model_utils.fields
from django.conf import settings
from django.db import migrations, models
from django.utils.timezone import utc

import src.models.models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                (
                    'is_superuser',
                    models.BooleanField(
                        default=False,
                        help_text='Designates that this user has all permissions without explicitly assigning them.',
                        verbose_name='superuser status',
                    ),
                ),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email address')),
                (
                    'is_staff',
                    models.BooleanField(
                        default=False,
                        help_text='Designates whether the user can log into this admin site.',
                        verbose_name='staff status',
                    ),
                ),
                (
                    'is_active',
                    models.BooleanField(
                        default=True,
                        help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.',
                        verbose_name='active',
                    ),
                ),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
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
                ('profile_picture', models.URLField(blank=True, null=True)),
                ('user_type', models.CharField(choices=[('admin', 'admin'), ('merchant', 'merchant')], max_length=20)),
                ('phone', models.CharField(help_text='International format phone number', max_length=15, unique=True)),
                (
                    'username',
                    models.CharField(
                        max_length=50,
                        null=True,
                        unique=True,
                        validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                    ),
                ),
                (
                    'groups',
                    models.ManyToManyField(
                        blank=True,
                        help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.',
                        related_name='user_set',
                        related_query_name='user',
                        to='auth.Group',
                        verbose_name='groups',
                    ),
                ),
                (
                    'user_permissions',
                    models.ManyToManyField(
                        blank=True,
                        help_text='Specific permissions for this user.',
                        related_name='user_set',
                        related_query_name='user',
                        to='auth.Permission',
                        verbose_name='user permissions',
                    ),
                ),
            ],
            options={
                'verbose_name': 'user',
                'verbose_name_plural': 'users',
                'abstract': False,
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Car',
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
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('failed_inspection', 'Failed Inspection'),
                            ('inspected', 'inspected'),
                            ('available', 'available'),
                            ('bought', 'bought'),
                            ('sold', 'sold'),
                        ],
                        max_length=30,
                    ),
                ),
                ('vin', models.CharField(max_length=17)),
                ('pictures', models.URLField(help_text='url of the folder where the images for the car is located.')),
                ('partitions', models.IntegerField(default=10)),
                ('colour', models.CharField(max_length=50)),
                (
                    'transmission_type',
                    models.CharField(choices=[('manual', 'Manual'), ('automatic', 'Automatic')], max_length=15),
                ),
                (
                    'cost',
                    models.DecimalField(
                        decimal_places=10, editable=False, help_text='cost of  purchasing the car', max_digits=10, max_length=10
                    ),
                ),
                (
                    'cost_of_repairs',
                    models.DecimalField(
                        decimal_places=10, editable=False, help_text='Total cost of spare parts', max_digits=10, max_length=10
                    ),
                ),
                (
                    'total_cost',
                    models.DecimalField(
                        decimal_places=10,
                        editable=False,
                        help_text='Total cost = cost + cost_of_repairs + maintainance_cost + misc',
                        max_digits=10,
                        max_length=10,
                    ),
                ),
                (
                    'maintainance_cost',
                    models.DecimalField(
                        decimal_places=10,
                        editable=False,
                        help_text='fuel, parking, mechanic workmanship costs',
                        max_digits=10,
                        max_length=10,
                    ),
                ),
                (
                    'resale_price',
                    models.DecimalField(
                        blank=True,
                        decimal_places=10,
                        help_text='price presented to merchants',
                        max_digits=10,
                        max_length=10,
                        null=True,
                    ),
                ),
                ('inspection_report', models.TextField()),
                ('buy_to_sale_time', models.IntegerField(editable=False)),
                (
                    'margin',
                    models.DecimalField(
                        decimal_places=10,
                        editable=False,
                        help_text='The profit that was made from car after sales in percentage of the total cost',
                        max_digits=10,
                        max_length=10,
                    ),
                ),
                (
                    'car_type',
                    models.CharField(
                        choices=[
                            ('suv', 'suv'),
                            ('saloon', 'saloon'),
                            ('minivan', 'minivan'),
                            ('convertible', 'convertible'),
                            ('microcar', 'microcar'),
                            ('city_car', 'City car'),
                            ('hatchback', 'Hatchback'),
                            ('sedan', 'sedan'),
                            ('family_car', 'Family car'),
                            ('muscle_car', 'Muscle car'),
                            ('roadstar', 'Roadstar'),
                            ('pickup', 'pickup'),
                            ('coupe', 'coupe'),
                        ],
                        max_length=30,
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CarBrand',
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
                ('name', models.CharField(max_length=100)),
                ('model', models.CharField(max_length=100)),
                ('year', models.IntegerField()),
            ],
            options={
                'unique_together': {('name', 'model', 'year')},
            },
        ),
        migrations.CreateModel(
            name='CarMerchant',
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
                ('bvn', models.CharField(default=None, max_length=14, null=True)),
                (
                    'user',
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE, related_name='merchant', to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Trade',
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
                ('slots_available', models.PositiveIntegerField(default=0)),
                ('slots_purchased', models.PositiveIntegerField(default=0)),
                (
                    'return_on_trade',
                    models.DecimalField(
                        decimal_places=10,
                        default=Decimal('0'),
                        max_digits=10,
                        max_length=10,
                        validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    ),
                ),
                (
                    'estimated_return_on_trade',
                    models.DecimalField(
                        decimal_places=10,
                        default=Decimal('0'),
                        max_digits=10,
                        max_length=10,
                        validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    ),
                ),
                ('remaining_slots', models.PositiveIntegerField(default=0, help_text='slots that are still available for sale')),
                (
                    'price_per_slot',
                    models.DecimalField(
                        decimal_places=10,
                        default=Decimal('0'),
                        editable=False,
                        help_text='price per slot',
                        max_digits=10,
                        max_length=10,
                        validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    ),
                ),
                (
                    'trade_status',
                    models.CharField(
                        choices=[
                            ('pending', 'Pending review'),
                            ('ongoing', 'Slots are yet to be fully bought'),
                            ('completed', 'Car has been sold and returns sorted to merchants'),
                            ('purchased', 'All slots have been bought by merchants'),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    'min_sale_price',
                    models.DecimalField(
                        decimal_places=10,
                        default=Decimal('0'),
                        help_text='min price at which the car can be sold',
                        max_digits=10,
                        max_length=10,
                        validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    ),
                ),
                (
                    'max_sale_price',
                    models.DecimalField(
                        decimal_places=10,
                        default=Decimal('0'),
                        help_text='max price at which the car can be sold',
                        max_digits=10,
                        max_length=10,
                        validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    ),
                ),
                ('bts_time', models.IntegerField(default=0, help_text='time taken to buy to sale in days')),
                ('car', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='trades', to='models.car')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Wallet',
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
                ('balance', models.DecimalField(decimal_places=10, max_digits=16)),
                ('trading_cash', models.DecimalField(decimal_places=10, max_digits=16)),
                ('withdrawable_cash', models.DecimalField(decimal_places=10, max_digits=16)),
                ('unsettled_cash', models.DecimalField(decimal_places=10, max_digits=16)),
                ('total_cash', models.DecimalField(decimal_places=10, max_digits=16)),
                (
                    'merchant',
                    models.OneToOneField(
                        help_text='merchant user wallet that holds monetary balances',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='wallet',
                        to='models.carmerchant',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TransactionPin',
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
                ('device_serial_number', models.CharField(max_length=50, unique=True)),
                ('device_platform', models.CharField(max_length=20)),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('expired', 'User already deleted device from device management'),
                            ('active', 'Transaction pin is still active'),
                            ('deleted', 'Transaction pin has been deleted'),
                        ],
                        max_length=10,
                    ),
                ),
                ('pin', models.CharField(max_length=200)),
                ('device_name', models.CharField(help_text='The name of the device i.e Iphone x', max_length=50)),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name='transaction_pins', to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Transaction',
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
                ('amount', models.DecimalField(decimal_places=4, max_digits=10)),
                ('transaction_type', models.CharField(choices=[('debit', 'Debit'), ('credit', 'Credit')], max_length=10)),
                ('transaction_reference', models.CharField(max_length=50)),
                ('transaction_description', models.CharField(blank=True, max_length=50, null=True)),
                (
                    'transaction_status',
                    models.CharField(
                        choices=[('success', 'Success'), ('failed', 'Failed'), ('pending', 'Pending')],
                        default='pending',
                        max_length=10,
                    ),
                ),
                ('transaction_response', models.JSONField(blank=True, null=True)),
                (
                    'transaction_kind',
                    models.CharField(
                        choices=[
                            ('deposit', 'Deposit'),
                            ('withdrawal', 'Withdrawal'),
                            ('transfer', 'Transfer'),
                            ('wallet_transfer', 'Wallet Transfer'),
                        ],
                        default='deposit',
                        max_length=50,
                    ),
                ),
                ('transaction_payment_link', models.URLField(blank=True, null=True)),
                (
                    'wallet',
                    models.ForeignKey(
                        help_text='transactions carried out by merchant',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='merchant_transactions',
                        to='models.wallet',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='TradeUnit',
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
                (
                    'share_percentage',
                    models.DecimalField(
                        decimal_places=10,
                        default=Decimal('0'),
                        editable=False,
                        help_text='the percentage of this unit in the trade',
                        max_digits=10,
                        max_length=10,
                    ),
                ),
                ('slots_quantity', models.PositiveIntegerField(default=1)),
                (
                    'unit_value',
                    models.DecimalField(
                        decimal_places=10,
                        default=Decimal('0'),
                        editable=False,
                        help_text='The amount to be paid given the slots quantity x trade.price_per_slot',
                        max_digits=10,
                        max_length=10,
                    ),
                ),
                (
                    'vat_percentage',
                    models.DecimalField(
                        blank=True,
                        decimal_places=10,
                        default=Decimal('0'),
                        editable=False,
                        help_text='the percentage of vat to be paid. calculated in relation to share percentage of tradeUnit in trade',
                        max_digits=10,
                        max_length=10,
                        null=True,
                    ),
                ),
                (
                    'estimated_rot',
                    models.DecimalField(
                        decimal_places=10,
                        default=Decimal('0'),
                        editable=False,
                        help_text='the estimated return on trade',
                        max_digits=10,
                        max_length=10,
                        validators=[django.core.validators.MinValueValidator(Decimal('0'))],
                    ),
                ),
                (
                    'merchant',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='units', to='models.carmerchant'),
                ),
                (
                    'trade',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='units', to='models.trade'),
                ),
                (
                    'transaction',
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name='trade_units',
                        to='models.transaction',
                    ),
                ),
            ],
            options={
                'ordering': ['-slots_quantity'],
            },
        ),
        migrations.CreateModel(
            name='SpareParts',
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
                ('name', models.CharField(max_length=100)),
                ('estimated_price', models.DecimalField(decimal_places=10, max_digits=10)),
                ('car_brand', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='models.carbrand')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Otp',
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
                ('otp', models.CharField(editable=False, max_length=6)),
                (
                    'expiry',
                    models.DateTimeField(default=datetime.datetime(2022, 4, 11, 16, 33, 8, 703584, tzinfo=utc), editable=False),
                ),
                (
                    'status',
                    models.CharField(
                        choices=[
                            ('verified', 'Otp verified by user successfully'),
                            ('failed', 'User entered wrong otp until disabled'),
                            ('expired', 'Otp was not entered before it expired'),
                            ('pending', 'Otp is yet to expire or has expired and no one sent a verification request for it'),
                        ],
                        default='pending',
                        help_text='Keep track of weather the otp was later verified or expired or failed',
                        max_length=20,
                    ),
                ),
                (
                    'user',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name='otps', to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                'get_latest_by': 'created',
            },
        ),
        migrations.CreateModel(
            name='LoginSessions',
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
                ('device_imei', models.CharField(blank=True, max_length=20, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Disbursement',
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
                ('amount', models.DecimalField(decimal_places=5, editable=False, max_digits=15)),
                (
                    'trade_unit',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name='trade_units', to='models.tradeunit'
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='CarMaintainance',
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
                (
                    'type',
                    models.CharField(
                        choices=[
                            ('spare_part', 'Car spare parts i.e brake.'),
                            ('expense', 'other expenses made on the car that doesnt directly relate to a physical parts.'),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    'car',
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='maintanances', to='models.car'),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='car',
            name='brand',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='models.carbrand'),
        ),
        migrations.AddField(
            model_name='car',
            name='car_inspector',
            field=models.OneToOneField(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to=settings.AUTH_USER_MODEL,
                validators=[src.models.models.validate_inspector],
            ),
        ),
        migrations.CreateModel(
            name='BankAccount',
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
                ('name', models.CharField(max_length=100)),
                ('bank_name', models.CharField(max_length=50)),
                ('account_number', models.CharField(max_length=10)),
                (
                    'merchant',
                    models.ForeignKey(
                        help_text='Bank account to remit merchant money to',
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='bank_accounts',
                        to='models.carmerchant',
                    ),
                ),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Activity',
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
                (
                    'activity_type',
                    models.CharField(
                        choices=[('transaction', 'transaction'), ('trade_unit', 'trade_unit'), ('disbursement', 'disbursement')],
                        max_length=15,
                    ),
                ),
                ('object_id', models.UUIDField()),
                ('description', models.TextField(default='')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
