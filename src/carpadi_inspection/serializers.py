from django.db.transaction import atomic
from rest_framework import serializers, exceptions

from src.models.models import InspectionStage, Inspections


class InspectionStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionStage
        fields = "__all__"


class InspectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Inspections
        fields = "__all__"

    @atomic
    def create(self, validated_data):
        user_logged_in = self.context.get("request")
        raise Exception("boom")
