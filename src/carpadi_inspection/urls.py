from src.carpadi_inspection.views import InspectionsViewSet, InspectionStagesViewSet
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register(r'', InspectionsViewSet)
router.register(r'stages', InspectionStagesViewSet)