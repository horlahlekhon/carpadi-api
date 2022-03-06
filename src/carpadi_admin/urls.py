from rest_framework.routers import SimpleRouter, DefaultRouter

from src.models.views import UserViewSet

admin_users_router = DefaultRouter()
admin_users_router.register(r'admins', UserViewSet)
