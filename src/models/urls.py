from rest_framework.routers import DefaultRouter

from src.models.views import UserViewSet, AssetsViewSet, NotificationViewSet

model_router = DefaultRouter()
model_router.register('users', UserViewSet)
model_router.register('assets', AssetsViewSet)
model_router.register('notifications', NotificationViewSet)
