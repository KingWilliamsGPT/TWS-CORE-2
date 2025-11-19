import re
import random
import string
import hashlib
import hmac
import logging
from pprint import pformat

logger = logging.getLogger(__name__)

import paystack
from rest_framework import viewsets, mixins
from rest_framework.permissions import AllowAny
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from django.conf import settings

from src.users.permissions import IsVerifiedUser
from src.common.clients import zeptomail
from src.common.serializers import EmptySerializer
from .services import BankAccountService
from .banks_enum import banks
from .serializers import (
    GetBankSerializer,
    AddBankAccountSerializer,
    BankAccountSerializer,
)
from .models import BankAccount


paystack.api_key = settings.PAYSTACK_SECRET


class BankAccountViewSet(viewsets.GenericViewSet):
    """
    Creates, Updates and Retrieves - User Accounts
    """

    serializers = {
        "default": EmptySerializer,
        "resolve_nuban": GetBankSerializer,
        "add_bank_account": AddBankAccountSerializer,
        "my_banks": BankAccountSerializer,
    }
    permissions = {
        "default": [IsVerifiedUser],
    }
    queryset = BankAccount.objects.none()

    def get_serializer_class(self):
        return self.serializers.get(self.action, self.serializers["default"])

    def get_permissions(self):
        self.permission_classes = self.permissions.get(
            self.action, self.permissions["default"]
        )
        return super().get_permissions()

    @action(detail=False, methods=["post"])
    def resolve_nuban(self, request, *args, **kwargs):
        """
        Resolve NUBAN (Nigerian Uniform Bank Account Number) to get account name
        Example Request:
        ```json
        {
            "bank_code": "001",  # use 001 for test bank, paystack only gives 3 trials for live banks per day
            "account_number": "0001234567"
        }
        ```
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bank_code = serializer.validated_data["bank_code"]
        account_number = serializer.validated_data["account_number"]
        data = BankAccountService.resolve_nuban(
            bank_code=bank_code, account_number=account_number
        )
        bank_name, bank_label = banks.get(bank_code, ["Unknown Bank", "UNKNOWN_BANK"])
        return Response(
            {
                **data,
                "bank_code": bank_code,
                "bank_name": bank_name,
                "bank_label": bank_label,
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["post"])
    def add_bank_account(self, request, *args, **kwargs):
        """
        Just a test endpoint to verify that the service is up and running
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bank_code = serializer.validated_data["bank_code"]
        account_number = serializer.validated_data["account_number"]

        if bank_code == "001" and not settings.DEBUG:
            raise ValidationError("Bank code 001 is only for testing purposes.")

        bank_account = BankAccountService.add_bank_account(
            user=request.user,
            bank_code=bank_code,
            account_number=account_number,
        )
        return Response(
            self.get_serializer(bank_account).data, status=status.HTTP_201_CREATED
        )

    @action(detail=False, methods=["delete"])
    def remove_bank_account(self, request, *args, **kwargs):
        """
        Just a test endpoint to verify that the service is up and running
        """
        return Response({"status": "ok"}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def my_banks(self, request, *args, **kwargs):
        """
        List the user's bank accounts
        """
        bank_accounts = BankAccount.objects.filter(user=request.user)
        return Response(
            self.get_serializer(bank_accounts, many=True).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def get_banks(self, request, *args, **kwargs):
        """
        Retrieve a list of supported banks.

        Example Response:
        ```json
        [
            {
                "bank_code": "001",
                "bank_name": "Paystack Test Bank",
                "bank_label": "PAYSTACK_TEST_BANK"
            },
            ...
        ]
        ```

        DONOT USE bank 001 for real transactions, it is only for testing.
        (it won't even be included in this list in production).
        """

        # banks_list = [
        #     {"bank_code": code, "bank_name": name, "bank_label": label}
        #     for code, (name, label) in banks.items()
        # ]
        banks_list = []
        for code, (name, label) in banks.items():
            if not settings.DEBUG and code == "001":
                continue
            banks_list.append(
                {"bank_code": code, "bank_name": name, "bank_label": label}
            )
        return Response(banks_list, status=status.HTTP_200_OK)
