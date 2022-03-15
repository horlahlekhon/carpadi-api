from decimal import Decimal

from celery import uuid
from django.test import TestCase
from nose.tools import eq_, ok_
from pytz import timezone

from src.models.serializers import TransactionsSerializer

# Create your tests here.


class TransactionsSerializerTest(TestCase):
    def setUp(self):
        self.transactions_good_data = {
            'id': uuid.uuid4(),
            'wallet': uuid.uuid4(),
            'amount': Decimal(5600.0000),
            'created': timezone.now(),
        }

        self.transactions_invalid_id = {
            'id': "invalid id",
            'wallet': uuid.uuid4(),
            'amount': Decimal(5600.0000),
            'created': timezone.now(),
        }

        self.transactions_invalid_wallet_id = {
            'id': uuid.uuid4(),
            'wallet': "invalid wallet",
            'amount': Decimal(5600.0000),
            'created': timezone.now(),
        }

        self.transactions_invalid_amount = {
            'id': uuid.uuid4(),
            'wallet': uuid.uuid4(),
            'amount': Decimal(5600.0000),
            'created': timezone.now(),
        }

    def test_serializer_with_empty_data(self):
        serializer = TransactionsSerializer(data={})
        eq_(serializer.is_valid(), False)

    def test_serializer_with_invalid_id(self):
        serializer = TransactionsSerializer(data=self.transactions_invalid_id)
        eq_(serializer.is_valid(), False)

    def test_serializer_with_invalid_wallet_id(self):
        serializer = TransactionsSerializer(data=self.transactions_invalid_wallet_id)
        eq_(serializer.is_valid(), False)

    def test_serializer_with_invalid_amount(self):
        serializer = TransactionsSerializer(data=self.transactions_invalid_amount)
        eq_(serializer.is_valid(), False)

    def test_serializer_with_valid_data(self):
        serializer = TransactionsSerializer(data=self.transactions_good_data)
        ok_(serializer.is_valid())
