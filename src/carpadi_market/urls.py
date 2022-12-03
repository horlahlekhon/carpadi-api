from rest_framework.routers import DefaultRouter

from src.carpadi_market.views import CarProductView, CarPurchasesView

router = DefaultRouter()
router.register(r'buy', CarProductView)
router.register('sell', CarPurchasesView)
