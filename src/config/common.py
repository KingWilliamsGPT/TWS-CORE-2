import os
import sentry_sdk
import sys
import dotenv

from datetime import timedelta
from sentry_sdk.integrations.django import DjangoIntegration
from os.path import join

TESTING = sys.argv[1:2] == ["test"]
RUNNING_ON_SERVER = os.getenv("RUNNING_ON_SERVER", "False") == "True"

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if not TESTING:
    ENV_FILE = ROOT_DIR.rstrip("/") + "/.env"
    if not os.path.exists(ENV_FILE):
        with open(ENV_FILE, "w"):
            pass
    # dotenv.read_dotenv(ENV_FILE)
    getattr(
        dotenv,
        "read_dotenv",
        getattr(
            dotenv,
            "load_dotenv",
            lambda *args: print(
                "DOT ENV NOT LOADED. The dotenv module is not installed",
                file=sys.stderr,
            ),
        ),
    )(ENV_FILE)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREFERRED_DVA_BANK = "paystack-titan"  # OR wema-bank

# SITE_URL = os.getenv('SITE_URL', 'http://localhost:8000')
SITE_NAME = os.getenv("SITE_NAME", "zeefas")
SITE_URL = "https://api.zeefas.com/"
FRONTEND_SERVER = "https://zeefas.com/"  # os.getenv('FRONTEND_SERVER', 'https://zeefas.com/')
DEVELOPER_EMAIL = "williamusanga23@gmail.com"

DEVELOPER_EMAILS = [
    DEVELOPER_EMAIL,
]

FRONTEND_DOMAIN = os.getenv("FRONTEND_DOMAIN", "https://zeefas.com")

DISABLE_DVA_CHECKS = os.getenv("DISABLE_DVA_CHECKS", "False").lower() == "true"
WHATSAPP_INVITE_LINK = "https://chat.whatsapp.com/JQU7KiHMKPs3Km6yuDhtWR"

INSTALLED_APPS = (
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 'jet',   # outdated bro
    "django.contrib.admin",
    # Third party apps
    "rest_framework",  # utilities for rest apis
    "rest_framework.authtoken",  # token authentication
    "django_extensions",
    "django_filters",  # for filtering rest endpoints
    "django_rest_passwordreset",  # for reset password endpoints
    # "drf_yasg",  # swagger api
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "easy_thumbnails",  # image lib
    "social_django",  # social login
    "corsheaders",  # cors handling
    "django_inlinecss",  # inline css in templates
    "django_summernote",  # text editor
    "django_celery_beat",  # task scheduler
    "health_check",
    "health_check.db",  # stock Django health checkers
    "health_check.cache",
    "health_check.storage",
    "health_check.contrib.migrations",
    "health_check.contrib.celery_ping",  # requires celery
    "countries_plus",
    "cities_light",
    # Your apps
    "src.notifications",
    "src.users",
    "src.social",
    "src.files",
    "src.common",
    "src.paystack_app",
    "src.wallet",
    "src.bank_account_app",
    "src.products",
    "src.chats",
    "src.orders",
    # Third party optional apps
    # app must be placed somewhere after all the apps that are going to be generating activities
    "actstream",
)

# https://docs.djangoproject.com/en/2.0/topics/http/middleware/
MIDDLEWARE = (
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "countries_plus.middleware.AddRequestCountryMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "social_django.middleware.SocialAuthExceptionMiddleware",
)


REDIS_DOMAIN_DEV = os.getenv("REDIS_DOMAIN_DEV", "127.0.0.1")
REDIS_DOMAIN_PROD = os.getenv("REDIS_DOMAIN_PROD", "redis")

if RUNNING_ON_SERVER:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [(REDIS_DOMAIN_PROD, 6379)],
            },
        },
    }

    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://{REDIS_DOMAIN_PROD}:6379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }
else:
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [(REDIS_DOMAIN_DEV, 6379)],
            },
        },
    }

    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://{REDIS_DOMAIN_DEV}:6379/1",
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            }
        }
    }


COUNTRIES_PLUS_COUNTRY_HEADER = (
    "HTTP_CF_COUNTRY"  # Cloudflare’s header for country code
)
COUNTRIES_PLUS_DEFAULT_ISO = "NG"

SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY", "#p7&kxb7y^yq8ahfw5%$xh=f8=&1y*5+a5($8w_f7kw!-qig(j"
)
ALLOWED_HOSTS = ["*"]
# ['127.0.0.1', '.vercel.app']
ROOT_URLCONF = "src.urls"
WSGI_APPLICATION = "src.wsgi.application"

