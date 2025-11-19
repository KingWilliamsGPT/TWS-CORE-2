import json
import logging
import paystack
from paystack import exceptions

from django.conf import settings
from rest_framework.exceptions import ValidationError, NotFound

from src.users.models import User
from src.common.clients import zeptomail
from ..exceptions import BusinessNotDVAReadyError
from ..utils import try_load_json, call_paystack_api


paystack.api_key = settings.PAYSTACK_SECRET
logger = logging.getLogger("app")


class Verification(paystack.Verification):
    @classmethod
    def validate_bank(
        cls,
        account_number: str,
        bank_code: str,
        document_number: str,
        country_code: str = "NG",
        account_name: str = "Unknown",
        account_type: str = "personal",
        document_type: str = "identityNumber",
    ):
        """
        Validate a bank account number.
        """

        raise paystack.exceptions.ApiException(
            "Account validation is not available in NG bro 😭"
        )
        if document_type not in (
            "identityNumber",
            "passportNumber",
            "businessRegistrationNumber",
        ):
            raise paystack.exceptions.ApiException(
                "Invalid document_type. Must be one of 'identityNumber', 'passportNumber', or 'businessRegistrationNumber'."
            )

        path_params = {}
        query_params = []
        form_params = []
        body_params = {
            "bank_code": bank_code,
            "country_code": country_code,
            "account_number": account_number,
            "account_name": account_name,
            "account_type": account_type,
            "document_type": document_type,
            "document_number": document_number,
        }
        response_types_map = {
            200: "Response",
            401: "Error",
            404: "Error",
        }

        return cls().api_client.call_api(
            "/bank/validate",
            "POST",
            path_params,
            query_params,
            body=body_params,
            post_params=form_params,
            response_types_map=response_types_map,
        )


