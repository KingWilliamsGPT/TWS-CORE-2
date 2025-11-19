import re
import random
import string
import hashlib
import hmac
import logging
from pprint import pformat

logger = logging.getLogger("app")

from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from django.conf import settings

from src.common.clients import zeptomail
from src.common.serializers import EmptySerializer
from .services.webhook import WebhookService
from .contants import PAYSTACK_IP_WHITELIST


class PaystackViewSet(viewsets.GenericViewSet):
    """
    Creates, Updates and Retrieves - User Accounts
    """

    serializers = {
        "default": EmptySerializer,
    }
    permissions = {
        "default": (AllowAny,),
    }

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers["default"])

    def get_permissions(self):
        self.permission_classes = self.permissions.get(
            self.action, self.permissions["default"]
        )
        return super().get_permissions()

    @action(
        detail=False,
        methods=["post"],
        url_path="webhook-respond",
        url_name="webhook_respond",
    )
    def webhook_respond(self, request):
        # Paystack webhook respond i'm not gonna call it Paystack_Webhook coz that's dumb security wise
        try:
            ip = request.META.get("REMOTE_ADDR")
            sig = request.META.get(
                "x-paystack-signature"
            )  # request will be presigned with secret key
            raw_payload = request.body  # raw_payload bytes
            payload = request.data  # dict

            if ip not in PAYSTACK_IP_WHITELIST:
                return Response({"message": f"FAIL"}, status=status.HTTP_403_FORBIDDEN)

            hash = hmac.new(
                settings.PAYSTACK_SECRET, raw_payload, hashlib.sha512
            ).hexdigest()
            if hash != sig:
                if settings.DEBUG:
                    logger.error(
                        f"Paystack webhook failed signature verification. \npayload: {payload} \nsig: {sig} \nhash: {hash}"
                    )
                return Response({"message": f"FAIL"}, status=status.HTTP_403_FORBIDDEN)

            WebhookService(payload).handle()

            return Response(
                {"message": f"Webhook received and processed from {ip}"},
                status=status.HTTP_200_OK,
            )
        except Exception as ex:
            ex = pformat(ex)
            _payload = pformat(payload)
            zeptomail._send(
                subject="Paystack webhook failed",
                to=settings.DEVELOPER_EMAILS,
                html_body=f"""
                    <h1>Paystack webhook failed</h1>
                    <br/>
                    <p><b>Remote IP:</b> {ip}</p>
                    <p><b>Signature:</b> {sig}</p>
                    <br/>
                    <br/>
                    <p><b>Raw Payload:</b> </p>
                    <pre>{_payload}</pre>
                    <h3>Exception:</h3>
                    <pre>{ex}</pre>
                """,
            )

            return Response({"message": f"FAIL"}, status=status.HTTP_403_FORBIDDEN)
