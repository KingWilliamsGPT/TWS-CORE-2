import logging
from requests.exceptions import HTTPError

from django.conf import settings
from django.shortcuts import redirect
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from social_django.utils import psa
from social_django.models import UserSocialAuth
from google.oauth2 import id_token
from google.auth.transport import requests as grequests

from .serializers import SocialSerializer


User = get_user_model()
logger = logging.getLogger(__name__)


class GoogleError(Exception):
    "An error occured with google"


def _make_placeholder_email(backend_name: str, provider_uid: str) -> str:
    """
    Create a placeholder email for users without email from OAuth provider.

    Args:
        backend_name: Name of the OAuth backend (e.g., 'google-oauth2')
        provider_uid: Unique identifier from the OAuth provider

    Returns:
        A unique placeholder email address
    """
    domain = getattr(settings, "SOCIAL_NOEMAIL_DOMAIN", "noemail.local")
    return f"{backend_name}_{provider_uid}@{domain}"


def _get_google_user(token, to_save=True):
    # {'aud': '569...9-ibbuu4d...f5q97a.apps.googleusercontent.com',
    # 'azp': '569...9-ibbuu4d...f5q97a.apps.googleusercontent.com',
    # 'email': 'williamusanga23@gmail.com',
    # 'email_verified': True,
    # 'exp': 1762049370,
    # 'family_name': 'Samuel',
    # 'given_name': 'Williams',
    # 'iat': 1762045770,
    # 'iss': 'https://accounts.google.com',
    # 'jti': 'fc65506...1fd494c',
    # 'name': 'Williams Samuel',
    # 'nbf': 1762045470,
    # 'picture': 'https://lh3.googleusercontent.com/a/ACg8ocIhu1eNI...oGeNC=s96-c',
    # 'sub': '1038...53'}
    try:
        # Try verifying as a Google ID token first
        idinfo = id_token.verify_oauth2_token(
            token,
            grequests.Request(),
            settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,  # your client_id
        )

        # If verification passes, extract info
        email = idinfo.get("email")
        name = idinfo.get("name", "")
        first_name, last_name = name.split(" ") if name else ("", "")
        picture = idinfo.get("picture", "")
        email_verified = idinfo.get("email_verified", False)
        # import pprint

        # print("G" + "0" * 10 + "gle info")
        # pprint.pprint(idinfo)

        if not email:
            return None

        if not email_verified:
            raise GoogleError("Email not verified")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "username": email,
                "first_name": first_name,
                "last_name": last_name,
                # "profile_picture": picture,
                "picture_url": picture,
                "is_email_verified": True,
            },
        )

        if created:
            user.set_unusable_password()
            user.save()

        return user

    except Exception as ex:
        logger.error(ex)
        return None


def _is_placeholder_email(email: str) -> bool:
    """Check if an email is a placeholder email."""
    if not email:
        return False
    domain = getattr(settings, "SOCIAL_NOEMAIL_DOMAIN", "noemail.local")
    return email.endswith(f"@{domain}")


@api_view(http_method_names=["GET"])
@permission_classes([AllowAny])
def complete_twitter_login(request, *args, **kwargs):
    """Complete Twitter OAuth login and redirect to frontend with tokens."""
    tokens = request.user.get_tokens()
    access_token = tokens["access"]
    refresh_token = tokens["refresh"]
    return redirect(
        settings.TWITTER_FE_URL
        + f"?access_token={access_token}&refresh_token={refresh_token}"
    )


