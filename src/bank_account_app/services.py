import logging

import paystack
from django.conf import settings
from src.paystack_app.utils import call_paystack_api
from src.paystack_app.services.api import Verification
from .models import BankAccount

paystack.api_key = settings.PAYSTACK_SECRET
logger = logging.getLogger("app")


class BankAccountService:
    @staticmethod
    def resolve_nuban(bank_code, account_number):
        """
        Resolve a Nigerian bank account number (NUBAN) to get account details.
        Sample response:
        {
            'account_number': '9103294854',
            'account_name': 'TEST ACCOUNT 9103294854',
            'bank_id': 24
        }
        """
        logger.debug(
            f"BankAccountService.resolve_nuban(bank_code={bank_code}, account_number={account_number})"
        )
        response = call_paystack_api(
            lambda: paystack.Verification.resolve_account_number(
                account_number=account_number, bank_code=bank_code
            )
        )
        logger.debug(f"resolve_nuban response: {response}")
        return response.data

    @classmethod
    def add_bank_account(
        cls,
        user,
        bank_code,
        account_number,
        account_name="Unknown",
        is_primary=False,
        is_verified=False,
        **kw,
    ):
        existing_account = BankAccount.objects.filter(
            user=user, bank_code=bank_code, account_number=account_number
        ).first()
        if existing_account:
            logger.debug(f"Bank account already exists: {existing_account}")
            return existing_account

        account_name = cls.resolve_nuban(bank_code, account_number).get(
            "account_name", account_name
        )

        if is_primary:
            # Unset existing primary accounts for the user
            BankAccount.objects.filter(user=user, is_primary=True).update(
                is_primary=False
            )

        bank_account = BankAccount.objects.create(
            user=user,
            bank_code=bank_code,
            account_number=account_number,
            account_name=account_name,
            is_primary=is_primary,
            is_verified=is_verified,
        )

        logger.debug(f"Created bank account: {bank_account}")
        return bank_account
