from django_filters import rest_framework as filters

from src.models.models import Inspections, InspectionStage


class InspectionsFilter(filters.FilterSet):
    class Meta:
        model = Inspections
        fields = (
            "inspection_date",
            "status",
            "inspection_verdict",
            "inspector",
            "inspection_assigner",
            "car",
        )


class InspectionsStageFilter(filters.FilterSet):
    class Meta:
        model = InspectionStage
        fields = (
            "inspection",
            "part_name",
            "score",
        )
