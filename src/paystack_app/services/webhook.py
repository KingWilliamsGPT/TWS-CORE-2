import logging
import uuid

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction

from src.common.clients import zeptomail

logger = logging.getLogger("app")
User = get_user_model()


class WebhookServiceBase(object):
    def __init__(self, data: str):
        self._data = data

    def handle(self):
        event = self._data["event"]
        paystack_data = self._data["data"]

        logger.info("=" * 1000)
        logger.info("WebhookServiceBase.data", self._data)
        logger.info("=" * 1000)

        method_handler_name = "handle_" + event.replace(".", "_")
        if hasattr(self, method_handler_name):
            method_handler = getattr(self, method_handler_name)
            try:
                method_handler(paystack_data)
            except Exception as e:
                error_id = str(uuid.uuid4())
                logged_message = f"""
                    Paystack webhook failed.
                    Event: {event} 
                    Handler: {method_handler_name}
                    IssueId: {error_id}
                """
                logger.error(logged_message)  # notice I didn't put raw data in logs

                zeptomail._send(
                    subject="Paystack webhook failed",
                    to=settings.DEVELOPER_EMAILS,
                    html_body=f"""
                        <p>Paystack webhook failed</p>
                        <p><b>Event:</b> {event}</p>
                        <p><b>Handler:</b> {method_handler_name}</p>
                        <p><b>IssueId:</b> {error_id}</p>
                        <br/>
                        <p><b>Paystack Data:</b></p>
                        <pre>{self._data}</pre>
                        <br/>
                        <p><b>Error:</b></p>
                        <pre>{e}</pre>
                    """,
                )

    # event handlers
    def handle_charge_dispute_create(self, data: dict):
        """A dispute was logged against your business"""

        zeptomail._send(
            subject="Paystack Dispute",
            to=settings.DEVELOPER_EMAILS,
            html_body=f"""
                <p>A dispute was logged against your business</p>
                <pre>{self._data}</pre>
            """,
        )

    def handle_charge_dispute_remind(self, data: dict):
        """A logged dispute has not been resolved"""

        zeptomail._send(
            subject="Paystack Dispute Reminder",
            to=settings.DEVELOPER_EMAILS,
            html_body=f"""
                <p>A logged dispute has not been resolved please take action immediately</p>
                <pre>{self._data}</pre>
            """,
        )

    def handle_charge_dispute_resolve(self, data: dict):
        """A dispute has been resolved"""

        zeptomail._send(
            subject="Paystack Dispute Resolved",
            to=settings.DEVELOPER_EMAILS,
            html_body=f"""
                <p>A dispute has been resolved</p>
                <pre>{self._data}</pre>
            """,
        )

    def handle_charge_success(self, data: dict):
        """A successful charge was made"""

    def handle_customeridentification_failed(self, data: dict):
        """A customer ID validation has failed"""

    def handle_customeridentification_success(self, data: dict):
        """A customer ID validation was successful"""

    def handle_dedicatedaccount_assign_failed(self, data: dict):
        """This is sent when a DVA couldn't be created and assigned to a customer"""

    def handle_dedicatedaccount_assign_success(self, data: dict):
        """This is sent when a DVA has been successfully created and assigned to a customer"""

    def handle_invoice_create(self, data: dict):
        """An invoice has been created for a subscription on your account. This usually happens 3 days before the subscription is due or whenever we send the customer their first pending invoice notification"""

    def handle_invoice_payment_failed(self, data: dict):
        """A payment for an invoice failed"""

    def handle_invoice_update(self, data: dict):
        """An invoice has been updated. This usually means we were able to charge the customer successfully. You should inspect the invoice object returned and take necessary action"""

    def handle_paymentrequest_pending(self, data: dict):
        """A payment request has been sent to a customer"""

    def handle_paymentrequest_success(self, data: dict):
        """A payment request has been paid for"""

    def handle_refund_failed(self, data: dict):
        """Refund cannot be processed. Your account will be credited with refund amount"""

    def handle_refund_pending(self, data: dict):
        """Refund initiated, waiting for response from the processor."""

    def handle_refund_processed(self, data: dict):
        """Refund has successfully been processed by the processor."""

    def handle_refund_processing(self, data: dict):
        """Refund has been received by the processor."""

    def handle_subscription_create(self, data: dict):
        """A subscription has been created"""

    def handle_subscription_disable(self, data: dict):
        """A subscription on your account has been disabled"""

    def handle_subscription_expiring_cards(self, data: dict):
        """Contains information on all subscriptions with cards that are expiring that month. Sent at the beginning of the month, to merchants using Subscriptions"""

    def handle_subscription_not_renew(self, data: dict):
        """A subscription on your account's status has changed to non-renewing. This means the subscription will not be charged on the next payment date"""

    def handle_transfer_failed(self, data: dict):
        """A transfer you attempted has failed"""

    def handle_transfer_success(self, data: dict):
        """A successful transfer has been completed"""

    def handle_transfer_reversed(self, data: dict):
        """A transfer you attempted has been reversed"""


