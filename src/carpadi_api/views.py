from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import status
from rest_framework import permissions
from django_filters import rest_framework as filters
from src.carpadi_api.filters import TransactionsFilter, CarsFilter
from src.carpadi_api.serializers import CarSerializer
from src.models.serializers import TransactionsSerializer, CarMerchantSerializer, BankAccountSerializer, \
    CarBrandSerializer
from src.models.models import Transactions, CarMerchant, BankAccount, CarBrand, Car


# from .models import Transaction

# Create your views here

class CarMerchantViewSet(viewsets.ModelViewSet):
    serializer_class = CarMerchantSerializer
    queryset = CarMerchant.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# Create your views here.
class TransactionsViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    handles basic CRUD functionalities for transaction model
    """

    permissions = {'default': (permissions.IsAuthenticated, )}
    serializer_class = TransactionsSerializer
    queryset = Transactions.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TransactionsFilter

    def list(self, request):
        serialize = TransactionsSerializer(self.queryset, many=True)
        return Response(serialize.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        transaction = get_object_or_404(self.queryset, pk=pk)
        serialize = TransactionsSerializer(transaction)
        return Response(serialize.data, status=status.HTTP_200_OK)


class BankAccountViewSet(viewsets.ModelViewSet):
    serializer_class = BankAccountSerializer
    queryset = BankAccount.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CarBrandSerializerViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = CarBrandSerializer
    queryset = CarBrand.objects.all()


class CarViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = CarSerializer
    queryset = Car.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = CarsFilter


