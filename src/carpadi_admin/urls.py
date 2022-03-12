from rest_framework.routers import SimpleRouter, DefaultRouter

from src.models.views import UserViewSet

admin_users_router = DefaultRouter()
from rest_framework.routers import SimpleRouter
from src.carpadi_admin.views import TransactionsViewSetAdmin

from src.models.views import UserViewSet

router = SimpleRouter()
transactions_router_admin = SimpleRouter()

admin_users_router.register(r'admins', UserViewSet)

transactions_router_admin.register(r'admins/transactions', TransactionsViewSetAdmin)
urlpatterns = transactions_router_admin.urls
