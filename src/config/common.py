import os
from datetime import timedelta
from os.path import join

import dotenv
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

APP_ENV = os.getenv("APP_ENV", default="test")
TESTING = APP_ENV.lower() == "test"
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# if not TESTING:
#     dotenv.read_dotenv(ROOT_DIR)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SITE_URL = os.getenv('SITE_URL', 'http://localhost:8000')

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'jet.dashboard',
    'jet',
    'django.contrib.admin',
    # Third party apps
    'rest_framework',  # utilities for rest apis
    'rest_framework.authtoken',  # token authentication
    'django_filters',  # for filtering rest endpoints
    'django_rest_passwordreset',  # for reset password endpoints
    'drf_yasg',  # swagger api
    'easy_thumbnails',  # asset lib
    'social_django',  # social login
    'corsheaders',  # cors handling
    'django_inlinecss',  # inline css in templates
    'django_summernote',  # text editor
    'django_celery_beat',  # task scheduler
    'djmoney',  # money object
    'health_check',
    'health_check.db',  # stock Django health checkers
    'health_check.cache',
    'health_check.storage',
    'health_check.contrib.migrations',
    'health_check.contrib.celery_ping',  # requires celery
    # Your apps
    'src.models',
    'src.notifications',
    'src.social',
    'src.files',
    'src.common',
    'src.carpadi_admin',
    'src.carpadi_api',
    'django_extensions',
    # Third party optional apps
    # app must be placed somewhere after all the apps that are going to be generating activities
    # 'actstream',                  # activity stream
    "fcm_django",
)

# https://docs.djangoproject.com/en/2.0/topics/http/middleware/
MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'social_django.middleware.SocialAuthExceptionMiddleware',
)

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '#p7&kxb7y^yq8ahfw5%$xh=f8=&1y*5+a5($8w_f7kw!-qig(j')
ALLOWED_HOSTS = ["*"]
ROOT_URLCONF = 'src.urls'
WSGI_APPLICATION = 'src.wsgi.application'

# Email

EMAIL_HOST = "in-v3.mailjet.com"
EMAIL_PORT = 587
EMAIL_FROM = "admin@carpadi.com"
EMAIL_HOST_USER = "effd16db611dab2e8a9d7515e6caf7d9"
EMAIL_HOST_PASSWORD = "1324403edf626ee9e5d9e0949d01d037"  # 44c3b9a23917b98d50913d884c940782
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend' if TESTING else "django.core.mail.backends.smtp.EmailBackend"

# EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
# EMAIL_HOST = os.getenv('EMAIL_HOST', default="in-v3.mailjet.com")
# EMAIL_PORT = os.getenv('EMAIL_PORT', default=587)
# EMAIL_FROM = os.getenv('EMAIL_FROM', default="horlahlekhon@gmail.com")
# EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', default="effd16db611dab2e8a9d7515e6caf7d9")
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', default="462488cdc685193b657ed4dafbf5633e")
EMAIL_USE_TLS = True

# Celery
BROKER_URL = os.getenv('BROKER_URL', 'redis://localhost:6379')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379')

ADMINS = ()

# Sentry
sentry_sdk.init(dsn=os.getenv('SENTRY_DSN', ''), integrations=[DjangoIntegration()])

# CORS
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# CELERY
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Postgres
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', default="postgres"),
        'USER': os.getenv('DB_USER', default="postgres"),
        'PASSWORD': os.getenv('DB_PASSWORD', default="password"),
        'HOST': os.getenv('DB_HOST', default="localhost"),
        'PORT': os.getenv('DB_PORT', default=5432),
    }
}

# General
APPEND_SLASH = True
TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'
# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False
USE_L10N = True
USE_TZ = True
LOGIN_REDIRECT_URL = '/'

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATICFILES_DIRS = []
STATIC_URL = '/static/'
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Media files
MEDIA_ROOT = join(os.path.dirname(BASE_DIR), 'media')
MEDIA_URL = '/media/'

# Headers
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': STATICFILES_DIRS,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

# Set DEBUG to False as a default for safety
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = os.getenv('DJANGO_DEBUG', False) == 'True'

# Password Validation
# https://docs.djangoproject.com/en/2.0/topics/auth/passwords/#module-django.contrib.auth.password_validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[%(server_time)s] %(message)s',
        },
        'verbose': {'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'},
        'simple': {'format': '%(levelname)s %(message)s'},
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {'level': 'DEBUG', 'class': 'logging.StreamHandler'},
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
        'mail_admins': {'level': 'ERROR', 'class': 'django.utils.log.AdminEmailHandler'},
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'propagate': True,
            'level': 'INFO',
        },
        'django.server': {
            'handlers': ['django.server'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {'handlers': ['console'], 'level': 'INFO'},
    },
}

# Custom user app
AUTH_USER_MODEL = 'models.User'

# Social login
AUTHENTICATION_BACKENDS = (
    'social_core.backends.facebook.FacebookOAuth2',
    'social_core.backends.twitter.TwitterOAuth',
    'src.models.backends.EmailOrUsernameOrPhoneModelBackend',
    'django.contrib.auth.backends.ModelBackend',
)
for key in ['GOOGLE_OAUTH2_KEY', 'GOOGLE_OAUTH2_SECRET', 'FACEBOOK_KEY', 'FACEBOOK_SECRET', 'TWITTER_KEY', 'TWITTER_SECRET']:
    exec("SOCIAL_AUTH_{key} = os.environ.get('{key}', '')".format(key=key))

