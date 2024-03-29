# Create your views here.
import rest_framework.exceptions
from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser, IsAuthenticated

from src.carpadi_inspection.filters import InspectionsFilter, InspectionsStageFilter
from src.carpadi_inspection.serializers import InspectionSerializer, InspectionPartSerializer
from src.models.models import Inspections, InspectionStage, User
from src.models.serializers import UserSerializer


class InspectionsViewSet(viewsets.ModelViewSet):
    serializer_class = InspectionSerializer
    queryset = Inspections.objects.all()
    permission_classes = (IsAdminUser,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = InspectionsFilter


class InspectionStagesViewSet(viewsets.ModelViewSet):
    serializer_class = InspectionPartSerializer
    queryset = InspectionStage.objects.all()
    permission_classes = (IsAdminUser,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = InspectionsStageFilter

    def get_queryset(self):
        if inspection := self.request.query_params.get("inspection"):
            return self.queryset.filter(inspection_id=inspection)
        raise rest_framework.exceptions.APIException(
            detail=dict(client_error="A valid inspection is required to interact with inspection stages")
        )

    def get_serializer_context(self):
        ctx = super(InspectionStagesViewSet, self).get_serializer_context()
        insp = self.request.query_params.get("inspection")
        if inspection := Inspections.objects.filter(pk=insp).first():
            ctx["inspection"] = inspection
            return ctx
        raise rest_framework.exceptions.APIException(
            detail=dict(client_error="A valid inspection is required to interact with inspection stages")
        )


class InspectorsViewset(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.filter(is_staff=True, is_superuser=False)
    serializer_class = UserSerializer
    permission_classes = (IsAdminUser, IsAuthenticated)
