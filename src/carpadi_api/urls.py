from rest_framework.routers import DefaultRouter

from src.carpadi_api.views import TransactionsViewSet, CarMerchantViewSet, WalletViewSet

router = DefaultRouter()
router.register(r'merchants', CarMerchantViewSet)
# router.register(r"merchants/merchants", )
router.register(r'wallets', WalletViewSet)
router.register(r'transactions', TransactionsViewSet)
