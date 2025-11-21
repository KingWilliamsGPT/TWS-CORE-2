import uuid
import hashlib
import secrets
from decimal import Decimal

import pyotp
from django.db import models
from django.conf import settings
from django.dispatch import receiver
from django.contrib.auth.models import AbstractUser
from rest_framework_simplejwt.tokens import RefreshToken
from easy_thumbnails.fields import ThumbnailerImageField
from django.urls import reverse
from django_rest_passwordreset.signals import reset_password_token_created
from easy_thumbnails.signals import saved_file
from easy_thumbnails.signal_handlers import generate_aliases_global
from phonenumber_field.modelfields import PhoneNumberField

from django_countries.fields import CountryField
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.hashers import make_password, check_password
from countries_plus.models import Country

from src.common.helpers import build_absolute_uri
from src.notifications.services import notify, ACTIVITY_USER_RESETS_PASS
from src.wallet.models import Wallet


def generate_random_secret():
    return pyotp.random_base32(32)


@receiver(reset_password_token_created)
def password_reset_token_created(
    sender, instance, reset_password_token, *args, **kwargs
):
    """
    Handles password reset tokens
    When a token is created, an e-mail needs to be sent to the user
    """
    reset_password_path = reverse("password_reset:reset-password-confirm")
    context = {
        "username": reset_password_token.user.username,
        "email": reset_password_token.user.email,
        "reset_password_url": build_absolute_uri(
            f"{reset_password_path}?token={reset_password_token.key}"
        ),
    }

    notify(
        ACTIVITY_USER_RESETS_PASS,
        context=context,
        email_to=[reset_password_token.user.email],
    )


class UserType(models.TextChoices):
    CUSTOMER = "customer", "Customer"
    SELLER = "seller", "Seller"


class OnboardingStatus(models.TextChoices):
    NEEDS_BASIC_INFORMATION = "needs_basic_information", "Needs Basic Information"
    NEEDS_EMAIL_VERIFICATION = "needs_email_verification", "Needs Email Verification"
    NEEDS_PHONE_VERIFICATION = "needs_phone_verification", "Needs Phone Verification"
    NEEDS_USER_TYPE = "needs_user_type", "Needs User Type Selection"
    NEEDS_PROFILE_USERNAME = "needs_profile_username", "Needs Profile Username Completion"
    NEEDS_PROFILE_PICTURE = "needs_profile_picture", "Needs Profile Picture Upload"
    NEEDS_LOCATION_INFO = "needs_location_info", "Needs Location Information"
    NEEDS_STORE_INFO = "needs_store_info", "Needs Store Information"
    NEEDS_KYC_IDENTITY_VERIFICATION = "needs_kyc_identity_verification", "Needs KYC Identity Verification"
    NEEDS_BANK = "needs_bank", "Needs Bank Information"
    NEEDS_VENDOR_PLAN = "needs_vendor_plan", "Needs Vendor Plan Selection"
    COMPLETED = "completed", "Completed"


class UserWalletMixin:
    @property
    def main_wallet(self):
        return self.wallets.filter(wallet_type=Wallet.WalletType.MAIN).first()

    @property
    def savings_wallet(self):
        return self.wallets.filter(wallet_type=Wallet.WalletType.SAVINGS).first()

    @property
    def locked_wallet(self):
        return self.wallets.filter(wallet_type=Wallet.WalletType.LOCKED).first()

    def get_or_create_wallet(self, wallet_type):
        wallet, created = self.wallets.get_or_create(
            wallet_type=wallet_type,
            defaults={"wallet_name": f"{wallet_type.title()} Wallet"},
        )
        return wallet

    def total_balance(self):
        return self.wallets.aggregate(total=models.Sum("balance"))["total"] or Decimal(
            "0.00"
        )


class UserAuthMixin:
    def get_authenticator_uri(self):
        return pyotp.totp.TOTP(self.two_factor_otp_secret).provisioning_uri(
            name=self.email, issuer_name=settings.SITE_NAME
        )

    def get_current_otp(self):
        return pyotp.totp.TOTP(self.two_factor_otp_secret).now()

    def has_basic_verification(self):
        return self.is_email_verified and self.is_phone_number_verified

    def can_upgrade_tier(self, tier):
        if tier > self.tier:
            return True

    def reset_tier(self):
        tier = self.Tier.TIER_0
        if self.has_basic_verification():
            tier = self.Tier.TIER_1

        if self.is_liveness_check_verified:
            tier = self.Tier.TIER_2

        if self.is_bvn_verified:
            tier = self.Tier.TIER_3

        self.tier = tier


