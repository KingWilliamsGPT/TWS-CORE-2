import uuid
import re
import random
import string
import logging

# django imports
from django.conf import settings
from django.db.models import Q
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db import transaction

# rest_framework/other imports
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.throttling import UserRateThrottle
from rest_framework.reverse import reverse
from rest_framework.exceptions import (
    ValidationError,
    PermissionDenied,
    NotFound,
    AuthenticationFailed,
)
from rest_framework import parsers
from rest_framework.parsers import MultiPartParser, FormParser, FileUploadParser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from countries_plus.models import Country

# local imports
from src.users.models import (
    User,
    RecoveryCode,
    WaitList,
)
from src.users.permissions import IsUserOrReadOnly, IsVerifiedUser
from src.users.serializers import (
    CreateUserSerializer,
    UserSerializer,
    UpdateUserSerializer,
    EmailOrPhoneSerializer,
    ResetForgottenPasswordSerializer,
    CheckUsernameSerializer,
    CountrySerializer,
    PasswordResetSerializer,
    ResetPasswordAndSendEmailSerializer,
    TFA_OtpSerializer,
    EmailVerificationSerializer,
    PhoneVerificationSerializer,
    ResetRecoveryCodesSerializer,
    BarcodeStuffSerializer,
    KycVerificationSerializer,
    TFA_Serializer,
    WaitListSerializer,
    OTP_Serializer,
    GetOboardingTokenSerializer,
    Onboarding,
)
from src.common.helpers import GetFrontendLink
from src.common.clients import zeptomail
from src.common.serializers import EmptySerializer
from src.paystack_app.services.api import PaystackServices
from src.bank_account_app.models import BankAccount
from src.bank_account_app.services import BankAccountService
from .password import PasswordValidator
from .services import UserService, OtpType
from .utils import (
    generate_qrcode,
    generate_signed_token,
    verify_signed_token,
    get_current_domain,
    WaitlistSpreadSheet,
)


LENGTH_OF_NEW_PASSWORD = 10
FRONTEND_LOGIN_URL = GetFrontendLink("login")
FRONTEND_GENERAL_SETTINGS_LINK = GetFrontendLink("general_settings")

logger = logging.getLogger("app")


def contains(s, pattern):
    return bool(re.search(pattern, s))


def generate_password(n=LENGTH_OF_NEW_PASSWORD):
    x = string.ascii_letters + "$#%^&~|?_"
    return "".join([random.choice(x) for i in range(n)])


class OtpRateThrottle(UserRateThrottle):
    rate = "3/min"


