import requests
from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import status

from src.carpadi_api.filters import ActivityFilter, TransactionsFilter, CarsFilter, TradeFilter
from src.carpadi_api.serializers import (
    CarSerializer,
    TransactionPinSerializers,
    UpdateTransactionPinSerializers,
    CarMerchantUpdateSerializer,
    WalletSerializer,
    TransactionSerializer,
    TradeSerializer,
    TradeUnitSerializer,
    BankAccountSerializer,
    BankSerializer,
)
from src.config import common
from src.models.models import (
    Transaction,
    CarMerchant,
    BankAccount,
    CarBrand,
    Car,
    TransactionPin,
    TransactionPinStatus,
    Wallet,
    Trade,
    TradeUnit,
    Activity,
    Banks,
)
from src.models.permissions import IsCarMerchantAndAuthed
from src.models.serializers import (
    CarMerchantSerializer,
    CarBrandSerializer,
    ActivitySerializer,
)


class DefaultApiModelViewset(viewsets.ModelViewSet):
    permissions = {'default': (IsCarMerchantAndAuthed,)}

    def get_permissions(self):
        self.permission_classes = self.permissions.get(self.action, self.permissions['default'])
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DefaultGenericViewset(viewsets.GenericViewSet):
    permissions = {'default': (IsCarMerchantAndAuthed,)}

    def get_permissions(self):
        self.permission_classes = self.permissions.get(self.action, self.permissions['default'])
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CarMerchantViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
                         viewsets.GenericViewSet):
    queryset = CarMerchant.objects.all()
    serializers = {"default": CarMerchantSerializer, "partial_update": CarMerchantUpdateSerializer}
    permission_classes = (IsCarMerchantAndAuthed,)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers['default'])

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg], "user": self.request.user}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_serializer_context(self):
        ctx = super(CarMerchantViewSet, self).get_serializer_context()
        if self.action not in ("create", "list"):
            ctx["merchant"] = self.get_object()
        return ctx

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance: CarMerchant = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance.refresh_from_db()
        ser = CarMerchantSerializer(instance=instance)
        return Response(ser.data)


class TransactionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                         viewsets.GenericViewSet):
    """
    handles basic CRUD functionalities for transaction model
    """

    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TransactionsFilter
    # permission_classes = (IsCarMerchantAndAuthed,)

    permissions = {'default': (IsCarMerchantAndAuthed,), "verify_transaction": ()}

    def get_permissions(self):
        self.permission_classes = self.permissions.get(self.action, self.permissions['default'])
        return super().get_permissions()

    def list(self, request):
        serialize = self.serializer_class(self.queryset, many=True)
        return Response(serialize.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        transaction = get_object_or_404(self.queryset, pk=pk)
        serialize = self.serializer_class(transaction)
        return Response(serialize.data, status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        user: User = self.request.user
        serializer.save(merchant=user.merchant)

    @transaction.atomic()
    @action(detail=False, methods=['get', 'post'], url_path='verify-transaction', url_name='verify_transaction')
    def verify_transaction(self, request):
        """
        verify transaction
        """
        if request.method == 'POST' and request.data.get("event.type") == "Transfer":
            data = request.data
            tx_ref = data.get("transfer").get("reference")
            transaction_id = data.get("transfer").get("id")
            tx = get_object_or_404(self.queryset, transaction_reference=tx_ref)
            headers = dict(Authorization=f"Bearer {common.FLW_SECRET_KEY}")
            response = requests.get(url=common.FLW_GET_TRANSFER_URL(transaction_id), headers=headers)
            res, code = Transaction.verify_deposit(response, tx)
            return Response(res, status=code)
        elif request.method == 'GET':
            tx_ref = request.query_params.get('tx_ref')
            transaction_id = request.query_params.get('transaction_id')
            tx = get_object_or_404(self.queryset, transaction_reference=tx_ref)
            headers = dict(Authorization=f"Bearer {common.FLW_SECRET_KEY}")
            response = requests.get(url=common.FLW_PAYMENT_VERIFY_URL(transaction_id), headers=headers)
            res, code = Transaction.verify_deposit(response, tx)
            return Response(res, code)
        else:
            return Response({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)


class BankAccountViewSet(viewsets.ModelViewSet):
    serializer_class = BankAccountSerializer
    queryset = BankAccount.objects.all()
    permissions = {'default': (IsCarMerchantAndAuthed,)}

    def get_permissions(self):
        self.permission_classes = self.permissions.get(self.action, self.permissions['default'])
        return super().get_permissions()

    def get_queryset(self):
        return self.queryset.filter(merchant=self.request.user.merchant)

    @action(detail=False, methods=['get'], url_path='get-banks', url_name='get_banks')
    def get_banks(self, request):
        serialize = BankSerializer(instance=Banks.objects.all(), many=True)
        return Response(serialize.data, status=status.HTTP_200_OK)


class CarBrandSerializerViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = CarBrandSerializer
    queryset = CarBrand.objects.all()
    permission_classes = (IsCarMerchantAndAuthed,)


class CarViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = CarSerializer
    queryset = Car.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = CarsFilter
    permission_classes = (IsCarMerchantAndAuthed,)


class TransactionPinsViewSet(viewsets.ModelViewSet):
    queryset = TransactionPin.objects.filter(status=TransactionPinStatus.Active)
    # serializer_class = TransactionPinSerializers
    permissions = {'default': (IsCarMerchantAndAuthed,)}
    serializers = {'default': TransactionPinSerializers, 'partial_update': UpdateTransactionPinSerializers}

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers['default'])

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
        filter_kwargs = {self.lookup_field: self.kwargs[lookup_url_kwarg], "user": self.request.user}
        obj = get_object_or_404(queryset, **filter_kwargs)
        self.check_object_permissions(self.request, obj)
        return obj

    def get_permissions(self):
        self.permission_classes = self.permissions.get(self.action, self.permissions['default'])
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        user = self.request.user
        return self.queryset.filter(user=user)

    def get_serializer_context(self):
        ctx = super(TransactionPinsViewSet, self).get_serializer_context()
        if self.action not in ("create", "list"):
            ctx["pin"] = self.get_object()
        return ctx

    def partial_update(self, request, *args, **kwargs):
        data = request.data
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)


class WalletViewSet(viewsets.ModelViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = (IsCarMerchantAndAuthed,)

    def retrieve(self, request, pk=None):
        wallet = get_object_or_404(self.queryset, pk=pk)
        serialize = self.serializer_class(wallet)
        return Response(serialize.data, status=status.HTTP_200_OK)

    def get_queryset(self):
        return [self.request.user.merchant.wallet]

    def create(self, request, *args, **kwargs):
        return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)

    # def list(self, request, *args, **kwargs):
    #     return Response({"message": "Method not allowed"}, status=status.HTTP_405_METHOD_NOT_ALLOWED)


from django.contrib.auth import get_user_model as User


class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TradeSerializer
    queryset = Trade.objects.all()
    permission_classes = (IsCarMerchantAndAuthed,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TradeFilter

    def get_queryset(self):
        queryset = super(TradeViewSet, self).get_queryset()
        if self.request.query_params.get("self") and bool(self.request.query_params.get("self")) == True:
            return queryset.filter(units__merchant__id=self.request.user.merchant.id)
        return queryset


class TradeUnitViewSet(viewsets.ModelViewSet):
    serializer_class = TradeUnitSerializer
    queryset = TradeUnit.objects.all()
    permission_classes = (IsCarMerchantAndAuthed,)

    def get_serializer_context(self):
        ctx = super(TradeUnitViewSet, self).get_serializer_context()
        if self.action != "list":
            ctx["merchant"] = self.request.user.merchant
        return ctx

    def get_queryset(self):
        user: User = self.request.user
        return self.queryset.filter(merchant=user.merchant)

    def perform_create(self, serializer):
        user: User = self.request.user
        serializer.save(merchant=user.merchant)


class ActivityViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ActivitySerializer
    queryset = Activity.objects.all()
    permission_classes = (IsCarMerchantAndAuthed,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = ActivityFilter

    def get_queryset(self):
        user: CarMerchant = self.request.user.merchant
        return user.activity_set.all()
