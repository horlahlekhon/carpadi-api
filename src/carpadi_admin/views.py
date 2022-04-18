from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import status
from rest_framework.permissions import IsAdminUser
from django_filters import rest_framework as filters

from src.carpadi_admin.filters import (
    TransactionsFilterAdmin,
    WalletFilterAdmin,
    DisbursementFilterAdmin,
    ActivityFilterAdmin,
    TradeFilterAdmin,
    SparePartsFilter
)
from src.carpadi_admin.serializers import (
    CarSerializer,
    WalletSerializerAdmin,
    TransactionSerializer,
    DisbursementSerializerAdmin,
    ActivitySerializerAdmin,
    TradeSerializer,
    SparePartsSerializer
)
from src.models.serializers import CarBrandSerializer, CarMerchantSerializer
from src.models.models import (
    Transaction,
    CarBrand,
    Car,
    CarMerchant,
    Wallet,
    Trade,
    Disbursement,
    Activity,
    SpareParts
)


# Create your views here.
class TransactionsViewSetAdmin(viewsets.ReadOnlyModelViewSet):
    """
    handles basic CRUD functionalities for transaction model for admin
    """

    permissions = {'default': (IsAdminUser,)}
    serializer_class = TransactionSerializer
    queryset = Transaction.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TransactionsFilterAdmin


class CarMerchantsViewSetAdmin(viewsets.ReadOnlyModelViewSet):
    permissions = {'default': (IsAdminUser,)}
    serializer_class = CarMerchantSerializer
    queryset = CarMerchant.objects.all()

    # def list(self, request):
    #     serialize = CarMerchantSerializer(self.queryset, many=True)
    #     return Response(serialize.data, status=status.HTTP_200_OK)
    #
    # def retrieve(self, request, pk=None):
    #     transaction = get_object_or_404(self.queryset, pk=pk)
    #     serialize = TransactionsSerializer(transaction)
    #     return Response(serialize.data, status=status.HTTP_200_OK)


class CarBrandSerializerViewSet(viewsets.ModelViewSet):
    serializer_class = CarBrandSerializer
    queryset = CarBrand.objects.all()
    permissions = {'default': (IsAdminUser,)}


class CarViewSet(viewsets.ModelViewSet):
    serializer_class = CarSerializer
    permissions = {'default': (IsAdminUser,)}
    queryset = Car.objects.all()


class WalletViewSetAdmin(viewsets.ReadOnlyModelViewSet):
    permissions = {'default': (IsAdminUser,)}
    serializer_class = WalletSerializerAdmin
    queryset = Wallet.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = WalletFilterAdmin


class TradeViewSetAdmin(viewsets.ModelViewSet):
    serializer_class = TradeSerializer
    permissions = {'default': (IsAdminUser,)}
    queryset = Trade.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TradeFilterAdmin


class DisbursementViewSetAdmin(viewsets.ReadOnlyModelViewSet):
    permissions = {'default': (IsAdminUser,)}
    serializer_class = DisbursementSerializerAdmin
    queryset = Disbursement.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = DisbursementFilterAdmin


class ActivityViewSetAdmin(viewsets.ReadOnlyModelViewSet):
    permissions = {'default': (IsAdminUser,)}
    serializer_class = ActivitySerializerAdmin
    queryset = Activity.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = ActivityFilterAdmin


class SparePartsViewSet(viewsets.ModelViewSet):
    permissions = {'default': (IsAdminUser,)}
    serializer_class = SparePartsSerializer
    queryset = SpareParts.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = SparePartsFilter
