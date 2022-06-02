from rest_framework.routers import DefaultRouter

from src.models.views import UserViewSet

model_router = DefaultRouter()
model_router.register('users', UserViewSet)
