from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView

from src.carpadi_api.serializers import TransactionPinSerializers
from src.models.models import User, TransactionPinStatus, TransactionPin
from src.models.permissions import IsUserOrReadOnly
from src.models.serializers import CreateUserSerializer, UserSerializer, PhoneVerificationSerializer
from rest_framework.serializers import ValidationError


class UserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Creates, Updates and Retrieves - User Accounts
    """

    queryset = User.objects.all()
    serializers = {'default': UserSerializer, 'create': CreateUserSerializer}
    permissions = {'default': (IsUserOrReadOnly,), 'create': (AllowAny,), 'verify_phone': (AllowAny,)}

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers['default'])

    def get_permissions(self):
        self.permission_classes = self.permissions.get(self.action, self.permissions['default'])
        return super().get_permissions()

    @action(detail=False, methods=['get'], url_path='me', url_name='me')
    def get_user_data(self, instance):
        try:
            return Response(UserSerializer(self.request.user, context={'request': self.request}).data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': 'Wrong auth token' + e}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='verify-phone', url_name='verify_phone')
    def verify_phone(self, instance):
        try:
            ser = PhoneVerificationSerializer(data=instance.data)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(status=status.HTTP_200_OK)
        except ValidationError as reason:
            return Response(reason.args[0], status=400)
        except Exception as reason:
            return Response({'error': str(reason)}, status=status.HTTP_400_BAD_REQUEST)
