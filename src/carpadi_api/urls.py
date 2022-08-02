from rest_framework.routers import DefaultRouter

from src.carpadi_api.views import (
    CarMerchantViewSet,
    BankAccountViewSet,
    CarBrandSerializerViewSet,
    CarViewSet,
    TransactionPinsViewSet,
    TransactionViewSet,
    WalletViewSet,
    ActivityViewSet,
    TradeViewSet,
    TradeUnitViewSet,
)

router = DefaultRouter()
router.register(r'merchants', CarMerchantViewSet)
# router.register(r"merchants/merchants", )
router.register(r'transactions', TransactionViewSet)
router.register(r'bank-accounts', BankAccountViewSet)
router.register(r'car-brands', CarBrandSerializerViewSet)
router.register(r'cars', CarViewSet)
router.register('pins', TransactionPinsViewSet)
router.register('wallets', WalletViewSet)
router.register('activities', ActivityViewSet)
router.register('trades', TradeViewSet)
router.register('trade-units', TradeUnitViewSet)
# urlpatterns = router.urls
