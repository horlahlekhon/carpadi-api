from attr import fields
from charset_normalizer import models
from rest_framework import serializers

from src.models.models import User, CarBrand, Car
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
        model = CarBrand
        fields = (
            'id',
            'name',
            'year',
            'model',
        )


class CreateCarBrandSerializer(serializers.ModelSerializer):
    
    def create(self, validated_data):
        carBrand = CarBrand.objects.create(**validated_data)
        return carBrand

    class Meta:
        fields = (
            'id',
            'name',
            'year',
            'model',
        )

    
class CarSerializer(serializers.ModelSerializer):

    class Meta:
        model = Car
        fields = (
            'id',
            'type',
            'brand',
            'status',
            'vin',
            'costOfCar',
            'projectedCarPrice',
            'sharesAvailable',
            'sharesPurchased',
        )

class CreateCarSerializer(serializers.ModelSerializer):

    def create(self, validated_data):

        car = Car.objects.create(**validated_data)
        return car

    class Meta:
        fields = (
            'id',
            'type',
            'brand',
            'status',
            'vin',
            'costOfCar',
            'projectedCarPrice',
            'sharesAvailable',
            'sharesPurchased',
        )