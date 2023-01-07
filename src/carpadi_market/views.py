# Create your views here.
from django.db.models import Max, Min
from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from src.carpadi_admin.filters import VehicleInfoFilter
from src.carpadi_admin.serializers import VehicleInfoSerializer
from src.carpadi_market.filters import CarProductFilter
from src.carpadi_market.serializers import CarProductSerializer, CarPurchaseOfferSerializer, HomepageSerializer
from src.models.models import CarProduct, CarPurchaseOffer, VehicleInfo, CarBrand, CarStates, Car
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


class CarMarketFiltersView(viewsets.ReadOnlyModelViewSet):
    serializer_class = CarBrandSerializer
    queryset = CarBrand.objects.filter(vehicleinfo__car__status=CarStates.Available)
    permission_classes = (AllowAny,)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        brands = self.get_serializer(instance=queryset, many=True).data
        vehicle_infos = VehicleInfo.objects.filter(car__status=CarStates.Available)
        transmissions = ['manual', 'automatic']
        years = queryset.order_by("year").distinct("year").values_list("year", flat=True)
        body_types = vehicle_infos.order_by("-car_type").distinct("car_type").values_list("car_type", flat=True)
        max_price = CarProduct.objects.aggregate(sum=Max("selling_price"))["sum"]
        min_price = CarProduct.objects.aggregate(sum=Min("selling_price"))["sum"]
        return Response(
            data=dict(
                years=years,
                transmissions=transmissions,
                brands=brands,
                body_types=body_types,
                price=dict(max=max_price, min=min_price),
            )
        )


class CarMarketHomePageView(viewsets.ReadOnlyModelViewSet):
    permission_classes = (AllowAny,)
    queryset = CarProduct.objects.all()

    def list(self, request, *args, **kwargs):
        model = self.request.query_params.get("model")
        make = self.request.query_params.get("make")
        if make:
            count = CarProduct.objects.filter(car__information__brand__name=make).count()
            return Response(data=dict(count=count))
        if model:
            count = CarProduct.objects.filter(car__information__brand__model=model).count()
            return Response(data=dict(count=count))
        data = HomepageSerializer(instance=None).to_representation(instance=None)
        return Response(data=data)
