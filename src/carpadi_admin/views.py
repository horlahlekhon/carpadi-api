from datetime import datetime

from django.shortcuts import get_object_or_404
from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import status

from src.carpadi_admin.filters import (
    TransactionsFilterAdmin,
    WalletFilterAdmin,
    DisbursementFilterAdmin,
    ActivityFilterAdmin,
    TradeFilterAdmin,
    SparePartsFilter,
    VehicleInfoFilter,
    CarMerchantFilter,
    CarFilter,
    CarDocumentsFilter,
)
from src.carpadi_admin.serializers import (
    CarSerializer,
    WalletSerializerAdmin,
    TransactionSerializer,
    DisbursementSerializerAdmin,
    AccountDashboardSerializer,
    TradeDashboardSerializer,
    InventoryDashboardSerializer,
    MerchantDashboardSerializer,
    TradeSerializerAdmin,
    CarMaintenanceSerializerAdmin,
    SparePartsSerializer,
    VehicleInfoSerializer,
    TradeUnitSerializerAdmin,
    HomeDashboardSerializer,
    CarMerchantAdminSerializer,
    SettingsSerializerAdmin,
    CarDocumentsSerializer,
)
from src.carpadi_api.filters import TradeUnitFilter
from src.carpadi_market.filters import CarProductFilter
from src.carpadi_market.serializers import CarProductSerializer
from src.models.models import (
    Transaction,
    CarBrand,
    Car,
    CarMerchant,
    Wallet,
    Trade,
    Disbursement,
    Activity,
    CarMaintenance,
    TradeUnit,
    TradeStates,
    SpareParts,
    CarProduct,
    VehicleInfo,
    Settings,
    CarDocuments, User,
)
from src.models.serializers import CarBrandSerializer, ActivitySerializer, UserSerializer


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


class CarMerchantsViewSetAdmin(viewsets.ReadOnlyModelViewSet, mixins.UpdateModelMixin):
    permission_classes = (IsAdminUser,)
    serializer_class = CarMerchantAdminSerializer
    queryset = CarMerchant.objects.all()
    filter_class = CarMerchantFilter
    filter_backends = (filters.DjangoFilterBackend,)

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
    permission_classes = (IsAdminUser,)


class CarViewSet(viewsets.ModelViewSet):
    serializer_class = CarSerializer
    permission_classes = (IsAdminUser,)
    queryset = Car.objects.all()
    filter_class = CarFilter
    filter_backends = (filters.DjangoFilterBackend,)

    # def update(self, request, *args, **kwargs):
    #     car = self.get_object()
    #     serializer = CarSerializer(car, data=request.data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WalletViewSetAdmin(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = WalletSerializerAdmin
    queryset = Wallet.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = WalletFilterAdmin


