from rest_framework.routers import SimpleRouter

from src.models.views import UserViewSet

admin_users_router = SimpleRouter()

admin_users_router.register(r'admins', UserViewSet)
