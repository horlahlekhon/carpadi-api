from rest_framework.routers import SimpleRouter

from src.models.views import UserViewSet
from src.carpadi_api.views import TransactionsViewSet

investment_users_router = SimpleRouter()
transactions_router = SimpleRouter()

investment_users_router.register(r'investments', UserViewSet)

transactions_router.register(r'transactions', TransactionsViewSet)
urlpatterns = transactions_router.urls
