import re
import random
import string
import hashlib
import hmac
import logging
from pprint import pformat

logger = logging.getLogger(__name__)

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


class ChatViewSet(viewsets.GenericViewSet):
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

    @action(detail=False, methods=["get"])
    def just_testing(self, request, *args, **kwargs):
        """
        Just a test endpoint to verify that the service is up and running
        """
        return Response({"status": "ok"}, status=status.HTTP_200_OK)
