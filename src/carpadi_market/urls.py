from rest_framework.routers import DefaultRouter

from src.carpadi_market.views import CarProductView

router = DefaultRouter()
router.register(r'cars', CarProductView)
