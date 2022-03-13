from dataclasses import field
from pyexpat import model
from rest_framework import serializers

from src.models.models import Wallet

class SocialSerializer(serializers.Serializer):
    """
    Serializer which accepts an OAuth2 access token.
    """

    access_token = serializers.CharField(
        allow_blank=False,
        trim_whitespace=True,
    )

class WalletSerializerAdmin(serializers.Serializer):
    """
    Wallet Serializer for an admin 
    """

    class Meta:
        model = Wallet
        fields = "__all__"
        read_only_fields = ('created', 'modified', 'id', 'merchant', 'balance')
