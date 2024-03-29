from typing import List, Dict, Optional

from django.db.transaction import atomic
from rest_framework import serializers

from src.carpadi_admin.serializers import VehicleInfoSerializer, CarSerializer
from src.carpadi_inspection.serializers import InspectionSerializer
from src.models.models import (
    CarFeature,
    Assets,
    CarProduct,
    AssetEntityType,
    Trade,
    VehicleInfo,
    CarStates,
    Car,
    CarPurchaseOffer,
    User,
    UserTypes,
    CarTypes,
    CarBrand,
    CarProductStatus,
    CarSellers,
)
from src.models.validators import PhoneNumberValidator


class CarSerializerField(serializers.RelatedField):
    def to_internal_value(self, data):
        try:
            return Car.objects.get(pk=data, product=None)
        except Car.DoesNotExist as reason:
            raise serializers.ValidationError('Car does not exist or is already listed under a car product') from reason

    def to_representation(self, value: Car):
        return dict(
            id=value.id,
            status=value.status,
            model=value.information.brand.model,
            vin=value.vin,
            make=value.information.brand.name,
            year=value.information.brand.year,
            fuel_type=value.information.fuel_type,
            transmission=value.information.transmission,
            engine=value.information.engine,
            car_type=value.information.car_type,
            colour=value.colour,
            name=value.name,
            cylinders=value.information.num_of_cylinders,
            previous_owners=value.information.previous_owners,
            engine_power=value.information.engine_power,
            torque=value.information.torque,
            last_service_mileage=value.information.last_service_mileage,
            last_service_date=value.information.last_service_date,
            drive_type=value.information.drive_type,
            specifications=value.information.specifications,
            mileage=value.information.mileage,
        )


class CarFeatureSerializer(serializers.ModelSerializer):
    images = serializers.ListField(write_only=True, child=serializers.URLField(), min_length=0, default=[])
    feature_images = serializers.SerializerMethodField()

    class Meta:
        model = CarFeature
        fields = "__all__"
        read_only_fields = ('sales_image',)

    def get_feature_images(self, obj: CarFeature):
        return Assets.objects.filter(object_id=obj.id).values_list("asset", flat=True)

    @atomic()
    def create(self, validated_data):
        images = validated_data.pop("images")
        feat = super(CarFeatureSerializer, self).create(validated_data)
        Assets.create_many(images=images, feature=feat, entity_type=AssetEntityType.Features)
        return feat


class CarProductSerializer(serializers.ModelSerializer):
    images = serializers.ListField(write_only=True, child=serializers.URLField(), min_length=1, required=True)
    product_images = serializers.SerializerMethodField()
    features = serializers.ListField(write_only=True, child=serializers.DictField(), min_length=1, required=False, default=[])
    car_features = serializers.SerializerMethodField()
    highlight = serializers.CharField(required=False, max_length=100)
    trade = serializers.SerializerMethodField()
    car = CarSerializerField(queryset=Car.objects.filter(status=CarStates.Available))

    class Meta:
        model = CarProduct
        fields = "__all__"

    def get_trade(self, obj: CarProduct):
        if obj.car.status == CarStates.Available and obj.car.trade:
            return obj.car.trade.id
        return None

    def validate_car(self, car: Car):
        try:
            if car.trade:
                return car
            raise serializers.ValidationError(
                "car is not available for trade." " None traded cars are not allowed for sales listing"
            )
        except Exception as reason:
            raise serializers.ValidationError(
                "car is not available for trade." " None traded cars are not allowed for sales listing"
            ) from reason

    def get_car_features(self, obj: CarProduct):
        return CarFeatureSerializer(instance=obj.features.all(), many=True).data

    def _create_features(self, attr: List[Dict], product_id: str):
        if attr:
            data = [d.update({"car": product_id}) for d in attr]
            feature_serializer = CarFeatureSerializer(data=attr, many=True)
            feature_serializer.is_valid(raise_exception=True)
            return feature_serializer.save()
        return None

    def get_product_images(self, obj: CarProduct):
        return Assets.objects.filter(object_id=obj.id).values_list("asset", flat=True)

    # def validate_car(self):
    #     ...

    # def vehicle_details(self, vehicle: VehicleInfo):
    #     return dict()

    def to_representation(self, instance: Car):
        data = super(CarProductSerializer, self).to_representation(instance)

        return data

    @atomic()
    def create(self, validated_data):
        images = validated_data.pop("images", [])
        car_features = validated_data.pop("features", [])
        product: CarProduct = super(CarProductSerializer, self).create(validated_data)
        Assets.create_many(images=images, feature=product, entity_type=AssetEntityType.CarProduct)
        features = self._create_features(car_features, product.id)
        return product

    @atomic()
    def update(self, instance, validated_data):
        images = validated_data.pop("images", [])
        car_features = validated_data.pop("features", [])
        features = self._create_features(car_features, instance.id)
        feat: CarProduct = super(CarProductSerializer, self).update(instance, validated_data)
        Assets.create_many(images=images, feature=feat, entity_type=AssetEntityType.CarProduct)
        return feat


class PurchasesUserSerializer(serializers.ModelSerializer):
    name = serializers.CharField()
    phone = serializers.CharField(validators=[PhoneNumberValidator])
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = CarSellers
        fields = (
            "name",
            "phone",
            "email",
        )

    def create(self, validated_data):
        if car_seller := CarSellers.objects.filter(phone=validated_data["phone"], email=validated_data["email"]).first():
            return car_seller
        return super(PurchasesUserSerializer, self).create(validated_data=validated_data)


class CarPurchasesCarSerializerField(serializers.RelatedField):
    def to_representation(self, value):
        return CarSerializer(instance=value).data


class CarPurchaseOfferSerializer(serializers.ModelSerializer):
    user = serializers.DictField(write_only=True)
    seller = serializers.SerializerMethodField()
    car = CarPurchasesCarSerializerField(read_only=True)

    class Meta:
        model = CarPurchaseOffer
        fields = "__all__"

    def get_seller(self, obj: CarPurchaseOffer):
        return PurchasesUserSerializer(instance=obj.seller).data

    @atomic
    def create(self, validated_data):
        user = validated_data.pop("user")
        ser = PurchasesUserSerializer(data=user)
        ser.is_valid(raise_exception=True)
        usr = ser.save()
        validated_data["seller"] = usr
        return CarPurchaseOffer.objects.create(**validated_data)


class HomepageSerializer(serializers.Serializer):
    def to_representation(self, instance):
        car_types = CarTypes.to_array()
        available_models = [
            dict(make=i.name, model=i.model) for i in CarBrand.objects.filter(vehicleinfo__car__status=CarStates.Available)
        ]  # noqa
        available_cars_count = CarProduct.objects.filter(status=CarProductStatus.Active).count()
        return dict(car_types=car_types, brands=available_models, available_cars_count=available_cars_count)
