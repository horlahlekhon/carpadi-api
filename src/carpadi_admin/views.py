from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import status
from rest_framework import permissions
from django_filters import rest_framework as filters

from src.carpadi_admin.filters import TransactionsFilterAdmin
from src.models.serializers import Transactions_Serializer
from src.models.models import Transactions

# Create your views here.
class TransactionsViewSetAdmin(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    handles basic CRUD functionalities for transaction model for admin
    """

    permissions = {'default': (permissions.IsAdminUser)}
    serializer_class = Transactions_Serializer
    queryset = Transactions.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = TransactionsFilterAdmin

    def list(self, request):
        serialize = Transactions_Serializer(self.queryset, many=True)
        return Response(serialize.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        transaction = get_object_or_404(self.queryset, pk=pk)
        serialize = Transactions_Serializer(transaction)
        return Response(serialize.data, status=status.HTTP_200_OK)
