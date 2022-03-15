from rest_framework.routers import SimpleRouter, DefaultRouter

from src.models.views import UserViewSet

from src.carpadi_admin.views import TransactionsViewSetAdmin, WalletViewSetAdmin


admin_users_router = DefaultRouter()

admin_users_router.register(r'admins', UserViewSet)
admin_users_router.register(r'admins/wallets', WalletViewSetAdmin)
admin_users_router.register(r'admins/transactions', TransactionsViewSetAdmin)

urlpatterns = admin_users_router.urls
