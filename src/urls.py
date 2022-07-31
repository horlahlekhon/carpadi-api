from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path, include, reverse_lazy
from django.views.generic.base import RedirectView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from src.carpadi_admin.urls import router as admin_router
from src.carpadi_api.urls import router as api_router
from src.files.urls import files_router
from src.models.urls import model_router
from src.carpadi_market.urls import router as market_router
from src.models.views import TokenObtainPairViewMod
from src.social.views import exchange_token, complete_twitter_login
from src.carpadi_inspection.urls import router as inspection_router

schema_view = get_schema_view(
    openapi.Info(title="Carpadi API", default_version='v1'),
    public=True,
)

market_router_set = DefaultRouter()
market_router_set.registry.extend(market_router.registry)

admin_router_set = DefaultRouter()
admin_router_set.registry.extend(admin_router.registry)

api_router_set = DefaultRouter()
api_router_set.registry.extend(api_router.registry)
api_router_set.registry.extend(files_router.registry)

generic_router = DefaultRouter()
generic_router.registry.extend(model_router.registry)

urlpatterns = [
    # admin panel
    path('admin/', admin.site.urls),
    url(r'^jet/', include('jet.urls', 'jet')),  # Django JET URLS
    # summernote editor
    path('summernote/', include('django_summernote.urls')),
    # api
    path('api/v1/', include(generic_router.urls)),
    path('api/v1/merchants/', include(api_router_set.urls)),
    path('api/v1/admins/', include(admin_router_set.urls)),
    path('api/v1/market/', include(market_router.urls)),
    path('api/v1/inspections', include(inspection_router.urls)),
    url(r'^api/v1/password_reset/', include('django_rest_passwordreset.urls', namespace='password_reset')),
    # auth
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/v1/auth/login/', TokenObtainPairViewMod.as_view(), name='token_obtain_pair'),
    # path('api/v1/auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token-refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # social login
    url('', include('social_django.urls', namespace='social')),
    url(r'^complete/twitter/', complete_twitter_login),
    url(r'^api/v1/social/(?P<backend>[^/]+)/$', exchange_token),
    # swagger docs
    url(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    url(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    url(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    url(r'^health/', include('health_check.urls')),
    # the 'api-root' from django rest-frameworks default router
    re_path(r'^$', RedirectView.as_view(url=reverse_lazy('api-root'), permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
