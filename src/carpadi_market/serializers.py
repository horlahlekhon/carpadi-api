from src.models.models import CarFeature, Assets, CarProduct, AssetEntityType
from rest_framework import serializers
from django.db.transaction import atomic


class CarFeatureSerializer(serializers.ModelSerializer):
    images = serializers.ListField(write_only=True, child=serializers.URLField(), min_length=0, default=[])
    feature_images = serializers.SerializerMethodField()

    class Meta:
        model = CarFeature
        fields = "__all__"
        read_only_fields = ('sales_image',)

    def get_feature_images(self, obj: CarFeature):
        pictures = Assets.objects.filter(object_id=obj.id).values_list("asset", flat=True)
        return pictures

    @atomic()
    def create(self, validated_data):
        images = validated_data.pop("images")
        feat = super(CarFeatureSerializer, self).create(validated_data)
        Assets.create_many(images=images, feature=feat, entity_type=AssetEntityType.Features)
        return feat



class CarProductSerializer(serializers.ModelSerializer):
    images = serializers.ListField(write_only=True, child=serializers.URLField(), min_length=1, required=True)
    product_images = serializers.SerializerMethodField()

    class Meta:
        model = CarProduct
        fields = "__all__"

    def get_product_images(self, obj: CarProduct):
        pictures = Assets.objects.filter(object_id=obj.id).values_list("asset", flat=True)
        return pictures

    @atomic()
    def create(self, validated_data):
        images = validated_data.pop("images")
        feat: CarProduct = super(CarProductSerializer, self).create(validated_data)
        Assets.create_many(images=images, feature=feat, entity_type=AssetEntityType.CarProduct)
        return feat

    @atomic()
    def update(self, instance, validated_data):
        images = validated_data.pop("images")
        feat: CarProduct = super(CarProductSerializer, self).update(instance, validated_data)
        Assets.create_many(images=images, feature=feat, entity_type=AssetEntityType.CarProduct)
        return feat
