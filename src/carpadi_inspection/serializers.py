from django.db.transaction import atomic
from rest_framework import serializers

from src.models.models import InspectionStage, Inspections, User, CarStates, Assets, AssetEntityType
from src.models.serializers import AssetsSerializer


class InspectionStageSerializer(serializers.ModelSerializer):
    pictures = serializers.ListField(child=serializers.URLField(), required=False, default=[], write_only=True)
    images = serializers.SerializerMethodField()

    class Meta:
        model = InspectionStage
        fields = "__all__"

    def get_images(self, instance: InspectionStage):
        return Assets.objects.filter(object_id=instance.id).values_list("asset", flat=True)

    @atomic
    def create(self, validated_data):
        pictures = validated_data.pop("pictures")
        stage = super(InspectionStageSerializer, self).create(validated_data)
        Assets.create_many(images=pictures, feature=stage, entity_type=AssetEntityType.InspectionStage)
        return stage

    @atomic
    def update(self, instance, validated_data):
        pictures = validated_data.pop("pictures")
        stage = super(InspectionStageSerializer, self).update(instance, validated_data)
        Assets.create_many(images=pictures, feature=stage, entity_type=AssetEntityType.InspectionStage)
        return stage


class InspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inspections
        fields = "__all__"

    def validate_inspector(self, attr: User):
        if attr.is_staff:
            return attr
        raise serializers.ValidationError("inspector must be an admin user")

    @atomic
    def create(self, validated_data):
        user_logged_in = self.context.get("request").user
        validated_data["inspection_assignor"] = user_logged_in
        inspection: Inspections = super(InspectionSerializer, self).create(validated_data)
        inspection.car.update_on_inspection_changes(inspection)
        return inspection

    @atomic
    def update(self, instance, validated_data):
        upd: Inspections = super(InspectionSerializer, self).update(instance, validated_data)
        upd.car.update_on_inspection_changes(upd)
        return upd
