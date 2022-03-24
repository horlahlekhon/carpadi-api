from rest_framework.routers import SimpleRouter, DefaultRouter

from src.models.views import UserViewSet

model_router = DefaultRouter()
model_router.register('users', UserViewSet)