class AuthRouterViewSet(viewsets.GenericViewSet):
    """
    Creates, Updates and Retrieves - User Accounts
    """

    queryset = User.objects.all()
    serializers = {
        "default": UserSerializer,
        "register": CreateUserSerializer,
        "update_me": UpdateUserSerializer,
        "check_username": CheckUsernameSerializer,
        "get_countries": CountrySerializer,
        "get_states": EmptySerializer,
        "password_reset": PasswordResetSerializer,
        "forgot_password": ResetPasswordAndSendEmailSerializer,
        "send_forgot_password_otp": EmailOrPhoneSerializer,
        "reset_forgot_password": ResetForgottenPasswordSerializer,
        "send_email_verification_otp": EmailVerificationSerializer,
        "check_email_verification_otp": EmailVerificationSerializer,
        "send_phone_verification_otp": PhoneVerificationSerializer,
        "check_phone_verification_otp": PhoneVerificationSerializer,
        "send_2fa_otp": TFA_Serializer,
        "check_2fa_otp": TFA_OtpSerializer,
        "reset_recovery_codes": ResetRecoveryCodesSerializer,
        "request_qr_code": BarcodeStuffSerializer,
        "do_liveness_check": EmptySerializer,
        "do_kyc_check": KycVerificationSerializer,
        "health": EmptySerializer,
        "join_waitlist": WaitListSerializer,
        "get_onboarding_token": GetOboardingTokenSerializer,
        "set_username": Onboarding.ChangeUserNameSerializer,
        "set_profile_picture": Onboarding.ChangeProfilePictureSerializer,
    }
    permissions = {
        "default": [IsVerifiedUser],
        "qr_image_for_2fa": (AllowAny,),
        "forgot_password": (AllowAny,),
        "register": (AllowAny,),
        "send_email_verification_otp": (AllowAny,),
        "check_email_verification_otp": (AllowAny,),
        "send_phone_verification_otp": (AllowAny,),
        "check_phone_verification_otp": (AllowAny,),
        "send_2fa_otp": (AllowAny,),
        "check_2fa_otp": (IsAuthenticated,),
        "health": (AllowAny,),
        "join_waitlist": (AllowAny,),
        "get_countries": (AllowAny,),
        "get_states": (AllowAny,),
        "send_forgot_password_otp": (AllowAny,),
        "reset_forgot_password": (AllowAny,),
        "get_onboarding_token": (AllowAny,),
        "set_username": (AllowAny,),
        "set_profile_picture": (AllowAny,),
    }
   

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers["default"])

    def get_permissions(self):
        self.permission_classes = self.permissions.get(
            self.action, self.permissions["default"]
        )
        return super().get_permissions()

    def get_qr_image_for_2fa(self, user: User):

        buffer = generate_qrcode(user.get_authenticator_uri()).getvalue()
        return HttpResponse(
            buffer,
            content_type="image/png",
        )

    def perform_update(self, serializer):
        if self.request.user != serializer.instance:
            raise PermissionDenied("You can only update your own account.")

        serializer.save()


    @action(detail=False, methods=["get"], url_path="utils/get_countries")
    def get_countries(self, request):
        countries = Country.objects.all().order_by("name")
        return Response(CountrySerializer(countries, many=True).data)

    @action(detail=False, methods=["get"], url_path="utils/get_states")
    def get_states(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="join_waitlist")
    def join_waitlist(self, request):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        if WaitList.objects.filter(email=email).exists():
            return Response(
                {"message": "already_joined"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        waitlist_entry = WaitList(email=email)
        waitlist_entry.save()

        try:
            WaitlistSpreadSheet.append_to_waitlist(email)
        except Exception as e:
            logger.error(f"Failed to append {email} to waitlist spreadsheet: {e}")

        try:
            # load a html template from src\users\templates\emails\joined_waitlist.html and send it to the user
            zeptomail._send(
                subject="You've joined the waitlist!",
                to=[email],
                template="users/emails/joined_waitlist.html",
                context={
                    "email": email,
                    "whatsapp_invite_link": settings.WHATSAPP_INVITE_LINK,
                },
            )
        except Exception as e:
            logger.error(f"Failed to render waitlist email template: {e}")

        return Response({"message": "success"}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="qr_image_for_2fa/(?P<token>.*)")
    def qr_image_for_2fa(self, request, token):
        """This is used by the email client or frontend to display the qr code image for 2fa setup."""
        user_id = verify_signed_token(token, max_age=300)
        if not user_id:
            raise NotFound({"error": "QR code expired or invalid"})
        user = User.objects.filter(id=user_id).first()
        if not user:
            raise NotFound({"error": "user not found"})

        return self.get_qr_image_for_2fa(user)

    @action(detail=False, methods=["post"], url_path="2fa/request_qr_code")
    def request_qr_code(self, request):
        """This endpoint returns a signed token that expires in 5 minutes.

        Return value looks something like this
        ```json
        {
            "image_url": "/api/v1/users/qr_image_for_2fa/c06b6b7...ezEM/",
            "qrcode_uri": "otpauth://totp/zeefas:useremail@gmail.com?secret=BUN...S2&issuer=zeefas"
        }
        ```
        - use can `image_url` which will return the image in png (NOT RECOMMENDED: the link expires)
        - or use `qrcode_uri` to generate the image yourself (Recommended)

        **DONOT STORE THE QRCODE IN LOCALSTORAGE OR ANY BROWSER STORAGE BRO**
        """
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data["password"]

        user = self.request.user
        if not user.check_password(password):
            return Response(
                {"error": "Wrong password"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = generate_signed_token(user.id)
        image_url = reverse("auth-qr-image-for-2fa", kwargs={"token": token})
        qrcode_uri = user.get_authenticator_uri()

        serializer_data = {
            "image_url": image_url,
            "qrcode_uri": qrcode_uri,
        }

        return Response(serializer_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def register(self, request):
        """Register a new user.
        
        ```python
        ONBOARDING_FLOW = {
            UserType.CUSTOMER: [
                OnboardingStatus.NEEDS_BASIC_INFORMATION,
                OnboardingStatus.NEEDS_EMAIL_VERIFICATION,
                OnboardingStatus.NEEDS_PHONE_VERIFICATION,
                OnboardingStatus.NEEDS_PROFILE_USERNAME,
                OnboardingStatus.NEEDS_PROFILE_PICTURE,
                OnboardingStatus.NEEDS_LOCATION_INFO,
                OnboardingStatus.COMPLETED,
            ],
            UserType.SELLER: [
                OnboardingStatus.NEEDS_BASIC_INFORMATION,
                OnboardingStatus.NEEDS_EMAIL_VERIFICATION,
                OnboardingStatus.NEEDS_PHONE_VERIFICATION,
                OnboardingStatus.NEEDS_STORE_INFO,
                OnboardingStatus.NEEDS_KYC_IDENTITY_VERIFICATION,
                OnboardingStatus.NEEDS_BANK,
                OnboardingStatus.NEEDS_VENDOR_PLAN,
                OnboardingStatus.COMPLETED,
            ]
        }
        ```
        """
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        raw_password = serializer.validated_data["password"]

        if User.objects.filter(email=serializer.validated_data["email"]).exists():
            return Response(
                {"error": "user with this email already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        pv = PasswordValidator(raw_password)
        if not pv.run_check():
            return Response({"password": pv.errors}, status=status.HTTP_400_BAD_REQUEST)

        user = User(
            **serializer.validated_data,
            username=f"user_{uuid.uuid4().hex}",
            is_email_verified=False,
            is_phone_number_verified=False,
            country_registered_with=request.country.iso,
        )
        user.advance_onboarding()
        user.set_password(serializer.validated_data["password"])
        user.save()

        # otp = UserService.send_user_otp(
        #     user, type=OtpType.EMAIL_VERIFICATION, sendit=False
        # )
        code_list = UserService.reset_recovery_codes(
            user, sendit=False
        )  # DONOT DONOT AND I REPEAT DONOT SEND THESE CODES IN THIS RESPONSE BRO, the email/phone are not verified hence you cannot tell if they own these resources
        user_token = generate_signed_token(user.id)
        qr_image_url = f"{self.request.scheme}://{self.request.get_host()}" + reverse(
            "auth-qr-image-for-2fa", kwargs={"token": user_token}
        )

        UserService.do_send_email(
            subject="Register OTP",
            to=[user.email],
            html_body=f"""
            Hi {user.username}, here is your OTP to complete your registration 
            <br><img src='{qr_image_url}' />
            <br> And here are your recovery codes: {', '.join(code_list)}
            """,
            sendit=True,
        )

        return Response(CreateUserSerializer(user).data, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=["post"], url_path="onboarding/get_onboarding_token")
    def get_onboarding_token(self, request):
        """Get onboarding token for user to continue onboarding process.
        
        This only works as long as the user onboarding is not complete.

        **TOKEN EXPIRES IN 2 DAYS**
        """
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = User.objects.filter(email=email).first()
        if user is None:
            raise NotFound({"error": "user with this email does not exist"})
        if not user.check_password(password):
            raise ValidationError({"error": "invalid password"})
        if user.is_onboarding_completed():
            raise ValidationError({"error": "user onboarding is already completed"})
        onboarding_token = user.get_onboarding_token()
        return Response(
            {
                "onboarding_token": onboarding_token,
                "onboarding_status": user.onboarding_status,
                "onboarding_flow": user.get_onboarding_flow(),
            }, status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=["post"], url_path="onboarding/set_username")
    def set_username(self, request):
        """Change username during onboarding process.
        
        This only works as long as the user onboarding is at the username step.
        **TOKEN EXPIRES IN 2 DAYS**
        """
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        onboarding_token = serializer.validated_data["onboarding_token"]
        new_username = serializer.validated_data["new_username"]
        user_id = User.verify_tfa_token(onboarding_token, max_age=settings.ONBOARDING_TOKEN_EXPIRY_TIME_SECONDS)
        if not user_id:
            raise ValidationError({"error": "invalid or expired onboarding token"})
        user = User.objects.filter(id=user_id).first()
        if user is None:
            raise NotFound({"error": "user not found"})
        
        if user.is_onboarding_completed():
            raise ValidationError({"error": "user onboarding is already completed"})

        if user.is_future_step(step=User.OnboardingStatus.NEEDS_PROFILE_USERNAME):
            raise ValidationError({"error": "user is not at the username onboarding step"})
        
        user.username = new_username
        user.advance_onboarding(User.OnboardingStatus.NEEDS_PROFILE_USERNAME)
        user.save(update_fields=["username", "onboarding_status"])
        return Response(
            CreateUserSerializer(user, context={'request': request}).data, 
            status=status.HTTP_200_OK
        )
    
    @extend_schema(
        request=Onboarding.ChangeProfilePictureSerializer,
        responses={200: CreateUserSerializer}
    )
    @action(detail=False, methods=["post"], url_path="onboarding/set_profile_picture",  parser_classes=[MultiPartParser, FormParser, FileUploadParser])
    def set_profile_picture(self, request):
        """Upload profile picture during onboarding process.
        
        This only works as long as the user onboarding is at the profile picture step.
        **TOKEN EXPIRES IN 2 DAYS**
        """
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        onboarding_token = serializer.validated_data["onboarding_token"]
        profile_picture = serializer.validated_data["profile_picture"]
        
        user_id = User.verify_tfa_token(onboarding_token, max_age=settings.ONBOARDING_TOKEN_EXPIRY_TIME_SECONDS)
        if not user_id:
            raise ValidationError({"error": "invalid or expired onboarding token"})
        
        user = User.objects.filter(id=user_id).first()
        if user is None:
            raise NotFound({"error": "user not found"})
        
        if user.is_onboarding_completed():
            raise ValidationError({"error": "user onboarding is already completed"})
        
        if user.is_future_step(step=User.OnboardingStatus.NEEDS_PROFILE_PICTURE):
            raise ValidationError({"error": "user is not at the profile picture onboarding step"})
        
        user.profile_picture = profile_picture
        user.advance_onboarding(User.OnboardingStatus.NEEDS_PROFILE_PICTURE)
        user.save(update_fields=["profile_picture", "onboarding_status"])
        return Response(
            CreateUserSerializer(user, context={'request': request}).data, 
            status=status.HTTP_200_OK
        )
        

    @action(detail=False, methods=["post"], throttle_classes=[OtpRateThrottle], url_path="email/send_email_verification_otp")
    def send_email_verification_otp(self, request):
        """Send OTP to user to verify email.

        Call this endpoint without `otp` it'll be ignored if you do.

        Throttle's by 3request/min
        ```json
        {
        "detail": "Request was throttled. Expected available in 50 seconds."
        }
        ```
        """
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"]).first()

        if user is None:
            raise NotFound({"error": "user with this email does not exist"})

        if user.is_email_verified:
            raise ValidationError({"error": "User email already verified"})

        UserService.send_user_otp(user, type=OtpType.EMAIL_VERIFICATION)
        return Response({"otp": "otp sent to your email"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], throttle_classes=[OtpRateThrottle], url_path="phone/send_phone_verification_otp")
    def send_phone_verification_otp(self, request):
        """Send OTP to user to verify phone number.

        Call this endpoint without `otp` it'll be ignored if you do.

        Throttle's by 3 request/min
        ```json
        {
        "detail": "Request was throttled. Expected available in 50 seconds."
        }
        ```
        """
        serializer = PhoneVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]
        user = User.objects.filter(phone_number=phone_number).first()

        if user is None:
            raise NotFound(
                {"error": f"user with this phone number {phone_number} does not exist"}
            )

        if user.is_phone_number_verified:
            raise ValidationError({"error": "User phone number already verified"})

        UserService.send_user_otp(user, type=OtpType.PHONE_VERIFICATION)
        return Response(
            {"otp": "otp sent to your phone number"}, status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"], throttle_classes=[OtpRateThrottle], url_path="2fa/send_2fa_otp")
    def send_2fa_otp(self, request):
        """
        Get OTP for user to verify email or phone number

        Call this endpoint without `otp` it'll be ignored if you do.

        Throttle's by 3request/min
        ```json
        {
        "detail": "Request was throttled. Expected available in 50 seconds."
        }
        ```
        """
        user = request.user
        if user.is_anonymous:
            serializer = TFA_Serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            tfa_token = serializer.validated_data["tfa_token"]
            user_id = User.verify_tfa_token(tfa_token)
            if not user_id:
                raise AuthenticationFailed(
                    "Invalid or expired tfa token was provided",
                    "invalid_tfa_token",
                )
            user = User.objects.filter(id=user_id).first()
            if not user:
                raise NotFound({"error": "user not found"})

        UserService.send_user_otp(user, type=OtpType.TWO_FACTOR)
        return Response(
            {"otp": "otp sent to your email/authenticator app"},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"], throttle_classes=[OtpRateThrottle], url_path="email/check_email_verification_otp")
    def check_email_verification_otp(self, request):
        """Verify OTP for user to verify email.

        You have to call this endpoint with `otp`.
        Throttle's by 3request/min
        ```json
        {
        "detail": "Request was throttled. Expected available in 50 seconds."
        }
        """
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        if not otp:
            return Response(
                {"error": "otp is required at this point"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(email=user_email).first()
        if user is None:
            raise NotFound({"error": "user with this email does not exist"})

        if user.is_email_verified:
            raise ValidationError({"error": "User email already verified"})

        if UserService.verify_user_otp(user, otp, type=OtpType.EMAIL_VERIFICATION):
            return Response(
                {
                    "otp": "otp verified",
                    # "need_phone_verification": not user.is_phone_number_verified,
                    "onboarding_status": user.onboarding_status,
                    "onboarding_flow": user.get_onboarding_flow(),
                },
                status=status.HTTP_200_OK,
            )

        return Response({"error": "invalid otp"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], throttle_classes=[OtpRateThrottle], url_path="phone/check_phone_verification_otp")
    def check_phone_verification_otp(self, request):
        """Verify OTP for user to verify phone number

        You have to call this endpoint with `otp`.
        Throttle's by 3request/min
        ```json
        {
        "detail": "Request was throttled. Expected available in 50 seconds."
        }
        """
        serializer = PhoneVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone_number = serializer.validated_data["phone_number"]
        otp = serializer.validated_data["otp"]

        if not otp:
            return Response(
                {"error": "otp is required at this point"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(phone_number=phone_number).first()
        if user is None:
            raise NotFound(
                {"error": f"user with this phone number {phone_number} does not exist"}
            )

        if user.is_phone_number_verified:
            raise ValidationError({"error": "User phone number already verified"})

        if UserService.verify_user_otp(user, otp, type=OtpType.PHONE_VERIFICATION):
            return Response(
                {
                    "otp": "otp verified",
                    # "need_email_verification": not user.is_email_verified,
                    "onboarding_status": user.onboarding_status,
                    "onboarding_flow": user.get_onboarding_flow(),
                },
                status=status.HTTP_200_OK,
            )

        return Response({"error": "invalid otp"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], throttle_classes=[OtpRateThrottle], url_path="2fa/check_2fa_otp")
    def check_2fa_otp(self, request):
        """Verify OTP for user to verify email or phone number

        You have to call this endpoint with `otp`.
        Throttle's by 3request/min
        ```json
        {
        "detail": "Request was throttled. Expected available in 50 seconds."
        }
        """
        serializer = TFA_OtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        otp = serializer.validated_data["otp"]
        user = request.user
        if UserService.verify_user_otp(user, otp, type=OtpType.TWO_FACTOR):
            return Response({"otp": "otp verified"}, status=status.HTTP_200_OK)
        return Response({"error": "invalid otp"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["put"], url_path="password")
    def password_reset(self, request):
        """Reset password when user is logged in"""
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_password, confirm_new, old_password = (
            serializer.validated_data["new_password"],
            serializer.validated_data["repeat_new_password"],
            serializer.validated_data["old_password"],
        )

        if new_password != confirm_new:
            raise ValidationError("new password and it's confirmation did not match")

        user = request.user
        if user.check_password(old_password):
            if self.password_is_strong(new_password, user.username):
                user.set_password(new_password)
                user.save()
                return Response({"msg": "password reset successfully"})
            else:
                raise ValidationError({"error": "password is not strong"})

        raise ValidationError({"error": "invalid old password"})

    @action(detail=False, methods=["put"], throttle_classes=[OtpRateThrottle], url_path="password/send_forgot_password_otp")
    def send_forgot_password_otp(self, request):
        # send otp to email before doing anything

        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        e = serializer.validated_data["email_or_phone_number"]
        email_or_phone_number, preferred_channel = e["value"], e["type"]

        user = User.objects.filter(
            Q(email=email_or_phone_number) | Q(phone_number=email_or_phone_number)
        ).first()

        if user:
            # preferred_channel = (
            #     "email" if user.email == email_or_phone_number else "phone"
            # )
            UserService.send_user_otp(
                user, type=OtpType.PASSWORD_RESET, preferred_channel=preferred_channel
            )
        else:
            print("I_MUST_LIE_BUT: User does not exist")

        return Response({"msg": "password reset email sent"})

    @action(detail=False, methods=["put"], throttle_classes=[OtpRateThrottle], url_path="password/reset_forgot_password")
    def reset_forgot_password(self, request):
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        email_or_phone_number = serializer.validated_data["email_or_phone_number"][
            "value"
        ]
        otp = serializer.validated_data["otp"]
        password = serializer.validated_data["password"]
        repeat_password = serializer.validated_data["repeat_password"]

        if password != repeat_password:
            raise ValidationError(
                {
                    "error": "password and it's confirmation did not match",
                    "code": "password_mismatch",
                }
            )

        pv = PasswordValidator(password)
        if not pv.run_check():
            return Response({"password": pv.errors}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            user = (
                User.objects.select_for_update()
                .filter(
                    Q(email=email_or_phone_number)
                    | Q(phone_number=email_or_phone_number)
                )
                .first()
            )

            if not user:
                raise ValidationError({"error": "user does not exist"})

            if not UserService.verify_user_otp(user, otp, type=OtpType.PASSWORD_RESET):
                raise ValidationError({"error": "invalid otp"})

            user.set_password(password)
            user.save()
            return Response({"msg": "password reset successfully"})

    def password_is_strong(self, password, username):
        common_passwords = ("password",)
        password_len = len(password)

        if not password:
            return False

        if password in common_passwords:
            return False  # password too common

        if username in password:
            return False  # username must not be in password

        if not (User.PASSWORD_MIN_LENGTH <= password_len <= User.PASSWORD_MAX_LENGTH):
            return False

        if not (
            # password must contain atleast 1 uppercase letter, 1 number and 1 punctuation
            contains(password, r"[A-Z]")
            and contains(password, r"[0-9]")
            and contains(password, rf"[{string.punctuation}]")
        ):
            return False

        return True

    @action(detail=False, methods=["post"], url_path="2fa/reset_recovery_codes")
    def reset_recovery_codes(self, request):
        """Reset's users recovery codes

        A copy of the codes will be sent to the user's email for convenience.
        There is no endpoint to see the codes as they are hashed and not stored in plain text.
        The codes can be used as an alternative way to login, when the user no longer has access to his/her authenticator app.
        """
        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data["password"]

        if not request.user.check_password(password):
            raise ValidationError({"error": "invalid password bro"})

        code_list = UserService.reset_recovery_codes(request.user)

        return Response(
            {"recovery_codes": code_list}, status=status.HTTP_201_CREATED
        )  # I know, long winded

    @action(detail=False, methods=["post"])
    def do_liveness_check(self, request):
        """Do liveness check to validate user identity.

        For now just call this with no data an it'll upgrade user to Tier 2
        """

        me = request.user

        if me.is_liveness_check_verified and me.tier == User.Tier.TIER_2:
            return Response(UserSerializer(me).data, status=status.HTTP_200_OK)

        if me.tier <= User.Tier.TIER_2 and me.has_basic_verification():
            UserService.update_tier(me, saveit=False)
            me.is_liveness_check_verified = True
            me.save(update_fields=["tier", "is_liveness_check_verified"])
        else:
            raise ValidationError({"error": "user is not verified"})

        return Response(UserSerializer(me).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def do_kyc_check(self, request):
        """Verify kyc data

        You could use this for testing.
        ```json
        {
            "country": "NG",
            "type": "bank_account",
            "account_number": "0111111111",
            "bvn": "22222222221",
            "bank_code": "007",
            "first_name": "Uchenna",
            "last_name": "Okoro"
        }
        ```

        """
        from src.paystack_app.exceptions import BusinessNotDVAReadyError

        serializer = self.get_serializer_class()(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = request.user
        if not user.has_basic_verification():
            raise ValidationError({"error": "user is not email/phone number verified"})

        if not user.is_liveness_check_verified:
            raise ValidationError({"error": "user has not done liveness check."})

        if user.is_bvn_verified or user.paystack_customer_verified:
            return Response(
                {"msg": "user is already kyc verified", "code": "already_verified"},
                status=status.HTTP_200_OK,
            )
        try:
            bvn = serializer.validated_data[
                "bvn"
            ]  # note that the bvn is never actually stored
            bank_code = serializer.validated_data["bank_code"]
            account_number = serializer.validated_data["account_number"]
            BankAccountService.create_bank_account(
                user=user,
                bank_code=bank_code,
                account_number=account_number,
                is_primary=True,
            )

            logger.debug("Creating Customer")

            PaystackServices.update_customer_if_needed(
                user=request.user,
                force_update=False,  # force is only for testing
                suppress_exceptions=True,
            )
            PaystackServices.create_customer(user=request.user)

            PaystackServices.validate_customer(
                user=request.user,
                bvn=bvn,
                bank_code=bank_code,
                account_number=account_number,
            )
        except BusinessNotDVAReadyError as ex:
            raise ValidationError({"error": str(ex)})

        if user.is_bvn_verified or user.paystack_customer_verified:
            return Response(
                {"msg": "user is already kyc verified", "code": "already_verified"},
                status=status.HTTP_200_OK,
            )
        return Response(
            {"msg": "kyc verification pending approval", "code": "pending_approval"},
            status=status.HTTP_200_OK,
        )


class UserViewSet(viewsets.GenericViewSet):
    """
    Creates, Updates and Retrieves - User Accounts
    """

    queryset = User.objects.all()
    serializers = {
        "default": UserSerializer,
        "register": CreateUserSerializer,
        "update_me": UpdateUserSerializer,
        "check_username": CheckUsernameSerializer,
        "get_countries": CountrySerializer,
        "get_states": EmptySerializer,
    }
    permissions = {
        "default": [IsVerifiedUser],
    }

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers["default"])

    def get_permissions(self):
        self.permission_classes = self.permissions.get(
            self.action, self.permissions["default"]
        )
        return super().get_permissions()

    def perform_update(self, serializer):
        if self.request.user != serializer.instance:
            raise PermissionDenied("You can only update your own account.")

        serializer.save()

    @action(detail=False, methods=["patch"])
    def update_me(self, request, *args, **kwargs):
        be_partial_bro = True
        instance = self.request.user
        serializer = self.get_serializer(
            instance, data=request.data, partial=be_partial_bro
        )
        serializer.is_valid(raise_exception=True)
        username_in = serializer.validated_data.get("username")
        if username_in and username_in != instance.username:
            if (
                User.objects.exclude(id=instance.id)
                .filter(username=username_in)
                .exists()
            ):
                raise serializers.ValidationError(
                    {"username": "A user with this username already exists."}
                )
        self.perform_update(serializer)

        if getattr(instance, "_prefetched_objects_cache", None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def check_username(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        return Response(
            {"is_available": not User.objects.filter(username=username).exists()},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["delete"])
    def delete_me(self, request, *args, **kwargs):
        # self.request.user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def me(self, request):
        try:
            return Response(
                UserSerializer(
                    self.request.user, context={"request": self.request}
                ).data,
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            return Response(
                {"error": f"Wrong auth token {e}"}, status=status.HTTP_400_BAD_REQUEST
            )