# EBAY
MAX_EBAY_CALL_RETRIES = 5
SUPPRESS_EBAY_ERRORS = True
DEFAULT_FEEDBACK = "."  #'Successfull Order.' # when the user wants to send feedback but fails to give a feedback message


# Email
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "localhost")
EMAIL_PORT = os.getenv("EMAIL_PORT", 1025)
# EMAIL_FROM = os.getenv('EMAIL_FROM', 'noreply@somehost.local')
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")

# Elastic Email
ELASTIC_EMAIL_NAME = os.getenv("ELASTIC_EMAIL_NAME", "AutoVerify")
ELASTIC_EMAIL = os.getenv("ELASTIC_EMAIL", "noreply@bloombyte.dev")
ELASTIC_EMAIL_KEY = os.getenv("ELASTIC_EMAIL_KEY")

# Zepto Mail
ZEPTO_EMAIL_NAME = os.getenv("ZEPTO_EMAIL_NAME", "AutoVerify")
ZEPTO_EMAIL = os.getenv("ZEPTO_EMAIL", "noreply@bloombyte.dev")
ZEPTO_API_KEY = os.getenv("ZEPTO_API_KEY")

# Stripe
STRIPE_DEBUG = os.getenv("STRIPE_DEBUG", "True") == "True"
STRIPE_TEST_PUBLISHABLE_KEY = os.getenv("STRIPE_TEST_PUBLISHABLE_KEY", "")
STRIPE_TEST_SECRET_KEY = os.getenv("STRIPE_TEST_SECRET_KEY", "")
STRIPE_PROD_PUBLISHABLE_KEY = os.getenv("STRIPE_PROD_PUBLISHABLE_KEY", "")
STRIPE_PROD_SECRET_KEY = os.getenv("STRIPE_PROD_SECRET_KEY", "")
# - WEBHOOK
STRIPE_WEBHOOK_KEY = os.getenv(
    "STRIPE_WEBHOOK_KEY",
)

# Translation: This object was programmatically generated with provided access, please do not delete it. As it may cause unexpected errors in the software
STRIPE_OBJECT_DELETE_WARNING = "Ten obiekt został wygenerowany programowo przy użyciu udostępnionego dostępu, proszę go nie usuwać Może to spowodować nieoczekiwane błędy w oprogramowaniu"

if STRIPE_DEBUG:
    STRIPE_PUBLISHABLE_KEY = STRIPE_TEST_PUBLISHABLE_KEY
    STRIPE_SECRET_KEY = STRIPE_TEST_SECRET_KEY
else:
    STRIPE_PUBLISHABLE_KEY = STRIPE_PROD_PUBLISHABLE_KEY
    STRIPE_SECRET_KEY = STRIPE_PROD_SECRET_KEY

CHECKOUT_SUCCESS_URL = os.getenv("CHECKOUT_SUCCESS_URL")


# Ecart

ECART_API_ID = os.getenv("ECART_API_ID", "")


# Celery
BROKER_URL = os.getenv("BROKER_URL", "redis://redis:6379")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379")

ADMINS = ()

# Sentry
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN", ""), integrations=[DjangoIntegration()])

# CORS
CORS_ORIGIN_ALLOW_ALL = True
CORS_ALLOW_CREDENTIALS = True

# CORS_ALLOWED_ORIGINS = [
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
#     "https://be.autoverify.bloombyte.dev/",
# ]


# CELERY
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"

# Postgres
# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql',
#         'NAME': os.getenv('DB_NAME'),
#         'USER': os.getenv('DB_USER'),
#         'PASSWORD': os.getenv('DB_PASSWORD'),
#         'HOST': os.getenv('DB_HOST', 'db'),
#         'PORT': os.getenv('DB_PORT'),
#     }
# }

alt_backend = {
    "postgres": "django.db.backends.postgresql",
    "mysql": "django.db.backends.mysql",
}

USE_DEFAULT_BACKEND = os.getenv("USE_DEFAULT_BACKEND") == "True"
ALT_BACKEND = str(os.getenv("ALT_BACKEND")).lower()


class ImproperlyConfigured(Exception):
    pass


try:
    db_backend = alt_backend[ALT_BACKEND]
except KeyError:
    raise ImproperlyConfigured(
        f"ALT_BACKEND={ALT_BACKEND} in .env change it to either postgres or mysql."
    )

