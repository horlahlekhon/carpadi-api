from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import status
from rest_framework.permissions import IsAdminUser
from django_filters import rest_framework as filters

from src.carpadi_admin.filters import TransactionsFilterAdmin, WalletFilterAdmin
from src.carpadi_admin.serializers import WalletSerializerAdmin

from src.models.serializers import TransactionsSerializer
from src.models.models import Transactions, Wallet


class WalletViewSetAdmin(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
     handles Wallet for admin
    """

    permissions = {'default': IsAdminUser}
    serializer_class = WalletSerializerAdmin
    queryset = Wallet.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = WalletFilterAdmin

    def list(self, request):
        serialize = WalletSerializerAdmin(self.queryset, many=True)
        return Response(serialize.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        wallet = get_object_or_404(self.queryset, pk=pk)
        serialize = WalletSerializerAdmin(wallet)
        return Response(serialize.data, status=status.HTTP_200_OK)


class TransactionsViewSetAdmin(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    handles basic CRUD functionalities for transaction model for admin
    """

    permissions = {'default': IsAdminUser}
    serializer_class = TransactionsSerializer
    queryset = Transactions.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TransactionsFilterAdmin

    def list(self, request):
        serialize = TransactionsSerializer(self.queryset, many=True)
        return Response(serialize.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        transaction = get_object_or_404(self.queryset, pk=pk)
        serialize = TransactionsSerializer(transaction)
        return Response(serialize.data, status=status.HTTP_200_OK)
