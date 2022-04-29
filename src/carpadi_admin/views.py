import datetime

from django.shortcuts import get_object_or_404
from rest_framework import viewsets
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
)
from src.carpadi_admin.serializers import (
    CarSerializer,
    WalletSerializerAdmin,
    TransactionSerializer,
    DisbursementSerializerAdmin,
    ActivitySerializerAdmin,
    TradeSerializer,
    DashboardSerializerAdmin,

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


class DashboardViewSetAdmin(viewsets.ViewSet):
    permissions = {'default': (IsAdminUser,)}
    serializer_class = DashboardSerializerAdmin,

    @staticmethod
    def get_graph(request):
        date = request.GET.get("date")
        data = DashboardSerializerAdmin.get_rot_vs_ttc(month=date.month, year=date.year)
        return Response(data=data, status=200)

    @staticmethod
    def get_summary(request):
        date = request.GET.get("date")
        data = DashboardSerializerAdmin.get_cars_summary(month=date.month, year=date.year)
        return Response(data=data, status=200)

    @staticmethod
    def get_bts(request):
        date = request.GET.get("date")
        data = DashboardSerializerAdmin.get_average_bts(month=date.month, year=date.year)
        return Response(data=data, status=200)

    @staticmethod
    def get_trading_users(request):
        date = request.GET.get("date")
        data = DashboardSerializerAdmin.get_number_of_users_trading(month=date.month, year=date.year)
        return Response(data=data, status=200)

    @staticmethod
    def get_shares(request):
        date: datetime.date = request.GET.get("date")
        data = DashboardSerializerAdmin.get_total_available_shares(month=date.month, year=date.year)
        return Response(data=data, status=200)

    @staticmethod
    def get_shares_value(request):
        date = request.GET.get("date")
        data = DashboardSerializerAdmin.get_available_shares_value(month=date.month, year=date.year)
        return Response(data=data, status=200)

    @staticmethod
    def get_total_trading_cash(request):
        date = request.GET.get("date")
        data = DashboardSerializerAdmin.get_total_trading_cash(month=date.month, year=date.year)
        return Response(data=data, status=200)

    @staticmethod
    def get_cars_with_shares(request):
        date = request.GET.get("date")
        data = DashboardSerializerAdmin.get_cars_with_available_share(month=date.month, year=date.year)
        return Response(data=data, status=200)

    @staticmethod
    def get_recent_trading_activities(request):
        date = request.GET.get("date")
        data = DashboardSerializerAdmin.get_available_shares_value(month=date.month, year=date.year)
        return Response(data=data, status=200)
