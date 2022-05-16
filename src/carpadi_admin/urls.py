from rest_framework.routers import DefaultRouter

from src.carpadi_admin.views import (
    TransactionsViewSetAdmin,
    CarMerchantsViewSetAdmin,
    CarBrandSerializerViewSet,
    CarViewSet,
    WalletViewSetAdmin,
    TradeViewSetAdmin,
    DisbursementViewSetAdmin,
    ActivityViewSetAdmin, CarMaintenanceViewSetAdmin,
    SparePartsViewSet, DashboardViewSet
)
from src.models.views import UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet)
router.register(r'merchants', CarMerchantsViewSetAdmin)
router.register(r'transactions', TransactionsViewSetAdmin)
router.register(r'car-brands', CarBrandSerializerViewSet)
router.register(r'cars', CarViewSet)
router.register(r'wallets', WalletViewSetAdmin)
router.register(r'trades', TradeViewSetAdmin)
router.register(r'disbursements', DisbursementViewSetAdmin)
router.register(r'activities', ActivityViewSetAdmin)
router.register(r'maintenances', CarMaintenanceViewSetAdmin)
router.register(r'spare-parts', SparePartsViewSet)
router.register(r'dashboards',  DashboardViewSet, basename='dashboards')

# urlpatterns = transactions_router_admin.urls
