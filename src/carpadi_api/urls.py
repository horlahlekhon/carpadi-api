from rest_framework.routers import SimpleRouter, DefaultRouter

from src.carpadi_api.views import CarMerchantViewSet
from src.models.views import UserViewSet
from src.carpadi_api.views import TransactionsViewSet

router = DefaultRouter()
router.register(r'merchants', CarMerchantViewSet)
# router.register(r"merchants/merchants", )
router.register(r'transactions', TransactionsViewSet)
# urlpatterns = router.urls
