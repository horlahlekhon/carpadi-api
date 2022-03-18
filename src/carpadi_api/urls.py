from rest_framework.routers import SimpleRouter, DefaultRouter

from src.carpadi_api.views import (
    CarMerchantViewSet,
    BankAccountViewSet,
    CarBrandSerializerViewSet,
    CarViewSet,
    TransactionPinsViewSet,
)
from src.models.views import UserViewSet
from src.carpadi_api.views import TransactionsViewSet

router = DefaultRouter()
router.register(r'merchants', CarMerchantViewSet)
# router.register(r"merchants/merchants", )
router.register(r'transactions', TransactionsViewSet)
router.register(r'bank-accounts', BankAccountViewSet)
router.register(r'car-brands', CarBrandSerializerViewSet)
router.register(r'cars', CarViewSet)
router.register('pins', TransactionPinsViewSet)
# urlpatterns = router.urls
