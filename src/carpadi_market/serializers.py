from typing import List, Dict

from django.db.transaction import atomic
from rest_framework import serializers

from src.models.models import CarFeature, Assets, CarProduct, AssetEntityType, Trade, VehicleInfo, CarStates, Car


class CarSerializerField(serializers.RelatedField):
    def to_internal_value(self, data):
        try:
            return Car.objects.get(pk=data, product=None)
        except Car.DoesNotExist as reason:
            raise serializers.ValidationError(
                f"Car with id {data} does not exist or " f"is already listed under a car product"
            ) from reason

    def to_representation(self, value: Car):
        return dict(
            id=value.id,
            status=value.status,
            model=value.information.brand.model,
            vin=value.vin,
            make=value.information.brand.name,
            year=value.information.brand.year,
            fuel_type=value.information.fuel_type,
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

    # TODO validate that the car has trade and return error
    def validate_car(self, car: Car):
        pass

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

    def to_representation(self, instance):
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
