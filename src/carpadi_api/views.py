from django.shortcuts import get_object_or_404
from rest_framework import viewsets, mixins
from rest_framework.response import Response
from rest_framework.views import status
from rest_framework import permissions

from src.models.serializers import TransactionSerializer

from src.models.models import Transaction

# Create your views here.
class Transactionsviewset(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    handles basic CRUD functionalities for transaction model
    """
    
    queryset = Transaction.object.all()
    serializer_class = TransactionSerializer
    permissions = {'default': (permissions.IsAuthenticated,)}

    def create(self, request, *args, **kwargs):
        """ create functions"""
        return super().create(request, *args, **kwargs)

    def list(self, request):
        return Response(self.queryset)

    def retrieve(self, request, pk=None):
        transaction = get_object_or_404(self.queryset, pk=pk)
        return Response(transaction)