class OnboardingMixin:


    ONBOARDING_FLOW = {
        UserType.CUSTOMER: [
            OnboardingStatus.NEEDS_BASIC_INFORMATION,
            OnboardingStatus.NEEDS_EMAIL_VERIFICATION,
            OnboardingStatus.NEEDS_PHONE_VERIFICATION,
            OnboardingStatus.NEEDS_USER_TYPE,
            OnboardingStatus.NEEDS_PROFILE_USERNAME,
            OnboardingStatus.NEEDS_PROFILE_PICTURE,
            OnboardingStatus.NEEDS_LOCATION_INFO,
            OnboardingStatus.COMPLETED,
        ],
        UserType.SELLER: [
            OnboardingStatus.NEEDS_BASIC_INFORMATION,
            OnboardingStatus.NEEDS_EMAIL_VERIFICATION,
            OnboardingStatus.NEEDS_PHONE_VERIFICATION,
            OnboardingStatus.NEEDS_USER_TYPE,
            OnboardingStatus.NEEDS_STORE_INFO,
            OnboardingStatus.NEEDS_KYC_IDENTITY_VERIFICATION,
            OnboardingStatus.NEEDS_BANK,
            OnboardingStatus.NEEDS_VENDOR_PLAN,
            OnboardingStatus.COMPLETED,
        ]
    }

    def get_onboarding_flow(self):
        """Returns the flow for the user type"""
        if not self.user_type:
            return []
        return self.ONBOARDING_FLOW[self.user_type]

    def get_next_onboarding_step(self):
        """Return the next step based on current onboarding status"""
        flow = self.get_onboarding_flow()
        if not flow or self.onboarding_status == self.OnboardingStatus.COMPLETED:
            return None
        try:
            current_index = flow.index(self.onboarding_status)
        except ValueError:
            return flow[0]  # fallback to first step
        if current_index + 1 < len(flow):
            return flow[current_index + 1]
        return None
    
    def step_after(self, step: OnboardingStatus):
        """Return the next step based on current onboarding status"""
        flow = self.get_onboarding_flow()
        if not flow or self.onboarding_status == self.OnboardingStatus.COMPLETED:
            return None
        try:
            current_index = flow.index(step)
        except ValueError:
            return flow[0]  # fallback to first step
        if current_index + 1 < len(flow):
            return flow[current_index + 1]
        return None

    def is_onboarding_completed(self):
        return self.onboarding_status == self.OnboardingStatus.COMPLETED

    def advance_onboarding(self, from_step=None):
        """Move to next step in the flow"""
        next_step = self.get_next_onboarding_step()
        if from_step:
            flow = self.get_onboarding_flow()
            from_step_index = flow.index(from_step)
            current_index = flow.index(self.onboarding_status)
            if from_step_index < current_index:
                # this means we have already advanced beyond this step, advancing from `from_step` might take us backwards
                next_step = self.onboarding_status
            elif from_step_index > current_index:
                # This is unlikely but it does mean that current_step has not been fully completed
                next_step = current_index

        if next_step:
            self.onboarding_status = next_step
            self.save()
            return next_step
        return None

    def remaining_onboarding_steps(self):
        """Return list of steps left"""
        flow = self.get_onboarding_flow()
        if not flow:
            return []
        try:
            current_index = flow.index(self.onboarding_status)
        except ValueError:
            current_index = 0
        return flow[current_index + 1:]


