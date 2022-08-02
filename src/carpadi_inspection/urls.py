from rest_framework.routers import DefaultRouter

from src.carpadi_inspection.views import InspectionsViewSet, InspectionStagesViewSet

router = DefaultRouter()
router.register(r'', InspectionsViewSet)
router.register(r'stages', InspectionStagesViewSet)
