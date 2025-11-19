import enum
import secrets
import datetime
import base64
import logging

import pyotp
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.exceptions import ValidationError

from src.common.clients import zeptomail
from .models import User, RecoveryCode
from .utils import generate_qrcode


OTP_EXPIRY_MINUTES = 5
MAX_TRIALS = 3
MAX_SECURITY_CODES = 10

logger = logging.getLogger("app")


class OtpType(str, enum.Enum):
    EMAIL_VERIFICATION = "email"
    PHONE_VERIFICATION = "phone"
    PASSWORD_RESET = "password_reset"
    TWO_FACTOR = "2fa"  # if you still want app-based 2FA, that can stay TOTP


def generate_random_otp(length: int = 6) -> str:
    """Generate a random numeric OTP of fixed length (default 6 digits)."""
    return str(secrets.randbelow(10**length)).zfill(length)


class UserService:
    @staticmethod
    def do_send_email(*args, **kwargs):
        if kwargs.pop("sendit", True):
            logger.debug("sending some email...")
            return zeptomail._send(*args, **kwargs)

    @staticmethod
    def do_send_sms(*args, **kwargs):
        if kwargs.pop("sendit", True):
            logger.debug("sending some sms...")
            return zeptomail._send(*args, **kwargs)

    @staticmethod
    def get_secret_as_barcode_text(user: User, secret: str):
        buf = generate_qrcode(secret)
        barcode_text = base64.b64encode(buf.getvalue()).decode()

        zeptomail._send(
            subject="Security Code Reset",
            to=[user.email],
            html_body=f"Hi use this barcode for your authenticator app <br><img src='data:image/png;base64,{barcode_text}' />",
        )

        return barcode_text

    @classmethod
    def send_user_otp(
        cls,
        user: User,
        type=OtpType.EMAIL_VERIFICATION,
        preferred_channel: str = "email",
        sendit=True,
    ):
        """
        Sends OTP to user. Email/phone OTPs are random, short-lived and burnable.
        2FA OTP can remain app-based (TOTP) if required.
        """
        otp = generate_random_otp()
        otp_hash = make_password(otp)
        with transaction.atomic():
            if type == OtpType.EMAIL_VERIFICATION:
                user.email_otp_hash = otp_hash
                user.email_otp_expires_at = timezone.now() + datetime.timedelta(
                    minutes=OTP_EXPIRY_MINUTES
                )
                user.email_otp_trials = 0
                user.save(
                    update_fields=[
                        "email_otp_hash",
                        "email_otp_expires_at",
                        "email_otp_trials",
                    ]
                )

            elif type == OtpType.PHONE_VERIFICATION:
                user.phone_otp_hash = otp_hash
                user.phone_otp_expires_at = timezone.now() + datetime.timedelta(
                    minutes=OTP_EXPIRY_MINUTES
                )
                user.phone_otp_trials = 0
                user.save(
                    update_fields=[
                        "phone_otp_hash",
                        "phone_otp_expires_at",
                        "phone_otp_trials",
                    ]
                )

            elif type == OtpType.PASSWORD_RESET:
                user.password_reset_otp_hash = otp_hash
                user.password_reset_otp_expires_at = (
                    timezone.now() + datetime.timedelta(minutes=OTP_EXPIRY_MINUTES)
                )
                user.password_reset_otp_trials = 0
                user.save(
                    update_fields=[
                        "password_reset_otp_hash",
                        "password_reset_otp_expires_at",
                        "password_reset_otp_trials",
                    ]
                )

            elif type == OtpType.TWO_FACTOR:
                # TOTP based for authenticator apps
                secret = user.two_factor_otp_secret
                totp = pyotp.TOTP(secret)
                otp = totp.now()
                user.two_factor_otp_trials = 0
                user.save(update_fields=["two_factor_otp_trials"])
            else:
                raise ValueError(f"Invalid otp type: {type}")

        # Send messages outside atomic to avoid rollback issues
        if type == OtpType.EMAIL_VERIFICATION:
            cls.do_send_email(
                subject="Email Verification OTP",
                to=[user.email],
                html_body=f"Your EMAIL VERIFICATION OTP is {otp}. It will expire in {OTP_EXPIRY_MINUTES} minutes.",
                sendit=sendit,
            )
        elif type == OtpType.PHONE_VERIFICATION:
            # for now send SMS otp to email for testing
            cls.do_send_sms(
                subject="Email Verification OTP",
                to=[user.email],
                html_body=f"Your PHONE NUMBER VERIFICATION OTP is {otp}. It will expire in {OTP_EXPIRY_MINUTES} minutes.",
                sendit=sendit,
            )
            print(f"Your PHONE OTP is {otp}")  # Replace with SMS provider

        elif type == OtpType.PASSWORD_RESET:
            if preferred_channel == "email":
                cls.do_send_email(
                    subject="Password Reset OTP",
                    to=[user.email],
                    html_body=f"Your PASSWORD RESET OTP is {otp}. It will expire in {OTP_EXPIRY_MINUTES} minutes.",
                    sendit=sendit,
                )
            elif preferred_channel == "phone":
                # for now send SMS otp to email for testing
                cls.do_send_sms(
                    subject="Password Reset OTP",
                    to=[user.email],
                    html_body=f"Your PASSWORD RESET OTP is {otp}. It will expire in {OTP_EXPIRY_MINUTES} minutes.",
                    sendit=sendit,
                )
                print(f"Your PASSWORD RESET OTP is {otp}")
            else:
                raise ValueError(f"Invalid preferred channel: {preferred_channel}")

        elif type == OtpType.TWO_FACTOR:
            cls.do_send_email(
                subject="2FA OTP",
                to=[user.email],
                html_body=f"Your 2FA OTP is {otp}. It will expire in {OTP_EXPIRY_MINUTES} minutes.",
                sendit=sendit,
            )

        return otp

    @staticmethod
    def update_tier(user: User, saveit=True):
        if user.tier == User.Tier.TIER_0 and user.has_basic_verification():
            user.tier = User.Tier.TIER_1

        elif user.tier == User.Tier.TIER_1 and user.is_liveness_check_verified:
            user.tier = User.Tier.TIER_2

        elif user.tier == User.Tier.TIER_2 and user.is_bvn_verified:
            user.tier = User.Tier.TIER_3

        else:
            print("Error: User tier not updated")

        if saveit:
            user.save(update_fields=["tier"])

    @classmethod
    def verify_user_otp(cls, user: User, otp: str, type=OtpType.EMAIL_VERIFICATION):
        with transaction.atomic():
            if type == OtpType.EMAIL_VERIFICATION:
                if not user.email_otp_hash:
                    raise ValidationError({"error": "User email not verified"})
                if user.is_email_verified:
                    raise ValidationError({"error": "User email already verified"})
                if (
                    user.email_otp_expires_at
                    and user.email_otp_expires_at < timezone.now()
                ):
                    raise ValidationError({"error": "OTP expired"})
                if user.email_otp_trials >= MAX_TRIALS:
                    raise ValidationError({"error": "User email OTP trials exceeded"})

                if check_password(otp, user.email_otp_hash):
                    user.is_email_verified = True
                    user.email_otp_hash = None
                    user.email_otp_expires_at = None
                    cls.update_tier(user, saveit=False)
                    user.save(
                        update_fields=[
                            "is_email_verified",
                            "email_otp_hash",
                            "email_otp_expires_at",
                            "tier",
                        ]
                    )
                    return True

                user.email_otp_trials += 1
                user.save(update_fields=["email_otp_trials"])
                return False

            elif type == OtpType.PHONE_VERIFICATION:
                if not user.email_otp_hash:
                    raise ValidationError({"error": "User phone number not verified"})
                if user.is_phone_number_verified:
                    raise ValidationError(
                        {"error": "User phone number already verified"}
                    )
                if (
                    user.phone_otp_expires_at
                    and user.phone_otp_expires_at < timezone.now()
                ):
                    raise ValidationError({"error": "OTP expired"})
                if user.phone_otp_trials >= MAX_TRIALS:
                    raise ValidationError({"error": "User phone OTP trials exceeded"})

                if check_password(otp, user.phone_otp_hash):
                    user.is_phone_number_verified = True
                    user.phone_otp = None
                    user.phone_otp_expires_at = None
                    cls.update_tier(user, saveit=False)
                    user.save(
                        update_fields=[
                            "is_phone_number_verified",
                            "phone_otp_hash",
                            "phone_otp_expires_at",
                            "tier",
                        ]
                    )
                    return True

                user.phone_otp_trials += 1
                user.save(update_fields=["phone_otp_trials"])
                return False

            elif type == OtpType.PASSWORD_RESET:
                if not user.password_reset_otp_hash:
                    raise ValidationError({"error": "User has no password reset OTP"})
                if (
                    user.password_reset_otp_expires_at
                    and user.password_reset_otp_expires_at < timezone.now()
                ):
                    raise ValidationError({"error": "OTP expired"})
                if user.password_reset_otp_trials >= MAX_TRIALS:
                    raise ValidationError(
                        {"error": "User password reset OTP trials exceeded"}
                    )

                if check_password(otp, user.password_reset_otp_hash):
                    user.password_reset_otp_hash = None
                    user.password_reset_otp_expires_at = None
                    user.save(
                        update_fields=[
                            "password_reset_otp_hash",
                            "password_reset_otp_expires_at",
                        ]
                    )
                    return True

                user.password_reset_otp_trials += 1
                user.save(update_fields=["password_reset_otp_trials"])
                return False

            elif type == OtpType.TWO_FACTOR:
                if pyotp.TOTP(user.two_factor_otp_secret).verify(otp, valid_window=1):
                    return True
                user.two_factor_otp_trials += 1
                user.save(update_fields=["two_factor_otp_trials"])
                return False

    @classmethod
    def reset_recovery_codes(cls, user: User, sendit=True):
        code_list = RecoveryCode.reset_codes(user, count=MAX_SECURITY_CODES)

        cls.do_send_email(
            subject="Security Code Reset",
            to=[user.email],
            html_body=f"Your security codes have been reset. They are: {', '.join(code_list)}",
            sendit=sendit,
        )

        return code_list
