from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import status
from rest_framework import permissions
from django_filters import rest_framework as filters
from src.carpadi_api.filters import TransactionsFilter
from src.models.serializers import Transactions_Serializer
from src.models.models import Transactions, CarMerchant

from src.carpadi_api.serializers import CarMerchantSerializer

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

    permissions = {'default': (permissions.IsAuthenticated)}
    serializer_class = Transactions_Serializer
    queryset = Transactions.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TransactionsFilter

    def list(self, request):
        serialize = Transactions_Serializer(self.queryset, many=True)
        return Response(serialize.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        transaction = get_object_or_404(self.queryset, pk=pk)
        serialize = Transactions_Serializer(transaction)
        return Response(serialize.data, status=status.HTTP_200_OK)
