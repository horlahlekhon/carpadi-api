import datetime
import logging
import threading

import requests
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.db import transaction
from django.db.models import Q
from django.http.response import Http404
from django.utils import timezone
from django_filters import rest_framework as filters
from fcm_django.models import FCMDevice
from requests import status_codes
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
from src.config.common import OTP_EXPIRY
from src.models.filters import NotificationsFilter
from src.models.models import User, UserTypes, Assets, Notifications, Otp, OtpStatus, TradeUnit, CarMerchant, \
    NotificationTypes, Waitlists
from src.models.permissions import IsUserOrReadOnly, IsAdmin
from src.models.serializers import (
    CreateUserSerializer,
    UserSerializer,
    PhoneVerificationSerializer,
    TokenObtainModSerializer,
    CarMerchantSerializer,
    OtpSerializer,
    AssetsSerializer,
    NotificationsSerializer,
    EmailVerificationSerializer,
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
        'verify_email': (IsAuthenticated,),
        'get_inspectors': (
            IsAuthenticated,
            IsAdmin,
        ),
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

    @action(detail=False, methods=['post', 'get'], url_path='verify-email', url_name='verify_email')
    def verify_email(self, request):
        try:
            if request.method == 'POST':
                email_ver = EmailVerificationSerializer(data=request.data)
                email_ver.context.update({"user": request.user})
                email_ver.is_valid(raise_exception=True)
                merchant = email_ver.save()
                merchant_ser = CarMerchantSerializer(instance=merchant)
                return Response(data=merchant_ser.data)
            else:
                user = request.user
                expiry = datetime.datetime.now() + datetime.timedelta(minutes=OTP_EXPIRY)
                ot = Otp.objects.create(otp="123456", expiry=expiry, user=user)
                context = dict(username=user.username, otp=ot.otp, user=user.id, users=[user])
                notify("USER_EMAIL_VERIFICATION", **context)
                return Response(data=dict(message="A Verification otp has been sent to the provided email."))
        except ValidationError as reason:
            return Response(reason.args[0], status=400)
        except Exception as reason:
            return Response({'error': str(reason)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='generate-otp', url_name='generate_otp')
    def generate_otp(self, instance):
        data = instance.data
        try:
            ser = OtpSerializer(data=data)
            ser.is_valid(raise_exception=True)
            ser.save()
            return Response(status=status.HTTP_200_OK)
        except ValidationError as reason:
            return Response(serializers.as_serializer_error(reason), status=400)
        except Exception as reason:
            return Response(reason.args, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='validate-otp', url_name='validate_otp')
    def validate_otp(self, instance):
        print(f"validating otp: {instance.data}")
        try:
            data = instance.data
            if not data:
                return Response(data={"error": "otp is a required field"}, status=status.HTTP_400_BAD_REQUEST)
            if data.get("email"):
                otp = Otp.objects.filter(otp=data.get("otp"), email=data.get("email"), status=OtpStatus.Pending.value).latest()
            elif phone := data.get("phone"):
                otp = Otp.objects.filter(otp=data.get("otp"), phone=phone, status=OtpStatus.Pending).latest()
            elif username := data.get("username"):
                user = User.objects.filter(username=username).first()
                otp = Otp.objects.filter(otp=data.get("otp"), user_id=user.id, status=OtpStatus.Pending).latest()
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
            seed_type = str(request.query_params.get('type', None)).lower()
            seed_data = PadiSeeder(request=request)
            # seed_data.seed()
            seed_func = seed_data.seed if seed_type != "banks" else seed_data.seed_banks()
            t = threading.Thread(target=seed_func)
            t.setDaemon(True)
            t.start()
            # unit: TradeUnit = TradeUnit.objects.filter(merchant__user_id="176c67aa-fa6b-4e21-b3eb-55839127a3b9").first()
            # notice = Notifications.objects.create(
            #     notice_type=NotificationTypes.TradeUnit,
            #     user=unit.merchant.user,
            #     message="Ok, Just take a chill, you will eventually come!!",
            #     is_read=False,
            #     entity_id=unit.id,
            # )

            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], url_path='notify', url_name='notify')
    def random_notify(self, request):
        token = request.data.get("token")
        fcm: FCMDevice = FCMDevice.objects.first()
        fcm.registration_id = token
        fcm.save(update_fields=["registration_id"])
        user = fcm.user
        unit = TradeUnit.objects.first()
        context = dict()
        context["entity"] = (str(unit.id),)
        context["message"] = "this is a dummy message"
        context["slot_quantity"] = unit.slots_quantity
        context["car"] = unit.trade.car.name
        context["total"] = unit.unit_value
        context["email"] = user.email
        context["user"] = str(user.id)
        context["users"] = [user]
        notify('TRADE_UNIT_PURCHASE', **context)
        return Response(200)

    @action(detail=False, methods=['get'], url_path='welcome', url_name='welcome_user')
    def welcome_user(self, request, *args, **kwargs):
        from src.notifications.services import notify

        user = User.objects.get(email="horlahlekhon@gmail.com")
        # notification = NOTIFICATIONS.get('new_user')
        notify = notify("WELCOME_USER", user=user.id, profile=user, users=[user])
        return Response(notify, status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='captcha', url_name='captcha')
    def check_captcha(self, request, *args, **kwargs):
        response = request.data.get("response")
        ip = request.data.get("ip")
        if ip and response:
            response = requests.post(url=settings.CAPTCHA_SITE_VERIFY_URL(response, settings.ADMIN_CAPTCHA_SHARED_SECRET, ip))
            result = response.json()
            if response.ok and result.get("status") is True:
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data=dict(error=dict(data="We could not verify the captcha response", response=result)),
                )
        else:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data=dict(error="IP and the captcha response are " "required fields")
            )

    @action(detail=False, methods=['post'], url_path='join-waitlist', url_name='join_waitlist')
    def join_waitlist(self, request, *args, **kwargs):
        if not (waitlist := request.query_params.get("email")):
            return Response(status=status.HTTP_400_BAD_REQUEST, data=dict(error="Email is required as query parametre"))
        if exist := Waitlists.objects.filter(email=waitlist).first():
            return Response(status=status.HTTP_200_OK)
        else:
            Waitlists.objects.create(email=waitlist)


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
