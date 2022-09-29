import logging
import threading

from django.core.mail import EmailMultiAlternatives, send_mail
from django.db import transaction
from django.db.models import Q
from django.http.response import Http404
from django.utils import timezone
from django_filters import rest_framework as filters
from rest_framework import serializers
from rest_framework import status
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.exceptions import NotAcceptable
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.serializers import ValidationError
from rest_framework_simplejwt.views import TokenViewBase

from src.common.seeder import PadiSeeder
from src.models.filters import NotificationsFilter
from src.models.models import User, UserTypes, Assets, Notifications, Otp, OtpStatus, TradeUnit, CarMerchant, NotificationTypes
from src.models.permissions import IsUserOrReadOnly
from src.models.serializers import (
    CreateUserSerializer,
    UserSerializer,
    PhoneVerificationSerializer,
    TokenObtainModSerializer,
    CarMerchantSerializer,
    OtpSerializer,
    AssetsSerializer,
    NotificationsSerializer,
)
from src.notifications.services import notify

logger = logging.getLogger(__name__)


class UserViewSet(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Creates, Updates and Retrieves - User Accounts
    """

    queryset = User.objects.all()
    serializers = {'default': UserSerializer, 'create': CreateUserSerializer}
    permissions = {
        'default': (IsUserOrReadOnly,),
        'create': (AllowAny,),
        'verify_phone': (AllowAny,),
        'seed': (AllowAny,),
    }

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers['default'])

    def get_permissions(self):
        self.permission_classes = self.permissions.get(self.action, self.permissions['default'])
        return super().get_permissions()

    @action(detail=False, methods=['get'], url_path='me', url_name='me')
    def get_user_data(self, instance):
        try:
            user = self.request.user
            if user.user_type == UserTypes.CarMerchant and user.merchant:
                data = CarMerchantSerializer(instance=user.merchant).data
            else:
                data = UserSerializer(self.request.user, context={'request': self.request}).data

            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': f'Wrong auth token{e}'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='verify-phone', url_name='verify_phone')
    def verify_phone(self, instance):
        try:
            ser = PhoneVerificationSerializer(data=instance.data)
            ser.is_valid(raise_exception=True)
            user = ser.save()
            return Response(ser.get_tokens(user), status=status.HTTP_200_OK)
        except ValidationError as reason:
            return Response(reason.args[0], status=400)
        except Exception as reason:
            return Response({'error': str(reason)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='generate-otp', url_name='generate_otp')
    def generate_otp(self, instance):
        try:
            ser = OtpSerializer(data=instance.data)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(status=status.HTTP_200_OK)
        except ValidationError as reason:

            return Response(serializers.as_serializer_error(reason), status=400)
        except Exception as reason:
            return Response(reason.args, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='validate-otp', url_name='validate_otp')
    def validate_otp(self, instance):
        try:
            data = instance.data.get("otp")
            if not data:
                return Response(data={"error": "otp is a required field"}, status=status.HTTP_400_BAD_REQUEST)
            user = self.get_object()
            otp = Otp.objects.filter(otp=data, user=user, status=OtpStatus.Pending).latest()
            if otp.expiry < timezone.now():
                return Response(data={"error": "Otp has expired"}, status=status.HTTP_400_BAD_REQUEST)
            otp.status = OtpStatus.Verified
            otp.save()
            return Response(data={"status": "otp is valid"}, status=status.HTTP_200_OK)
        except Otp.DoesNotExist:
            return Response(data={"error": "Otp does not exist"}, status=status.HTTP_400_BAD_REQUEST)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_object(self):
        user = self.request.user
        if user.is_anonymous or not user.is_authenticated or not user.is_active:
            raise Http404('No user matches the given query.')
        if user.is_superuser or user.is_staff:
            raise NotAcceptable("Admin user cannot login on the merchant app")
        return user

    @action(detail=False, methods=['patch'], url_path='update', url_name='patch_user')
    def patch_user(self, request, *args, **kwargs):
        kwargs["partial"] = True
        return super(UserViewSet, self).update(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='update-password', url_name='update_password')
    def update_password(self, request, *args, **kwargs):
        data: dict = request.data
        if data.get("new_password") and data.get("old_password"):
            user: User = self.request.user
            if user.is_active and user.check_password(data.get("old_password")) and user.is_authenticated:
                user.set_password(data.get("new_password"))
                user.save(update_fields=["password"])
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST, data=dict(error="Invalid user cannot update password"))
        return Response(status=status.HTTP_400_BAD_REQUEST, data=dict(error="old_password and new_password must be supplied"))

    @action(detail=False, methods=['post'], url_path='seed', url_name='seed')
    def seed(self, request, *args, **kwargs):
        """
        Seed the database with some data
        """
        try:
            # seed_type = str(request.query_params.get('type', None)).lower()
            # seed_data = PadiSeeder(request=request)
            # # seed_data.seed()
            # seed_func = seed_data.seed if seed_type != "banks" else seed_data.seed_banks()
            # t = threading.Thread(target=seed_func)
            # t.setDaemon(True)
            # t.start()
            unit: TradeUnit = TradeUnit.objects.filter(merchant__user_id="c9eee4be-eea2-4672-88b5-705ac5990827").first()
            notice = Notifications.objects.create(
                notice_type=NotificationTypes.NewTrade,
                user=unit.merchant.user,
                message="This is a dummy message dont take shit serious abeg",
                is_read=False,
                entity_id=unit.id,
            )

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TokenObtainPairViewMod(TokenViewBase):
    """
    Takes a set of user credentials and returns an access and refresh JSON web
    token pair to prove the authentication of those credentials.
    """

    serializer_class = TokenObtainModSerializer


class AssetsViewSet(viewsets.ModelViewSet):
    """
    Retrieves and Updates - User Pictures
    """

    queryset = Assets.objects.all()
    serializer_class = AssetsSerializer
    permission_classes = (IsAuthenticated,)

    def get_object(self):
        user = self.request.user
        if user.is_anonymous or not user.is_authenticated or not user.is_active:
            raise Http404('No user matches the given query.')
        return user

    # @action(detail=False, methods=['patch'], url_path='update', url_name='patch_user')
    # def patch_user(self, request, *args, **kwargs):
    #     return super(PicturesViewSet, self).update(request, *args, **kwargs)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Retrieves and Updates - User notifications
    """

    queryset = Notifications.objects.all()
    serializer_class = NotificationsSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = NotificationsFilter

    def get_queryset(self):
        return super(NotificationViewSet, self).get_queryset().filter(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='read', url_name='read')
    def mark_as_read(self, request, *args, **kwargs):
        """
        Mark a notification as read
        """
        notice_id = request.query_params.get("id")
        read = request.query_params.get("read")
        if str(read) not in ["True", "False"]:
            return Response(
                {'error': "you need to specify `read` query parametre as a valid boolean i.e `True` or `False`"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        read_option = eval(read)
        if read_all := request.query_params.get("all"):
            return self.mark_all_as_read_or_unread(read=read_option)
        try:
            notifications = Notifications.objects.filter(user=request.user, id=notice_id)
            if notifications.exists():
                notifications.update(is_read=read_option)
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def mark_all_as_read_or_unread(self, read: bool):
        """
        Mark all notifications as read
        """
        try:
            notifications = Notifications.objects.filter(user=self.request.user).filter(~Q(is_read=read))
            notifications.update(is_read=read)
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