class User(OnboardingMixin, UserWalletMixin, UserAuthMixin, AbstractUser):
    PASSWORD_MIN_LENGTH = 6
    PASSWORD_MAX_LENGTH = 100

    class Tier(models.IntegerChoices):
        TIER_0 = 0, "Not Verified"  # default, no verification
        TIER_1 = 1, "Email / Phone"  # basic contact verification
        TIER_2 = 2, "Liveness Check"  # selfie / liveness verification
        TIER_3 = 3, "BVN Verified"  # full identity check

    class DVAStatus(models.IntegerChoices):
        PENDING = 0, "Pending"
        APPROVED = 1, "Approved"
        REJECTED = 2, "Rejected"
    

    UserType = UserType 
    OnboardingStatus = OnboardingStatus
    

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    pub_id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True
    )  # public identifier for frontend, user.id is kept secret for security reasons since it's a factor 2FA
    tier = models.IntegerField(choices=Tier.choices, default=Tier.TIER_0)
    user_type = models.CharField(
        max_length=10, choices=UserType.choices, default=UserType.CUSTOMER
    )
    onboarding_status = models.CharField(
        max_length=50,
        choices=OnboardingStatus.choices,
        default=OnboardingStatus.NEEDS_BASIC_INFORMATION,
    )

    profile_picture = ThumbnailerImageField(
        "ProfilePicture", upload_to="profile_pictures/", blank=True, null=True
    )
    picture_url = models.URLField("PictureUrl", blank=True, null=True)
    phone_number = PhoneNumberField(
        unique=True, null=True, blank=True, region="NG", default=None
    )
    country_registered_with = CountryField(default="NG")
    country = models.ForeignKey(
        Country,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
        # default="NG",
    )
    state = models.CharField(max_length=50, blank=True, null=True)
    # address = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    is_email_verified = models.BooleanField(default=False)
    is_phone_number_verified = models.BooleanField(default=False)
    is_liveness_check_verified = models.BooleanField(default=False)
    is_bvn_verified = models.BooleanField(default=False)

    email_otp_hash = models.CharField(
        max_length=128, blank=True, null=True, default=generate_random_secret
    )
    email_otp_trials = models.PositiveSmallIntegerField(default=0)
    email_otp_expires_at = models.DateTimeField(blank=True, null=True)

    phone_otp_hash = models.CharField(
        max_length=128, blank=True, null=True, default=generate_random_secret
    )
    phone_otp_trials = models.PositiveSmallIntegerField(default=0)
    phone_otp_expires_at = models.DateTimeField(blank=True, null=True)

    password_reset_otp_hash = models.CharField(
        max_length=128, blank=True, null=True, default=generate_random_secret
    )
    password_reset_otp_trials = models.PositiveSmallIntegerField(default=0)
    password_reset_otp_expires_at = models.DateTimeField(blank=True, null=True)

    two_factor_otp_secret = models.CharField(
        max_length=50, blank=True, null=True, default=generate_random_secret
    )
    two_factor_otp_trials = models.PositiveSmallIntegerField(default=0)
    two_factor_enabled = models.BooleanField(default=False)

    paystack_customer_id = models.CharField(max_length=50, blank=True, null=True)
    paystack_customer_code = models.CharField(max_length=50, blank=True, null=True)
    paystack_customer_verified = models.BooleanField(default=False)
    paystack_customer_json = models.JSONField(blank=True, null=True)

    paystack_dva_status = models.IntegerField(
        choices=DVAStatus.choices, default=DVAStatus.PENDING
    )
    paystack_dva_json = models.JSONField(blank=True, null=True)
    paystack_dva_id = models.CharField(max_length=50, blank=True, null=True)
    paystack_dva_account_name = models.CharField(max_length=100, blank=True, null=True)
    paystack_dva_account_number = models.CharField(max_length=50, blank=True, null=True)
    paystack_dva_currency = models.CharField(
        max_length=7, blank=True, null=True, default="NGN"
    )
    paystack_dva_bank_code = models.CharField(max_length=50, blank=True, null=True)
    paystack_dva_bank_name = models.CharField(max_length=50, blank=True, null=True)
    paystack_dva_bank_slug = models.CharField(max_length=50, blank=True, null=True)
    bvn_hashed = models.CharField(max_length=50, blank=True, null=True)

    # MeToMany
    # - wallets: Wallet
    # - recovery_codes: RecoveryCode

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.lower()
        super().save(*args, **kwargs)

    def set_bvn(self, raw_bvn, save=True):
        """
        Set user's bvn and hashes it
        """
        self.bvn_hashed = make_password(raw_bvn)
        if save:
            self.save(update_fields=["bvn_hashed"])

    def check_bvn(self, raw_bvn):
        """
        Check if the provided bvn matches the stored hashed bvn
        """
        if not self.bvn_hashed:
            return False
        return check_password(raw_bvn, self.bvn_hashed)

    def get_tokens(self):
        refresh = RefreshToken.for_user(self)

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    def __str__(self):
        return self.email

    def get_name(self):
        return self.get_full_name().strip() or self.email


class RecoveryCode(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="recovery_codes"
    )
    code_hash = models.CharField(max_length=64, db_index=True)  # store SHA256
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def mark_used(self):
        self.used = True
        self.save(update_fields=["used"])

    @staticmethod
    def hash_code(code: str) -> str:
        return hashlib.sha256(code.encode()).hexdigest()

    @classmethod
    def generate_codes(cls, user, count: int = 10) -> list[str]:
        """Generate N recovery codes, store hashed, return plaintext list for user."""
        codes = []
        for _ in range(count):
            code = secrets.token_hex(4).upper()  # e.g. 'A3F91B2C'
            code_hash = cls.hash_code(code)
            cls.objects.create(user=user, code_hash=code_hash)
            codes.append(code)
        return codes

    @classmethod
    def reset_codes(cls, user, count: int = 10) -> list[str]:
        cls.objects.filter(user=user).delete()
        return cls.generate_codes(user, count)

    @classmethod
    def verify_code(cls, user, code: str) -> bool:
        """Check if code is valid for user. If yes, burn it (mark used)."""
        code_hash = cls.hash_code(code)
        try:
            recovery_code = cls.objects.get(user=user, code_hash=code_hash, used=False)
        except cls.DoesNotExist:
            return False
        recovery_code.mark_used()
        return True


class WaitList(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


saved_file.connect(generate_aliases_global)
