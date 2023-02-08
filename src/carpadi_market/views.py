# Create your views here.
import rest_framework.exceptions
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Max, Min
from django.db.transaction import atomic
from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

from src.carpadi_admin.filters import VehicleInfoFilter
from src.carpadi_admin.serializers import VehicleInfoSerializer, CarSerializer
from src.carpadi_market.filters import CarProductFilter, CarPurchasesFilter
from src.carpadi_market.serializers import CarProductSerializer, CarPurchaseOfferSerializer, HomepageSerializer
from src.models.models import CarProduct, CarPurchaseOffer, VehicleInfo, CarBrand, CarStates, Car, CarPurchasesStatus
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


class CarPurchasesView(viewsets.ModelViewSet):
    serializer_class = CarPurchaseOfferSerializer
    queryset = CarPurchaseOffer.objects.all()
    permissions = {'default': (AllowAny,), 'get': (IsAdmin,), 'patch': (IsAdmin,)}
    filter_class = CarPurchasesFilter
    filter_backends = (filters.DjangoFilterBackend,)

    def get_permissions(self):
        self.permission_classes = self.permissions.get(self.action, self.permissions['default'])
        return super().get_permissions()

    @atomic
    @action(detail=True, methods=['post'], url_path='approve', url_name='add_inspection')
    def approve_purchase_offer(self, request, pk=None):
        try:
            purchase: CarPurchaseOffer = self.get_queryset().get(id=pk)
            if purchase.car:
                return Response(data={"client_error": "This offer have been previously approved"}, status=400)
            colour = request.data.get("colour", "black")  # get default colour from settings
            data = dict(vin=purchase.vehicle_info.vin, colour=colour)
            ser = CarSerializer(data=data)
            ser.is_valid(raise_exception=True)
            instance = ser.save()
            purchase.car = instance
            purchase.status = CarPurchasesStatus.Accepted
            purchase.save(update_fields=["car", "status"])
            purchase_ser = self.get_serializer(instance=purchase).data
            return Response(data=purchase_ser)
        except ObjectDoesNotExist as e:
            return Response(data={"client_error": "That Purchase offer was not found"}, status=404)
        except ValueError as reason:
            return Response(data={"client_error": reason.args}, status=400)
        except serializers.ValidationError as reason:
            return Response(data=reason.detail, status=reason.status_code)
        except Exception as reason:
            raise rest_framework.exceptions.APIException(detail={"server_error": reason.args}, code=500) from reason


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
    queryset = CarProduct.objects.filter(car__status=CarStates.Available)

    def list(self, request, *args, **kwargs):
        model = self.request.query_params.get("model")
        make = self.request.query_params.get("make")
        if model and make:
            count = (
                self.get_queryset()
                .filter(car__information__brand__name__icontains=make, car__information__brand__model__icontains=model)
                .count()
            )
            return Response(data=dict(count=count))
        elif make:
            count = self.get_queryset().filter(car__information__brand__name__icontains=make).count()
            return Response(data=dict(count=count))
        elif model:
            count = self.get_queryset().filter(car__information__brand__model__icontains=model).count()
            return Response(data=dict(count=count))
        data = HomepageSerializer(instance=None).to_representation(instance=None)
        return Response(data=data)


class VehicleInfoViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    # permission_classes = (IsAdminUser,)
    permission_classes = (AllowAny,)
    serializer_class = VehicleInfoSerializer
    queryset = VehicleInfo.objects.all()