if USE_DEFAULT_BACKEND:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
        }
    }
else:
    OPTIONS = {
        "sslmode": os.getenv("DB_SSL_MODE"),
        "channel_binding": os.getenv("DB_CHANNEL_BINDING"),
    }
    if not OPTIONS["sslmode"] and not OPTIONS["channel_binding"]:
        OPTIONS = {}
    DATABASES = {
        "default": {
            "ENGINE": db_backend,
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USER"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST", "db"),
            "PORT": os.getenv("DB_PORT"),
            # 'CONN_MAX_AGE': 300, # this was a bad idea
            "OPTIONS": OPTIONS,
        }
    }


# General
APPEND_SLASH = True
TIME_ZONE = "UTC"
LANGUAGE_CODE = "en-us"
# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False
USE_L10N = True
USE_TZ = True
LOGIN_REDIRECT_URL = "/"

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.0/howto/static-files/
STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")  # Where files are collected
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),  # Your additional static directories
]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
# STATICFILES_FINDERS = (
#     'django.contrib.staticfiles.finders.FileSystemFinder',
#     'django.contrib.staticfiles.finders.AppDirectoriesFinder',
# )

# Media files
MEDIA_ROOT = join(os.path.dirname(BASE_DIR), "media")
MEDIA_URL = "/media/"

# Headers
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# I have given up hope on session for this project
# True in prod
# SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', 'True') == 'True'
# CSRF_COOKIE_SECURE = True
# SESSION_COOKIE_DOMAIN = 'be.autoverify.bloombyte.dev'
# SESSION_ENGINE = 'django.contrib.sessions.backends.db'
# SESSION_SAVE_EVERY_REQUEST = True
# SESSION_EXPIRE_AT_BROWSER_CLOSE = False

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": STATICFILES_DIRS,
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
            ],
        },
    },
]

# Set DEBUG to False as a default for safety
# https://docs.djangoproject.com/en/dev/ref/settings/#debug
DEBUG = os.getenv("DJANGO_DEBUG", "False") == "True"

