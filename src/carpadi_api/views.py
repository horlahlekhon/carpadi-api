from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import status
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters

from src.carpadi_api.filters import TransactionsFilter
from src.models.serializers import TransactionsSerializer, WalletSerializer
from src.models.models import Transactions, CarMerchant, Wallet

from src.carpadi_api.serializers import CarMerchantSerializer


class CarMerchantViewSet(viewsets.ModelViewSet):
    serializer_class = CarMerchantSerializer
    queryset = CarMerchant.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WalletViewSet(mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    handles wallet operation for a particular merchant
    """

    permissions = {'default': IsAuthenticated}
    queryset = Wallet.objects.all()
    filter_backends = filters.DjangoFilterBackend

    def create(self, request):
        serialize = WalletSerializer(data=request.data)
        if serialize.is_valid():
            serialize.save()
            return Response(serialize.validated_data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, pk=None):
        wallet = get_object_or_404(self.queryset, pk=pk)
        serialize = WalletSerializer(wallet)
        return Response(serialize.data, status=status.HTTP_200_OK)


class TransactionsViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    handles basic CRUD functionalities for transaction model
    """

    permissions = {'default': IsAuthenticated}
    queryset = Transactions.objects.all()
    filter_backends = filters.DjangoFilterBackend
    filter_class = TransactionsFilter

    def list(self, request):
        serialize = TransactionsSerializer(self.queryset, many=True)
        return Response(serialize.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        transaction = get_object_or_404(self.queryset, pk=pk)
        serialize = TransactionsSerializer(transaction)
        return Response(serialize.data, status=status.HTTP_200_OK)
