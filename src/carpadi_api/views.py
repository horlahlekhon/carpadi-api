from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import status
from django_filters import rest_framework as filters
from src.carpadi_api.filters import TransactionsFilter, CarsFilter
from src.carpadi_api.serializers import (
    CarSerializer, TransactionPinSerializers,
    UpdateTransactionPinSerializers,
    CarMerchantUpdateSerializer,
)
from src.models.permissions import IsCarMerchantAndAuthed
from src.models.serializers import (
    TransactionSerializer, CarMerchantSerializer,
    BankAccountSerializer, CarBrandSerializer, WalletSerializer,
)
from src.models.models import Transaction, CarMerchant, BankAccount, CarBrand, Car, TransactionPin, TransactionPinStatus, Wallet



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


class CarMerchantViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
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


class TransactionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    handles basic CRUD functionalities for transaction model
    """

    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TransactionsFilter
    permission_classes = (IsCarMerchantAndAuthed,)

    def list(self, request):
        serialize = self.serializer_class(self.queryset, many=True)
        return Response(serialize.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        transaction = get_object_or_404(self.queryset, pk=pk)
        serialize = self.serializer_class(transaction)
        return Response(serialize.data, status=status.HTTP_200_OK)


class BankAccountViewSet(viewsets.ModelViewSet):
    serializer_class = BankAccountSerializer
    queryset = BankAccount.objects.all()
    permissions = {'default': (IsCarMerchantAndAuthed,)}

    def get_permissions(self):
        self.permission_classes = self.permissions.get(self.action, self.permissions['default'])
        return super().get_permissions()


class CarBrandSerializerViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = CarBrandSerializer
    queryset = CarBrand.objects.all()


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


class WalletViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    # filter_backends = (filters.DjangoFilterBackend,)
    # filter_class = TransactionsFilter
    permission_classes = (IsCarMerchantAndAuthed,)

    def retrieve(self, request, pk=None):
        wallet = get_object_or_404(self.queryset, pk=pk)
        serialize = self.serializer_class(wallet)
        return Response(serialize.data, status=status.HTTP_200_OK)
