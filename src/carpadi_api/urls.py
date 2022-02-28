from rest_framework.routers import SimpleRouter

from src.models.views import UserViewSet

investment_users_router = SimpleRouter()

investment_users_router.register(r'investments', UserViewSet)
