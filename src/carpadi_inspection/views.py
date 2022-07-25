from django.shortcuts import render

# Create your views here.
from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAdminUser

from src.carpadi_inspection.filters import InspectionsFilter, InspectionsStageFilter
from src.carpadi_inspection.serializers import InspectionSerializer, InspectionStageSerializer
from src.models.models import Inspections, InspectionStage


class InspectionsViewSet(viewsets.ModelViewSet):
    serializer_class = InspectionSerializer
    queryset = Inspections.objects.all()
    permission_classes = (IsAdminUser,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = InspectionsFilter


class InspectionStagesViewSet(viewsets.ModelViewSet):
    serializer_class = InspectionStageSerializer
    queryset = InspectionStage.objects.all()
    permission_classes = (IsAdminUser,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = InspectionsStageFilter

