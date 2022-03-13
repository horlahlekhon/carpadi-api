from rest_framework.routers import SimpleRouter, DefaultRouter

from src.models.views import UserViewSet

from src.carpadi_admin.views import TransactionsViewSetAdmin, WalletViewSetAdmin


admin_users_router = DefaultRouter()

router = SimpleRouter()
transactions_router_admin = SimpleRouter()
wallet_router_admin = SimpleRouter()

admin_users_router.register(r'admins', UserViewSet)

transactions_router_admin.register(r'admins/transactions', TransactionsViewSetAdmin)
wallet_router_admin.register(r'admins/wallets', WalletViewSetAdmin)
