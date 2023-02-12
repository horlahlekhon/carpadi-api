import datetime

from django.conf import settings
from django.db.models import Sum, Avg
from django.db.transaction import atomic
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ErrorDetail

from src.models.models import InspectionStage, Inspections, User, CarStates, Assets, AssetEntityType, Stages
from src.models.serializers import AssetsSerializer


class InspectionPartSerializer(serializers.ModelSerializer):
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
        stage = super(InspectionPartSerializer, self).create(validated_data)
        Assets.create_many(images=pictures, feature=stage, entity_type=AssetEntityType.InspectionPart)
        return stage

    @atomic
    def update(self, instance, validated_data):
        pictures = validated_data.pop("pictures")
        stage: InspectionStage = super(InspectionPartSerializer, self).update(instance, validated_data)
        Assets.create_many(images=pictures, feature=stage, entity_type=AssetEntityType.InspectionPart)
        if validated_data.get("stage_name") == Stages.Completed:
            inspection = stage.inspection
            parts = InspectionStage.objects.filter(inspection=inspection)
            if parts.count() < settings.INSPECTION_PARTS_COUNT:
                raise serializers.ValidationError(
                    detail=ErrorDetail("Inspection parts are not complete, please recheck"), code=400
                )
            inspection.inspection_score = (parts.aggregate(avg=Avg("score")).get("avg") or 0) / 100
            inspection.save(update_fields=["inspection_score"])
        return stage


class InspectorSerializerField(serializers.RelatedField):
    def to_representation(self, value: User):
        return dict(username=value.username, id=value.id, phone=value.phone, email=value.email)

    def to_internal_value(self, data):
        try:
            return self.queryset.get(pk=data)
        except User.DoesNotExist as e:
            raise serializers.ValidationError(f"Inspector with id {data} does not exist") from e


class InspectionSerializer(serializers.ModelSerializer):
    inspector = InspectorSerializerField(required=True, queryset=User.objects.filter(is_staff=True, is_active=True))
    pictures = serializers.ListField(child=serializers.URLField(), default=[], write_only=True)

    class Meta:
        model = Inspections
        fields = "__all__"

    def validate_inspection_date(self, attr: datetime.datetime):
        now = timezone.now()
        if attr < now:
            raise serializers.ValidationError("Inspection date must be in the future")
        return attr

    @atomic
    def create(self, validated_data):
        user_logged_in = self.context.get("request").user
        validated_data["inspection_assignor"] = user_logged_in
        pictures = validated_data.pop("pictures")
        inspection: Inspections = super(InspectionSerializer, self).create(validated_data)
        Assets.create_many(images=pictures, feature=inspection, entity_type=AssetEntityType.Inspection)
        inspection.car.update_on_inspection_changes(inspection)
        return inspection

    @atomic
    def update(self, instance: Inspections, validated_data):
        if not instance.car.is_editable():
            raise serializers.ValidationError("This car is beyond the scope of modification")
        pictures = validated_data.pop("pictures") if validated_data.get("pictures") else []
        Assets.create_many(images=pictures, feature=instance, entity_type=AssetEntityType.Inspection)
        upd: Inspections = super(InspectionSerializer, self).update(instance, validated_data)
        upd.car.update_on_inspection_changes(upd)
        return upd
