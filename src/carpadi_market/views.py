from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters import rest_framework as filters
from src.carpadi_market.filters import CarProductFilter
from src.carpadi_market.serializers import CarProductSerializer
from src.models.models import CarProduct


class CarProductView(viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = CarProductSerializer
    queryset = CarProduct.objects.all()
    filter_class = CarProductFilter
    filter_backends = (filters.DjangoFilterBackend, )
