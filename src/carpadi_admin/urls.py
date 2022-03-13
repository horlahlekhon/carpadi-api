from rest_framework.routers import SimpleRouter, DefaultRouter

from src.models.views import UserViewSet

from rest_framework.routers import SimpleRouter
from src.carpadi_admin.views import TransactionsViewSetAdmin, CarMerchantsViewSetAdmin, CarBrandSerializerViewSet, \
    CarViewSet

from src.models.views import UserViewSet
router = DefaultRouter()
router.register('users', UserViewSet)
router.register(r'merchants', CarMerchantsViewSetAdmin)
router.register(r'transactions', TransactionsViewSetAdmin)
router.register(r'car-brands', CarBrandSerializerViewSet)
router.register(r'cars', CarViewSet)

# urlpatterns = transactions_router_admin.urls
