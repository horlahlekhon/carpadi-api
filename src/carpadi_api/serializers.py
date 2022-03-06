from email.policy import default
from celery import uuid
from rest_framework import serializers

# from .models import Transaction
from ..models.models import CarMerchant


class SocialSerializer(serializers.Serializer):
    """
    Serializer which accepts an OAuth2 access token.
    """

    access_token = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )


class CarMerchantSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarMerchant
        fields = "__all__"
