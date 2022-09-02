from django.db.transaction import atomic
from rest_framework import serializers

from src.models.models import InspectionStage, Inspections, User, CarStates


class InspectionStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionStage
        fields = "__all__"


class InspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inspections
        fields = "__all__"
        # extra_kwargs = {}

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
        inspection = super(InspectionSerializer, self).update(instance, validated_data)
        return inspection