@api_view(http_method_names=["POST"])
@permission_classes([AllowAny])
@psa()
def exchange_token(request, backend):
    """
    Exchange an OAuth2 access token for a JWT token for this site.

    This endpoint allows the frontend to handle the OAuth2 flow and exchange
    the provider's access token for our application's JWT tokens.

    ## Supported Providers
    Call this endpoint with the provider name in the URL:
        POST API_ROOT + 'social/facebook/'
        POST API_ROOT + 'social/google-oauth2/'
        POST API_ROOT + 'social/twitter/'

    ## Request Format
    Requests must include the following field:
    - `access_token`: The OAuth2 access token provided by the provider

    ## Response Format
    Returns JWT access and refresh tokens on success.
    """
    from src.users.auth import _jwt_response as JWTResponseTokens

    serializer = SocialSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Get non-field errors key from settings
    non_field_errors_key = getattr(settings, "NON_FIELD_ERRORS_KEY", "non_field_errors")

    try:
        # Authenticate user via social auth provider
        # The psa decorator and this call handle the entire OAuth2 backend process
        user = _get_google_user(serializer.validated_data["access_token"])
        if not user:
            user = request.backend.do_auth(serializer.validated_data["access_token"])
    except GoogleError as e:
        # Google ID token verification failed
        logger.warning(f"OAuth authentication failed for backend {backend}: {str(e)}")
        return Response(
            {
                "errors": {
                    "token": "Invalid token",
                    "detail": str(e),
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    except HTTPError as e:
        # Invalid or malformed access token
        logger.warning(f"OAuth authentication failed for backend {backend}: {str(e)}")
        return Response(
            {
                "errors": {
                    "token": "Invalid token",
                    "detail": str(e),
                }
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as e:
        # Unexpected error during authentication
        logger.error(
            f"Unexpected error during OAuth authentication for backend {backend}: {str(e)}",
            exc_info=True,
        )
        return Response(
            {
                "errors": {
                    non_field_errors_key: "Authentication failed due to server error"
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if not user:
        # Authentication failed but no exception was raised
        logger.warning(f"OAuth authentication returned no user for backend {backend}")
        return Response(
            {"errors": {non_field_errors_key: "Authentication Failed"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Get social auth record and provider UID
    social = UserSocialAuth.objects.filter(user=user, provider=backend).first()
    provider_uid = social.uid if social else str(user.id)

    # Get user's email, convert empty string to None
    email = getattr(user, "email", None)

    # Create placeholder email if user has no email from provider
    if not email:
        placeholder_email = _make_placeholder_email(backend, provider_uid)
        user.email = placeholder_email
        user.save(update_fields=["email"])
        email = placeholder_email  # Update the email variable
        logger.info(
            f"Created placeholder email for user {user.id} from backend {backend}"
        )

    try:
        with transaction.atomic():
            # Check if another user already exists with this email
            # This can happen if user previously signed up with email/password
            # and is now logging in with OAuth
            existing_user = (
                User.objects.filter(email__iexact=email).exclude(id=user.id).first()
            )

            if existing_user:
                logger.info(
                    f"Merging OAuth user {user.id} into existing user {existing_user.id}"
                )

                # Transfer all social auth records to existing user
                socials_to_transfer = UserSocialAuth.objects.filter(user=user)
                for social_auth in socials_to_transfer:
                    social_auth.user = existing_user
                    social_auth.save(update_fields=["user"])

                # Check if the newly created user has any related objects
                # that would prevent deletion
                has_related_objects = False
                # related_checks = [
                #     # Add your model relationships here to check
                #     # Example: user.orders.exists(), user.wallets.exists()
                # ]

                # commenting this out out is abit dangerous, I love danger :)
                # for check in related_checks:
                #     if callable(check) and check():
                #         has_related_objects = True
                #         break

                if not has_related_objects:
                    # Safe to delete the duplicate user
                    user.delete()
                    logger.info(f"Deleted duplicate OAuth user {user.id}")
                else:
                    # Keep both users but log for manual review
                    logger.warning(
                        f"Cannot auto-delete OAuth user {user.id} - has related objects. "
                        f"Manual merge required with existing user {existing_user.id}"
                    )

                user = existing_user

            # Mark email as verified if it came from OAuth provider
            # and is not a placeholder email
            if not user.is_email_verified and not _is_placeholder_email(user.email):
                user.is_email_verified = True
                user.save(update_fields=["is_email_verified"])
                logger.info(f"Marked email as verified for user {user.id}")

    except Exception as e:
        # Log the error but continue - the user object should still be valid
        logger.error(
            f"Error during user merge/verification for backend {backend}: {str(e)}",
            exc_info=True,
        )
        # Don't expose internal errors to client
        # Continue with the user we have

    # Check if user account is active
    if not user.is_active:
        logger.warning(
            f"Inactive user {user.id} attempted to login via OAuth backend {backend}"
        )
        return Response(
            {"errors": {non_field_errors_key: "This user account is inactive"}},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Return JWT tokens
    return JWTResponseTokens(user)