# Password Validation
# https://docs.djangoproject.com/en/2.0/topics/auth/passwords/#module-django.contrib.auth.password_validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "django.server": {
            "()": "django.utils.log.ServerFormatter",
            "format": "[%(server_time)s] %(message)s",
        },
        "verbose": {
            "format": "%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s"
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "django.server": {
            "level": "INFO",
            "class": "logging.StreamHandler",
            "formatter": "django.server",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            # "filters": ["require_debug_true"],   # only logs if DEBUG=True
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "src.config.logging.CustomAdminEmailHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "root": {  # to prevent duplicate logs
            "handlers": ["console"],
            "level": "WARNING",
        },
        "django": {
            "handlers": ["console"],
            "propagate": False,
        },
        "django.server": {
            "handlers": ["django.server"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["mail_admins", "console"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "app": {
            "handlers": ["console", "mail_admins"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Custom user app
AUTH_USER_MODEL = "users.User"

# Social login
AUTHENTICATION_BACKENDS = (
    "social_core.backends.google.GoogleOAuth2",
    "social_core.backends.facebook.FacebookOAuth2",
    "social_core.backends.twitter.TwitterOAuth",
    "src.users.backends.EmailOrUsernameModelBackend",
    "django.contrib.auth.backends.ModelBackend",
)
for key in [
    "GOOGLE_OAUTH2_KEY",
    "GOOGLE_OAUTH2_SECRET",
    "FACEBOOK_KEY",
    "FACEBOOK_SECRET",
    "TWITTER_KEY",
    "TWITTER_SECRET",
]:
    # exec("SOCIAL_AUTH_{key} = os.environ.get('{key}', '')".format(key=key))
    globals()["SOCIAL_AUTH_" + key] = os.getenv(key, "")

# FB
SOCIAL_AUTH_FACEBOOK_SCOPE = ["email"]
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {"fields": "id, name, email"}
SOCIAL_AUTH_FACEBOOK_API_VERSION = "5.0"

# Twitter
SOCIAL_AUTH_TWITTER_SCOPE = ["email"]

SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = ["email", "profile"]
SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ["username", "first_name", "email"]
# If this is not set, PSA constructs a plausible username from the first portion of the
# user email, plus some random disambiguation characters if necessary.
SOCIAL_AUTH_USERNAME_IS_FULL_EMAIL = True
SOCIAL_AUTH_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    "social_core.pipeline.social_auth.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.social_auth.associate_by_email",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
)

SOCIAL_AUTH_TWITTER_PIPELINE = (
    "social_core.pipeline.social_auth.social_details",
    "social_core.pipeline.social_auth.social_uid",
    "social_core.pipeline.social_auth.auth_allowed",
    # 'social_core.pipeline.social_auth.social_user',
    "src.common.social_pipeline.user.social_user",
    "social_core.pipeline.user.get_username",
    "social_core.pipeline.social_auth.associate_by_email",
    "social_core.pipeline.user.create_user",
    "social_core.pipeline.social_auth.associate_user",
    "social_core.pipeline.social_auth.load_extra_data",
    "social_core.pipeline.user.user_details",
    "src.common.social_pipeline.user.login_user",  # login correct user at the end
)

SOCIAL_AUTH_LOGIN_REDIRECT_URL = "/complete/twitter/"

THUMBNAIL_ALIASES = {
    "src.users": {
        "thumbnail": {"size": (100, 100), "crop": True},
        "medium_square_crop": {"size": (400, 400), "crop": True},
        "small_square_crop": {"size": (50, 50), "crop": True},
    },
}

# Django Rest Framework

# Django Rest Framework
REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
    "PAGE_SIZE": int(os.getenv("DJANGO_PAGINATION_LIMIT", 18)),
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S.%fZ",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        # 'rest_framework_xml.renderers.XMLRenderer',
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        # "rest_framework.permissions.IsAuthenticated",  This forces login for all views
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        # "rest_framework.authentication.SessionAuthentication",
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        # "rest_framework.authentication.TokenAuthentication",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "rest_framework.parsers.JSONParser",
        "rest_framework_xml.parsers.XMLParser",
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/second",
        "user": "1000/second",
        "subscribe": "60/minute",
    },
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}


SPECTACULAR_SETTINGS = {
    "TITLE": " zeefas API",
    "DESCRIPTION": "Backend API documentation for zeefas",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,  # keeps /api/schema/ clean
}

# JWT configuration

# ORIGIN OF SECRET KEY
# from django.core.management.utils import get_random_secret_key

JWT_SECRET_KEY = os.getenv(
    "JWT_SIGNING_KEY", "nlt2fz*q*&+fj0*e$+vj2&l=5(%uw)rg0u6d7dt0c"
)

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    # 'ROTATE_REFRESH_TOKENS': False,
    # 'BLACKLIST_AFTER_ROTATION': True,
    # 'UPDATE_LAST_LOGIN': False,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": JWT_SECRET_KEY,
    "VERIFYING_KEY": None,
    # 'AUDIENCE': None,
    # 'ISSUER': None,
    "AUTH_HEADER_TYPES": ("Bearer", "JWT"),
    # 'AUTH_HEADER_NAME': 'AUTHORIZATION',
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    # 'JTI_CLAIM': 'jti',
    # 'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    # 'SLIDING_TOKEN_LIFETIME': timedelta(minutes=5),
    # 'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=1),
}

# summernote configuration
SUMMERNOTE_CONFIG = {
    "summernote": {
        "toolbar": [
            ["style", ["style"]],
            ["font", ["bold", "underline", "clear"]],
            ["fontname", ["fontname"]],
            ["color", ["color"]],
            ["para", ["ul", "ol", "paragraph", "smallTagButton"]],
            ["table", ["table"]],
            ["insert", ["link", "video"]],
            ["view", ["fullscreen", "codeview", "help"]],
        ]
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


SWAGGER_SETTINGS = {
    "api_version": "1.0",
    "relative_paths": True,
    "VALIDATOR_URL": None,
    "USE_SESSION_AUTH": True,
    "SECURITY_DEFINITIONS": {
        "Token": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": 'Enter "Token <your_token_here>" (for DRF TokenAuthentication) or "Bearer <your_jwt_here>" if using JWT-based auth.',
        },
    },
    # Add these settings for better UX
    # "PERSIST_AUTH": True,  # Persist auth across page reloads
    # "REFETCH_SCHEMA_WITH_AUTH": True,  # Refetch schema when auth changes
    # "REFETCH_SCHEMA_ON_LOGOUT": True,  # Refetch schema on logout
}


ACCOUNT_DELETION_POLICY_VERIFICATION_TOKEN = os.getenv(
    "ACCOUNT_DELETION_POLICY_VERIFICATION_TOKEN"
)


PAYSTACK_SECRET = os.getenv("PAYSTACK_SECRET", None)
