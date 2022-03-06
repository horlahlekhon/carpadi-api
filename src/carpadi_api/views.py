from urllib import response
from django.shortcuts import get_object_or_404
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import status

from src.carpadi_api.serializers import CarMerchantSerializer

# from .models import Transaction

# Create your views here.
from ..models.models import CarMerchant


# class TransactionsCRUD(viewsets.ModelViewSet):
#     """
#     handles basic CRUD functionalities for transaction model
#     """
#
#     serializer_class = TransactionSerializer
#     queryset = Transaction.object.all()
#
#     def create(self, request):
#         """ create functions"""
#
#         transaction = self.get_object()
#         serializer = TransactionSerializer(data=request.data)
#
#         if serializer.is_valid():
#             return response(serializer.data)
#
#     def list(self, request):
#         return Response(self.queryset)
#
#     def retrieve(self, request, pk=None):
#         transaction = get_object_or_404(self.queryset, pk=pk)
#         return Response(transaction)
#
#     def update(self, request, pk=None):
#         """ nothng to write"""
#


class CarMerchantViewSet(viewsets.ModelViewSet):
    serializer_class = CarMerchantSerializer
    queryset = CarMerchant.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
