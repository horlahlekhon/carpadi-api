# Create your views here.
from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated, AllowAny

from src.carpadi_admin.filters import VehicleInfoFilter
from src.carpadi_admin.serializers import VehicleInfoSerializer
from src.carpadi_market.filters import CarProductFilter
from src.carpadi_market.serializers import CarProductSerializer, CarPurchaseOfferSerializer
from src.models.models import CarProduct, CarPurchaseOffer, VehicleInfo, CarBrand, CarStates
from src.models.permissions import IsAdmin
from src.models.serializers import CarBrandSerializer


class CarProductView(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    serializer_class = CarProductSerializer
    queryset = CarProduct.objects.all()
    filter_class = CarProductFilter
    filter_backends = (filters.DjangoFilterBackend,)

    def get_queryset(self):
        ordering = self.request.query_params.get("order_by")
        data = super(CarProductView, self).get_queryset()
        if ordering:
            data = data.order_by(ordering)
        print(data.query)
        return data


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


class CarBrandsMarketView(viewsets.ReadOnlyModelViewSet):
    serializer_class = CarBrandSerializer
    queryset = CarBrand.objects.filter(vehicleinfo__car__status=CarStates.Available)
    permission_classes = (AllowAny,)
