from rest_framework.routers import DefaultRouter

from src.carpadi_market.views import (
    CarProductView,
    CarPurchasesView,
    CarMarketFiltersView,
    CarMarketHomePageView,
    VehicleInfoViewSet,
)

router = DefaultRouter()
router.register(r'buy', CarProductView)
router.register('sell', CarPurchasesView)
router.register('filters', CarMarketFiltersView)
router.register('home', CarMarketHomePageView)
router.register('vehicle-by-vin', VehicleInfoViewSet)