class PaystackServices:
    @staticmethod
    def get_customer_by_code(user, must_be_by_fetch=False):
        """
        Note:
            `user_pub_id` in metadata is important as user.email can change.
            So basicaly we are searching by `user_pub_id`.
            we search by email first (faster) hoping the email has not changed.
            If email has changed we fetch all customers and loop through them (slower)
            to find the one with matching `user_pub_id` in metadata.

        This function was created to be used to update users who may have accidentaly not been updated when a paystack customer was created.
        """
        try:
            # first try fetching by email (faster)
            logger.debug(f"Fetching paystack customer by email: {user.email}")
            code = user.paystack_customer_code or user.email
            if not code:
                raise ValidationError("User has no email or paystack_customer_code")
            res = call_paystack_api(
                lambda: paystack.Customer.fetch(code=code),
                catch_exception=False,
            )
            logger.debug(f"Found Customer")
            customer = res.data
            user_pub_id = customer.get("metadata", {}).get("user_pub_id")
            if str(user.pub_id) != str(user_pub_id):
                logger.debug(
                    f"Customer with user.email|user.paystack_customer_code: {code} does not belong to this user"
                )
                raise paystack.exceptions.NotFoundException(
                    "Customer with this code does not exist"
                )
            return customer
        except paystack.exceptions.NotFoundException:
            # next try fetching by user_pub_id in metadata (slower)
            try:
                logger.debug(
                    f"Fetching paystack customer by user_pub_id in metadata: {user.pub_id}"
                )
                res = call_paystack_api(
                    lambda: paystack.Customer.list(),
                    catch_exception=False,
                )
                customers = res.data
                for customer in customers:
                    user_pub_id = customer.get("metadata", {}).get("user_pub_id")
                    if str(user.pub_id) == str(user_pub_id):
                        if must_be_by_fetch:
                            # refetch by code to ensure we have the latest data
                            return call_paystack_api(
                                lambda: paystack.Customer.fetch(
                                    code=customer["customer_code"]
                                ),
                                catch_exception=False,
                            ).data
                        return customer
                logger.debug(
                    f"No paystack customer found for user with id: {user.pub_id}"
                )
            except paystack.exceptions.ApiException as ex:
                logger.error(f"Failed to fetch paystack customer: {ex}")
                return None

    @classmethod
    def update_customer_if_needed(
        cls, user: User, force_update=False, suppress_exceptions=False
    ):
        """Pulls customer information from paystack to update the database."""
        logger.debug(
            f"update_customer_if_needed(user): Updating paystack customer for user with pub_id: {user.pub_id}"
        )
        if (
            not user.paystack_customer_code
            or not user.paystack_customer_id
            or not user.paystack_customer_verified  # please help me update UNVERIFIED users
        ) or force_update:
            customer = cls.get_customer_by_code(
                user,
                must_be_by_fetch=True,  # for complete data eg. `customer["identified"]`
            )
            if customer:
                user.paystack_customer_id = customer["id"]
                user.paystack_customer_code = customer["customer_code"]
                user.paystack_customer_verified = customer["identified"]
                user.is_bvn_verified = customer["identified"]
                if user.is_bvn_verified:
                    if user.tier < User.Tier.TIER_3:
                        user.tier = User.Tier.TIER_3
                user.paystack_customer_json = customer
                user.save(
                    update_fields=[
                        "paystack_customer_code",
                        "paystack_customer_id",
                        "paystack_customer_json",
                        "paystack_customer_verified",
                        "is_bvn_verified",
                        "tier",
                    ]
                )
                return user
            else:
                logger.debug(
                    f"update_customer_if_needed(user): No paystack customer found for user with pub_id: {user.pub_id}"
                )
                if suppress_exceptions:
                    return user
                raise NotFound("No paystack customer found for this user")
        logger.debug(
            f"update_customer_if_needed(user): No update needed for user with pub_id: {user.pub_id}"
        )
        return user

    @classmethod
    def create_customer(cls, user: User):
        if user.paystack_customer_code:
            return

        cls.can_we_create_dvas(raise_exception=True)

        customer = call_paystack_api(
            lambda: paystack.Customer.create(
                email=user.email,
                first_name=user.first_name,
                last_name=user.last_name,
                phone=str(user.phone_number),
                metadata={"user_pub_id": str(user.pub_id)},
            )
        )
        if customer.status:
            data = customer.data
            user.paystack_customer_code = data["customer_code"]
            user.paystack_customer_id = data["id"]
            user.paystack_customer_json = data
            user.save(
                update_fields=[
                    "paystack_customer_code",
                    "paystack_customer_id",
                    "paystack_customer_json",
                ]
            )

        return customer

    @classmethod
    def validate_customer(
        cls,
        user: User,
        bvn: str,
        bank_code: str,
        account_number: str,
        country: str = "NG",
        type: str = "bank_account",
    ):
        """
        Note:
        type: str -> only `bank_account` is supported by paystack atm.
        """
        if user.paystack_customer_verified:
            return

        cls.can_we_create_dvas(raise_exception=True)

        code = user.paystack_customer_code
        res = call_paystack_api(
            lambda: paystack.Customer.validate(
                code=code,
                first_name=user.first_name,
                last_name=user.last_name,
                type=type,
                bvn=bvn,
                bank_code=bank_code,
                account_number=account_number,
                country=country,
            )
        )
        return res

    @classmethod
    def create_dva(cls, user: User):
        """
        This will be called from the WebsocketServer so try not to throw errors here
        """
        cls.can_we_create_dvas(raise_exception=True)

        return call_paystack_api(
            lambda: paystack.DedicatedVirtualAccount.create(
                customer=user.paystack_customer_id,
                preferred_bank=settings.PREFERRED_DVA_BANK,
                metadata={"user_pub_id": str(user.pub_id)},
            )
        )

    @staticmethod
    def list_customers():
        return call_paystack_api(paystack.Customer.list)

    @staticmethod
    def can_we_create_dvas(raise_exception=False):
        if settings.DISABLE_DVA_CHECKS:
            return True
        try:
            paystack.DedicatedVirtualAccount.available_providers()
            return True
        except exceptions.UnauthorizedException as ex:
            zeptomail._send(
                subject="DVA is not setup for business",
                to=settings.DEVELOPER_EMAILS,
                html_body=f"""
                <p>This business is not setup to create Dedicated Virtual Accounts.</p>
                <pre>{ex}</pre>
                """,
            )
            if raise_exception:
                raise BusinessNotDVAReadyError("Business cannot create DVA accounts")

            return False
