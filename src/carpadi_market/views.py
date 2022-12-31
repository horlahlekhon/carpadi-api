# Create your views here.
from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated, AllowAny

from src.carpadi_admin.filters import VehicleInfoFilter
from src.carpadi_admin.serializers import VehicleInfoSerializer
from src.carpadi_market.filters import CarProductFilter
from src.carpadi_market.serializers import CarProductSerializer, CarPurchaseOfferSerializer
from src.models.models import CarProduct, CarPurchaseOffer, VehicleInfo
from src.models.permissions import IsAdmin

class CarProductView(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    serializer_class = CarProductSerializer
    queryset = CarProduct.objects.all()
    filter_class = CarProductFilter
    filter_backends = (filters.DjangoFilterBackend,)


class CarPurchasesView(viewsets.GenericViewSet, mixins.CreateModelMixin, mixins.RetrieveModelMixin, mixins.ListModelMixin):
    # permission_classes = (AllowAny,)
    serializer_class = CarPurchaseOfferSerializer
    queryset = CarPurchaseOffer.objects.all()
    permissions = {'default': (AllowAny,), 'get': (IsAdmin,)}

    def get_permissions(self):
        self.permission_classes = self.permissions.get(self.action, self.permissions['default'])
        return super().get_permissions()


# class AgoraHomepageView(viewsets.GenericViewSet):
#     permission_classes = (AllowAny,)
#     serializer_class = CarProductSerializer
#     queryset = CarProduct.objects.all()
#     filter_class = CarProductFilter
#     filter_backends = (filters.DjangoFilterBackend,)
