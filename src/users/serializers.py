from rest_framework import serializers
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from phonenumber_field.serializerfields import PhoneNumberField
from drf_spectacular.utils import extend_schema_serializer, OpenApiExample
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from phonenumber_field.phonenumber import to_python
from countries_plus.models import Country

from src.common.serializers import ThumbnailerJSONSerializer
from src.users.models import (
    User,
    RecoveryCode,
    WaitList,
)

# from .enums.bank_codes import BankCodeEnum
from src.bank_account_app.banks_enum import Banks


def country_flag(iso_code):
    return "".join(chr(127397 + ord(c)) for c in iso_code.upper())


class EmailOrPhoneField(serializers.Field):
    def to_internal_value(self, data):

        # Try email
        try:
            validate_email(data)
            return {"type": "email", "value": data.lower()}
        except ValidationError:
            pass

        # Try phone
        try:
            phone_number = to_python(data)
            if phone_number and phone_number.is_valid():
                return {"type": "phone", "value": phone_number.as_e164}
        except Exception:
            pass

        raise serializers.ValidationError(
            "Enter a valid email address or phone number."
        )

    def to_representation(self, value):
        # When serializing back out
        return value


class EmailOrPhoneSerializer(serializers.Serializer):
    email_or_phone_number = EmailOrPhoneField(required=True)


class ResetForgottenPasswordSerializer(serializers.Serializer):
    email_or_phone_number = EmailOrPhoneField(required=True)
    otp = serializers.CharField(required=True)
    password = serializers.CharField(required=True)
    repeat_password = serializers.CharField(required=True)


class CountrySerializer(serializers.ModelSerializer):
    country_flag = serializers.SerializerMethodField(read_only=True)

    def get_country_flag(self, obj):
        return country_flag(obj.iso)

    class Meta:
        model = Country
        fields = [
            "iso",
            "iso3",
            "name",
            "capital",
            "area",
            "population",
            "neighbours",
            "continent",
            "currency_code",
            "currency_name",
            "currency_symbol",
            "phone",
            "languages",
            "tld",
            "country_flag",
        ]


class UserSerializer(serializers.ModelSerializer):
    profile_picture = ThumbnailerJSONSerializer(
        required=False, allow_null=True, alias_target="src.users"
    )

    country = CountrySerializer(read_only=True)
    country_id = serializers.SlugRelatedField(
        slug_field="iso",
        queryset=Country.objects.all(),
        source="country",
        write_only=True,
        required=False,
    )
    onboarding_flow = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            "id",
            "user_type",
            "username",
            "first_name",
            "last_name",
            "email",
            "profile_picture",
            "picture_url",
            "phone_number",
            "tier",
            "country",
            "country_id",
            "state",
            "onboarding_status",
            "onboarding_flow",
            "country_registered_with",
            "is_email_verified",
            "is_phone_number_verified",
            "is_liveness_check_verified",
            "is_bvn_verified",
            "two_factor_enabled",
            "paystack_customer_verified",
            "paystack_dva_status",
            "paystack_dva_account_name",
            "paystack_dva_account_number",
            "paystack_dva_currency",
            "paystack_dva_bank_code",
            "paystack_dva_bank_name",
            "paystack_dva_bank_slug",
        )
        read_only_fields = [*fields]

    def get_onboarding_flow(self, obj):
        return obj.get_onboarding_flow()


class UpdateUserSerializer(serializers.ModelSerializer):
    country = CountrySerializer(read_only=True)
    country_id = serializers.SlugRelatedField(
        slug_field="iso",
        queryset=Country.objects.all(),
        source="country",
        write_only=True,
        required=False,
    )

    class Meta:
        model = User
        fields = (
            "id",
            "user_type",
            "first_name",
            "last_name",
            "username",
            "two_factor_enabled",
            "country",
            "country_id",
            "state",
            "country_registered_with",
        )
        read_only_fields = ["id", "country_registered_with"]


class CheckUsernameSerializer(serializers.ModelSerializer):
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ["username", "is_available"]
        extra_kwargs = {"username": {"required": True}}


class WaitListSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaitList
        fields = (
            "id",
            "email",
            "created_at",
        )
        read_only_fields = ("id", "created_at")


