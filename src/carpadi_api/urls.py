from rest_framework.routers import SimpleRouter

from src.models.views import UserViewSet
from src.carpadi_api.views import TransactionsViewSet

investment_users_router, transaction_router = SimpleRouter()


investment_users_router.register(r'investments', UserViewSet)

transaction_router.register(r'transactions', TransactionsViewSet)
urlpatterns = transaction_router.urls