# FB
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {'fields': 'id, name, email'}
SOCIAL_AUTH_FACEBOOK_API_VERSION = '5.0'

# Twitter
SOCIAL_AUTH_TWITTER_SCOPE = ['email']

SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ['email', 'profile']
SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ['username', 'first_name', 'email']
# If this is not set, PSA constructs a plausible username from the first portion of the
# user email, plus some random disambiguation characters if necessary.
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

SOCIAL_AUTH_TWITTER_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    # 'social_core.pipeline.social_auth.social_user',
    'src.common.social_pipeline.user.social_user',
    'social_core.pipeline.user.get_username',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.user.create_user',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
    'src.common.social_pipeline.user.login_user',  # login correct user at the end
)

SOCIAL_AUTH_LOGIN_REDIRECT_URL = '/complete/twitter/'

THUMBNAIL_ALIASES = {
    'src.models': {
        'thumbnail': {'size': (100, 100), 'crop': True},
        'medium_square_crop': {'size': (400, 400), 'crop': True},
        'small_square_crop': {'size': (50, 50), 'crop': True},
    },
}

# Django Rest Framework

# Django Rest Framework
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'PAGE_SIZE': int(os.getenv('DJANGO_PAGINATION_LIMIT', 18)),
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%S.%fZ',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
        'rest_framework.throttling.ScopedRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {'anon': '100/second', 'user': '1000/second', 'subscribe': '60/minute'},
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}

# JWT configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60 * 10),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': False,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUDIENCE': None,
    'ISSUER': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# summernote configuration
SUMMERNOTE_CONFIG = {
    'summernote': {
        'toolbar': [
            ['style', ['style']],
            ['font', ['bold', 'underline', 'clear']],
            ['fontname', ['fontname']],
            ['color', ['color']],
            ['para', ['ul', 'ol', 'paragraph', 'smallTagButton']],
            ['table', ['table']],
            ['insert', ['link', 'video']],
            ['view', ['fullscreen', 'codeview', 'help']],
        ]
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'

OTP_EXPIRY = 30
DJANGO_REST_PASSWORDRESET_TOKEN_CONFIG = {
    "CLASS": "django_rest_passwordreset.tokens.RandomNumberTokenGenerator",
    "OPTIONS": {"min_number": 100000, "max_number": 999999},
}

FLW_PUBLIC_KEY = os.getenv('FLUTTER_WAVE_PUBLIC_KEY', '')
FLW_SECRET_KEY = os.getenv('FLUTTER_WAVE_SECRET_KEY', '')
FLW_REDIRECT_URL = os.getenv(
    'PAYMENT_REDIRECT_URL', 'https://a670-41-217-100-193.ngrok.io/api/v1/merchants/transactions/verify-transaction/'
)
FLW_PAYMENT_URL = os.getenv('PAYMENT_URL', "https://api.flutterwave.com/v3/payments")
FLW_PAYMENT_VERIFY_URL = "https://api.flutterwave.com/v3/transactions/{}/verify".format
FLW_GET_TRANSFER_URL = "https://api.flutterwave.com/v3/transfers/{}".format
FLW_ACCOUNT_VERIFY_URL = "https://api.flutterwave.com/v3/accounts/resolve"
LOG_DIRECTORY = os.getenv('LOG_DIRECTORY', 'logs')

FLW_WITHDRAW_URL = os.getenv('FLW_WITHDRAW_URL', "https://api.flutterwave.com/v3/transfers")

# import cloudinary
#
# cloudinary.config(
#     cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME', ''),
#     api_key=os.getenv('CLOUDINARY_API_KEY', ''),
#     api_secret=os.getenv('CLOUDINARY_API_SECRET', ''),
# )

CARMD_PARTNER_TOKEN = os.getenv('CARMD_PARTNER_TOKEN', '')
CARMD_APIKEY = os.getenv('CARMD_APIKEY', '')
CARMD_VIN_CHECK = "http://api.carmd.com/v3.0/decode?vin={}".format

from firebase_admin import initialize_app

FIREBASE_APP = initialize_app()

FCM_DJANGO_SETTINGS = {
    # default: _('FCM Django')
    "APP_VERBOSE_NAME": "Carpadi",
    # true if you want to have only one active device per registered user at a time
    # default: False
    "ONE_DEVICE_PER_USER": False,
    # devices to which notifications cannot be sent,
    # are deleted upon receiving error response from FCM
    # default: False
    "DELETE_INACTIVE_DEVICES": False,
    # Transform create of an existing Device (based on registration id) into
    # an update. See the section
    # "Update of device with duplicate registration ID" for more details.
    "UPDATE_ON_DUPLICATE_REG_ID": True,
}

from celery.schedules import crontab

# from src.common.tasks import check_cars_with_completed_documentations

CELERY_BEAT_SCHEDULE = {
    "sample_task": {
        "task": "src.common.tasks.check_cars_with_completed_documentations",
        "schedule": crontab(minute="*/1"),
    },
}

BULK_SMS_API_KEY = "fwFidxGn1ATSvjvUoaEO85DYk1rKIpTQARfebvG4GNi7QvJyicRupmF6A44a"
BULK_SMS_API_BASE_URL = "https://www.bulksmsnigeria.com/api/v1/sms/create"
MIN_SLOT_ALLOWED = 4
MIN_CAR_PICTURES_FOR_TRADE = 5
