from rest_framework import serializers

from src.models.models import User, Transactions, Wallet
from src.common.serializers import ThumbnailerJSONSerializer


class UserSerializer(serializers.ModelSerializer):
    profile_picture = ThumbnailerJSONSerializer(required=False, allow_null=True, alias_target='src.models')

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'profile_picture',
        )
        read_only_fields = ('username',)


class CreateUserSerializer(serializers.ModelSerializer):
    profile_picture = ThumbnailerJSONSerializer(required=False, allow_null=True, alias_target='src.models')
    tokens = serializers.SerializerMethodField()

    def get_tokens(self, user):
        return user.get_tokens()

    def create(self, validated_data):
        # call create_user on user object. Without this
        # the password will be stored in plain text.
        user = User.objects.create_user(**validated_data)
        return user

    class Meta:
        model = User
        fields = (
            'id',
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
            'tokens',
            'profile_picture',
        )
        read_only_fields = ('tokens',)
        extra_kwargs = {'password': {'write_only': True}}


class CarBrandSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "name", "model", "created")



# wallet serialer
class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = "__all__"
        read_only_fields = ('created', 'id', 'merchant')


# transaction  serializer
class TransactionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transactions
        fields = ('id', 'created', 'wallet', 'amount')
        read_only_fields = ('id', 'created', 'wallet','amount')