class TradeViewSetAdmin(viewsets.ModelViewSet):
    serializer_class = TradeSerializerAdmin
    permission_classes = (IsAdminUser,)
    queryset = Trade.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TradeFilterAdmin

    @action(detail=False, methods=['post'], url_path='disburse-rots', url_name='verify_transaction')
    def disburse_trade(self, request):
        """
        This method is used to disburse a trade that has been verified by the admin and money is ready to be disbursed
        to merchants.
        """
        trade = get_object_or_404(Trade, pk=request.query_params.get("trade"))
        if trade.trade_status != TradeStates.Completed:
            return Response(
                {"message": "Trade is not completed, please complete this trade before disbursing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        trade.close()
        return Response({"message": "Trade disbursed successfully"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='rollback-trade', url_name='rollback_trade')
    def rollback_trade(self, request):
        """
        This endpoint is used to roll back a trade that have been completed. and will do the follwoing
        * set all disbursements to failed and also fail all related transactions
        * return the unit_value back to the wallet's trading_cash
        * set the status of the trade back to Purchased
        """
        trade = get_object_or_404(Trade, pk=request.data.get("trade"))
        if trade.trade_status != TradeStates.Completed:
            return Response(
                {"message": "Trade is not completed, please complete this trade before disbursing"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        trade.rollback()
        return Response({"message": "Trade rolled back to purchased state"}, status=status.HTTP_200_OK)


class DisbursementViewSetAdmin(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = DisbursementSerializerAdmin
    queryset = Disbursement.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = DisbursementFilterAdmin


class ActivityViewSetAdmin(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = ActivitySerializer
    queryset = Activity.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = ActivityFilterAdmin


class CarMaintenanceViewSetAdmin(viewsets.ModelViewSet):
    serializer_class = CarMaintenanceSerializerAdmin
    permission_classes = (IsAdminUser,)
    queryset = CarMaintenance.objects.all()

    def get_queryset(self):
        queryset = CarMaintenance.objects.all()
        car = self.request.query_params.get('car', None)
        if car is not None:
            queryset = queryset.filter(car_id=car)
        return queryset


class SparePartsViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = SparePartsSerializer
    queryset = SpareParts.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = SparePartsFilter


class DashboardViewSet(viewsets.GenericViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = AccountDashboardSerializer

    @action(detail=False, methods=['get'], url_path='accounts', url_name='account_dashboard')
    def accounts(self, request, *args, **kwargs):
        data = dict(
            start_date=request.query_params.get('start_date', datetime.now().date().replace(day=1)),
            end_date=request.query_params.get('end_date', datetime.now().date()),
        )
        serializer = self.get_serializer(data=data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='trades', url_name='trade_dashboard')
    def trades(self, request, *args, **kwargs):
        ser = TradeDashboardSerializer(data=request.query_params)
        if ser.is_valid():
            return Response(ser.data, status=status.HTTP_200_OK)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='inventory', url_name='inventory_dashboard')
    def inventory(self, request, *args, **kwargs):
        ser = InventoryDashboardSerializer(data=request.query_params)
        if ser.is_valid():
            return Response(ser.data, status=status.HTTP_200_OK)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='merchants', url_name='merchants_dashboard')
    def merchants(self, request, *args, **kwargs):
        ser = MerchantDashboardSerializer(data=request.query_params)
        if ser.is_valid():
            return Response(ser.data, status=status.HTTP_200_OK)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='home', url_name='home_dashboard')
    def home(self, request, *args, **kwargs):
        data = dict(
            start_date=request.query_params.get('start_date', datetime.now().date().replace(day=1)),
            end_date=request.query_params.get('end_date', datetime.now().date()),
            filter_year_only=request.query_params.get("filter_year_only", False),
        )

        serializer = HomeDashboardSerializer(data=data)
        if serializer.is_valid():
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CarProductViewSetAdmin(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = CarProductSerializer
    queryset = CarProduct.objects.all()
    filter_class = CarProductFilter
    filter_backends = (filters.DjangoFilterBackend,)


class VehicleInfoViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = VehicleInfoSerializer
    queryset = VehicleInfo.objects.all()
    filter_class = VehicleInfoFilter
    filter_backends = (filters.DjangoFilterBackend,)


class TradeUnitReadOnlyView(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAdminUser,)
    serializer_class = TradeUnitSerializerAdmin
    queryset = TradeUnit.objects.all()
    filter_class = TradeUnitFilter
    filter_backends = (filters.DjangoFilterBackend,)


class SettingsViewset(viewsets.GenericViewSet, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.ListModelMixin):
    serializer_class = SettingsSerializerAdmin
    permission_classes = (IsAdminUser,)
    queryset = Settings.objects.all()


class CarDocumentsViewset(viewsets.ModelViewSet):
    serializer_class = CarDocumentsSerializer
    queryset = CarDocuments.objects.all()
    permission_classes = (IsAdminUser,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = CarDocumentsFilter

    def get_serializer(self, *args, **kwargs):
        """if an array is passed, set serializer to many"""
        if isinstance(self.request.data, list):
            kwargs['many'] = True
        return super(CarDocumentsViewset, self).get_serializer(*args, **kwargs)



