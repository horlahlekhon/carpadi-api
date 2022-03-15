from rest_framework.routers import SimpleRouter, DefaultRouter

from src.carpadi_api.views import TransactionsViewSet, CarMerchantViewSet, WalletViewSet

router = DefaultRouter()

router.register(r'merchants', CarMerchantViewSet)
router.register(r'wallets', WalletViewSet)
router.register(r'transactions', TransactionsViewSet)

urlpatterns = router.urls