class WebhookService(WebhookServiceBase):
    # TODO:
    # - make sure you are checking meta_data: {'user_id': str(user.id)}

    def handle_charge_success(self, data: dict):
        pass
        # with transaction.atomic():
        #     pass

    def handle_customeridentification_failed(self, data: dict):
        """
        {
            "event": "customeridentification.failed",
            "data": {
                "customer_id": 82796315,
                "customer_code": "CUS_XXXXXXXXXXXXXXX",
                "email": "email@email.com",
                "identification": {
                "country": "NG",
                "type": "bank_account",
                "bvn": "123*****456",
                "account_number": "012****345",
                "bank_code": "999991"
                },
                "reason": "Account number or BVN is incorrect"
            }
        }
        """
        with transaction.atomic():
            reason = data["reason"]
            email = data["email"]
            user = (
                User.objects.select_for_update()  # apply lock row, to avoid race coditions
                .filter(email=email)
                .first()
            )
            identification = data["identification"]
            if user:
                user.paystack_customer_id = None
                user.paystack_customer_code = None
                user.paystack_customer_verified = False
                user.is_bvn_verified = False
                user.paystack_customer_json = self._data
                user.reset_tier()

                user.save(
                    update_fields=[
                        "paystack_customer_id",
                        "paystack_customer_code",
                        "paystack_customer_json",
                        "paystack_customer_verified",
                        "is_bvn_verified",
                        "tier",
                    ]
                )

        if user:
            zeptomail._send(
                subject="Your BVN verification has failed",
                to=[user.email],
                html_body=f"""
                Your BVN verification has failed
                Reason: <b>{reason}</b>
                Details: <pre>{identification}</pre>
                """,
            )

    def handle_customeridentification_success(self, data: dict):
        """
        {
            "event": "customeridentification.success",
            "data": {
                "customer_id": "9387490384",
                "customer_code": "CUS_xnxdt6s1zg1f4nx",
                "email": "bojack@horsinaround.com",
                "identification": {
                    "country": "NG",
                    "type": "bvn",
                    "value": "200*****677"
                }
            }
        }
        """
        from .api import PaystackServices

        with transaction.atomic():
            email = data["email"]
            user = (
                User.objects.select_for_update()  # apply lock row, to avoid race coditions
                .filter(email=email)
                .first()
            )
            reason = data.get("reason", "")
            identification = data["identification"]

            if user:
                if not user.has_basic_verification():
                    return
                if not user.is_liveness_check_verified:
                    return
                # if user.is_bvn_verified:
                #     return

                user.paystack_customer_json = self._data
                user.paystack_customer_id = data["customer_id"]
                user.paystack_customer_code = data["customer_code"]
                user.paystack_customer_verified = True
                user.is_bvn_verified = True
                user.tier = User.Tier.TIER_3

                user.save(
                    update_fields=[
                        "paystack_customer_id",
                        "paystack_customer_code",
                        "paystack_customer_json",
                        "paystack_customer_verified",
                        "is_bvn_verified",
                        "tier",
                    ]
                )

        if user:
            zeptomail._send(
                subject="Your BVN has been verified",
                to=[user.email],
                html_body=f"""
                Your BVN has been verified
                Reason: <b>{reason}</b>
                Details: <pre>{identification}</pre>
                """,
            )

            PaystackServices.create_dva(user)

    def handle_dedicatedaccount_assign_failed(self, data: dict):
        """
        {
            "event": "dedicatedaccount.assign.failed",
            "data": {
                "customer": {
                    "id": 100110,
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "johndoe@test.com",
                    "customer_code": "CUS_hcekca0j0bbg2m4",
                    "phone": "+2348100000000",
                    "metadata": {},
                    "risk_action": "default",
                    "international_format_phone": "+2348100000000"
                },
                "dedicated_account": null,
                "identification": {
                    "status": "failed"
                }
            }
        }
        """
        with transaction.atomic():
            email = data["customer"]["email"]
            user = (
                User.objects.select_for_update()  # apply lock row, to avoid race coditions
                .filter(email=email)
                .first()
            )
            if user:
                user.paystack_dva_json = self._data
                user.paystack_dva_status = User.DVAStatus.REJECTED
                user.save(update_fields=["paystack_dva_json", "paystack_dva_status"])

        if user:
            zeptomail._send(
                subject="Your DVA verification has failed",
                to=[user.email],
                html_body=f"""
                    We could not attach a Wallet to your account. Please contact our support team.
                """,
            )

    def handle_dedicatedaccount_assign_success(self, data: dict):
        """
        {
            "event": "dedicatedaccount.assign.success",
            "data": {
                "customer": {
                    "id": 100110,
                    "first_name": "John",
                    "last_name": "Doe",
                    "email": "johndoe@test.com",
                    "customer_code": "CUS_hp05n9khsqcesz2",
                    "phone": "+2348100000000",
                    "metadata": {},
                    "risk_action": "default",
                    "international_format_phone": "+2348100000000"
                },
                "dedicated_account": {
                    "bank": {
                        "name": "Test Bank",
                        "id": 20,
                        "slug": "test-bank"
                    },
                    "account_name": "PAYSTACK/John Doe",
                    "account_number": "1234567890",
                    "assigned": true,
                    "currency": "NGN",
                    "metadata": null,
                    "active": true,
                    "id": 987654,
                    "created_at": "2022-06-21T17:12:40.000Z",
                    "updated_at": "2022-08-12T14:02:51.000Z",
                    "assignment": {
                        "integration": 100123,
                        "assignee_id": 100110,
                        "assignee_type": "Customer",
                        "expired": false,
                        "account_type": "PAY-WITH-TRANSFER-RECURRING",
                        "assigned_at": "2022-08-12T14:02:51.614Z",
                        "expired_at": null
                    }
                },
                "identification": {
                    "status": "success"
                }
            }
        }
        """
        with transaction.atomic():
            email = data["customer"]["email"]
            user = (
                User.objects.select_for_update()  # apply lock row, to avoid race coditions
                .filter(email=email)
                .first()
            )
            if user:
                if user.paystack_dva_status == User.DVAStatus.VERIFIED:
                    return
                user.paystack_dva_json = self._data
                user.paystack_dva_status = User.DVAStatus.VERIFIED

                dedicated_account = data["dedicated_account"]
                user.paystack_dva_id = dedicated_account["id"]
                user.paystack_dva_account_name = dedicated_account["account_name"]
                user.paystack_dva_account_number = dedicated_account["account_number"]
                user.paystack_dva_currency = dedicated_account["currency"]
                user.paystack_dva_bank_code = dedicated_account["bank"]["id"]
                user.paystack_dva_bank_name = dedicated_account["bank"]["name"]
                user.paystack_dva_bank_slug = dedicated_account["bank"]["slug"]

                customer = data["customer"]
                if (
                    user.paystack_customer_id != customer["id"]
                    or user.paystack_customer_code != customer["customer_code"]
                ):
                    raise ValueError(
                        f"Customer ID mismatch: {user.paystack_customer_id} != {customer['id']} and Customer Code mismatch: {user.paystack_customer_code} != {customer['customer_code']}"
                    )

                user.save(
                    update_fields=[
                        "paystack_dva_json",
                        "paystack_dva_status",
                        "paystack_dva_id",
                        "paystack_dva_account_name",
                        "paystack_dva_account_number",
                        "paystack_dva_currency",
                        "paystack_dva_bank_code",
                        "paystack_dva_bank_name",
                        "paystack_dva_bank_slug",
                    ]
                )

    def handle_transfer_failed(self, data: dict): ...

    def handle_transfer_success(self, data: dict): ...

    def handle_transfer_reversed(self, data: dict): ...