class CreateUserSerializer(serializers.ModelSerializer):
    profile_picture = ThumbnailerJSONSerializer(
        required=False, allow_null=True, alias_target="src.users"
    )
    # tokens = serializers.SerializerMethodField()

    # def get_tokens(self, user):
    #     return user.get_tokens()
    country = CountrySerializer(read_only=True)
    country_id = serializers.SlugRelatedField(
        slug_field="iso",
        queryset=Country.objects.all(),
        source="country",
        write_only=True,
        required=False,
    )
    onboarding_flow = serializers.SerializerMethodField()

    def get_onboarding_flow(self, obj):
        return obj.get_onboarding_flow()

    onboarding_token = serializers.SerializerMethodField()

    def get_onboarding_token(self, user):
        return user.get_onboarding_token()

    def create(self, validated_data):
        # call create_user on user object. Without this
        # the password will be stored in plain text.
        user = User.objects.create_user(**validated_data)
        return user

    class Meta:
        model = User
        fields = (
            "id",
            "user_type",
            "username",
            "password",
            "first_name",
            "last_name",
            "email",
            # 'tokens',
            "profile_picture",
            "phone_number",
            "country",
            "country_id",
            "country_registered_with",
            "state",
            "onboarding_status",
            "onboarding_flow",
            "is_email_verified",
            "is_phone_number_verified",
            "is_liveness_check_verified",
            "is_bvn_verified",
            "onboarding_token",
        )
        read_only_fields = (
            # 'tokens',
            "username",
            "onboarding_status",
            "onboarding_flow",
            "is_email_verified",
            "is_phone_number_verified",
            "is_liveness_check_verified",
            "is_bvn_verified",
            "country_registered_with",
            "onboarding_token",
        )
        extra_kwargs = {
            "password": {"write_only": True},
        }


class PasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=500)
    repeat_new_password = serializers.CharField(max_length=500)
    old_password = serializers.CharField(max_length=500)


class ResetPasswordAndSendEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=10, write_only=True, required=False)

    def validate_email(self, value):
        return value.strip().lower()


class PhoneVerificationSerializer(serializers.Serializer):
    phone_number = PhoneNumberField(region="NG")
    otp = serializers.CharField(max_length=10, write_only=True, required=False)


class ResetRecoveryCodesSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    recovery_codes = serializers.ListField(
        child=serializers.CharField(), read_only=True
    )


class BarcodeStuffSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    barcode_uri = serializers.CharField(read_only=True)
    image_url = serializers.CharField(read_only=True)


class KycVerificationSerializer(serializers.Serializer):
    bvn = serializers.CharField(max_length=11)
    bank_code = serializers.ChoiceField(choices=Banks.choices)
    account_number = serializers.CharField(max_length=10)


class TFA_Serializer(serializers.Serializer):
    tfa_token = serializers.CharField(max_length=200, write_only=True)


class TFA_OtpSerializer(TFA_Serializer):
    otp = serializers.CharField(max_length=10, write_only=True)


class OTP_Serializer(serializers.Serializer):
    otp = serializers.CharField(max_length=10, write_only=True)


class GetOboardingTokenSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=500, write_only=True)
    email = serializers.EmailField(write_only=True)
    onboarding_token = serializers.CharField(max_length=500, read_only=True)


class Onboarding:
    class UseOnboardingTokenSerializer(serializers.Serializer):
        onboarding_token = serializers.CharField(max_length=500, write_only=True)

    class ChangeUserNameSerializer(UseOnboardingTokenSerializer):
        new_username = serializers.CharField(max_length=150, write_only=True)

    class ChangeProfilePictureSerializer(UseOnboardingTokenSerializer):
        @extend_schema_field(OpenApiTypes.BINARY)
        class ProfilePictureField(serializers.ImageField):
            pass

        profile_picture = ProfilePictureField(required=True)

    class ChangeUserTypeSerializer(UseOnboardingTokenSerializer):
        user_type = serializers.ChoiceField(
            choices=User.UserType.choices, write_only=True
        )

    class SetUserLocationSerializer(UseOnboardingTokenSerializer):
        country = CountrySerializer(read_only=True)
        country_id = serializers.SlugRelatedField(
            slug_field="iso",
            queryset=Country.objects.all(),
            source="country",
            write_only=True,
            required=False,
        )
        state = serializers.CharField(max_length=100, write_only=True, required=False)