from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import status
from rest_framework import permissions

from src.models.serializers import Transactions_Serializer

from src.models.models import Transaction

# Create your views here.
class TransactionsViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    handles basic CRUD functionalities for transaction model
    """
    
    permissions = {'default': (permissions.IsAuthenticated, permissions.IsAdminUser)}
    serializer_class = Transactions_Serializer
    queryset = Transaction.object.all()

    def list(self, request):
        serialize = Transactions_Serializer(self.queryset, many=True)
        return Response(serialize.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        transaction = get_object_or_404(self.queryset, pk=pk)
        serialize = Transactions_Serializer(transaction)
        return Response(serialize.data, status=status.HTTP_200_OK)
