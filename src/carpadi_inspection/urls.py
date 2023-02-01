from rest_framework.routers import DefaultRouter

from src.carpadi_inspection.views import InspectionsViewSet, InspectionStagesViewSet, InspectorsViewset

router = DefaultRouter()
router.register(r'inspections', InspectionsViewSet)
router.register(r'<uuid:pk>/stages', InspectionStagesViewSet)
router.register(r'inspectors', InspectorsViewset)
