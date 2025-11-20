from datetime import datetime
import secrets

from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import (
    ValidationError,
    PermissionDenied,
    AuthenticationFailed,
)
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenViewBase,
)
from rest_framework_simplejwt.serializers import (
    TokenObtainSerializer,
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import update_last_login

from src.users.utils import generate_signed_token, verify_signed_token
from src.social.views import exchange_token, complete_twitter_login
from src.users.models import User


def _jwt_response(serializer_or_user):
    user = getattr(serializer_or_user, "user", serializer_or_user)
    refresh = RefreshToken.for_user(user)
    tokens = {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }
    access, refresh = tokens["access"], tokens["refresh"]
    access_expiry = int(
        (timezone.now() + settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]).timestamp()
    )
    refresh_expiry = int(
        (timezone.now() + settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"]).timestamp()
    )

    update_last_login(None, user)

    return Response(
        {
            "access": access,
            "refresh": refresh,
            "access_expiry": str(access_expiry),
            "refresh_expiry": str(refresh_expiry),
        },
        status=status.HTTP_200_OK,
    )


def authenticate(**kwargs):
    password = kwargs.pop("password", None)
    user = User.objects.filter(**kwargs).first()

    if password is None:
        raise ValueError("Server Error password is required")

    if user is not None and user.check_password(password):
        return user


class FirstFactorSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(max_length=128, write_only=True)

    default_error_messages = {
        "no_active_account": _("No active account found with the given credentials")
    }

    def validate(self, attrs: dict):
        authenticate_kwargs = {
            "email": attrs["email"],
            "password": attrs["password"],
        }
        self.user = authenticate(**authenticate_kwargs)

        if not self.user:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        return {}


class SecondFactorSerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=10, write_only=True)
    tfa_token = serializers.CharField(max_length=200, write_only=True)

    default_error_messages = {
        "no_active_account": _("No active account found with the given credentials"),
        "invalid_otp": _("invalid otp"),
        "invalid_tfa_token": _("invalid tfa_token"),
    }

    def validate(self, attrs: dict):
        otp = attrs.get("otp")
        if not otp or len(otp) != 6 or not otp.isdigit():
            raise AuthenticationFailed(
                self.error_messages["invalid_otp"],
                "invalid_otp",
            )

        tfa_token = attrs.get("tfa_token")
        if not tfa_token:
            raise AuthenticationFailed(
                self.error_messages["invalid_tfa_token"],
                "invalid_tfa_token",
            )

        user_id = verify_signed_token(tfa_token)
        if not user_id or "///" not in user_id:
            raise AuthenticationFailed(
                self.error_messages["invalid_tfa_token"],
                "invalid_tfa_token",
            )

        user_id = user_id.split("///")[0]

        self.user = User.objects.filter(id=user_id).first()
        if not self.user:
            raise AuthenticationFailed(
                self.error_messages["no_active_account"],
                "no_active_account",
            )

        return {}

@extend_schema(tags=["auth"])
class TokenPairView__FirstFactor(TokenObtainPairView):
    """Return access and refresh token if 2FA is disabled

    since 2fa will be ENABLED by default and cannot be disabled, this returns
    ```json
    {
        "tfa_token": "<token>"  // expires in 5 minutes
    }
    ```

    CALL THE Second Factor endpoint with this `tfa_token` bro to get your { access_token, refresh_token }

    """

    serializer_class = FirstFactorSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        user = serializer.user

        # if not (user.is_email_verified or user.is_phone_number_verified):
        if not (user.is_email_verified):
            raise PermissionDenied(
                {
                    "error": "user email or phone number not verified",
                    "details": {
                        "email_verified": user.is_email_verified,
                        "phone_number_verified": user.is_phone_number_verified,
                    },
                }
            )

        if not user.two_factor_enabled:
            return _jwt_response(serializer)

        nonce = f"///{secrets.token_hex(10)}"
        signed_token = generate_signed_token(str(user.id) + nonce)

        return Response({"tfa_token": signed_token}, status=status.HTTP_200_OK)

@extend_schema(tags=["auth"])
class TokenPairView__SecondFactor(TokenViewBase):
    serializer_class = SecondFactorSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        user = serializer.user

        if not (user.is_email_verified or user.is_phone_number_verified):
            raise PermissionDenied(
                {
                    "error": "user email or phone number not verified",
                    "details": {
                        "email_verified": user.is_email_verified,
                        "phone_number_verified": user.is_phone_number_verified,
                    },
                }
            )

        return _jwt_response(serializer)

@extend_schema(tags=["auth"])
class RefreshTokenView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as e:
            raise InvalidToken(e.args[0])

        access = serializer.validated_data["access"]
        access_expiry = int(
            (datetime.now() + settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"]).timestamp()
        )

        return_values = {
            "access": access,
            "access_expiry": str(access_expiry),
        }

        return Response(return_values, status=status.HTTP_200_OK)
