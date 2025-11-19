from decimal import Decimal

from django.db import transaction

from src.users.models import User
from ..models import Wallet, Transaction



class BaseWalletService:
    @staticmethod
    def get_user_wallets(user: User):
        """
        Returns all wallets associated with a user.
        """
        return user.wallets.all()
    
    
    @staticmethod
    def deposit(wallet: Wallet, amount: Decimal, **kwargs):
        with transaction.atomic():
            wallet.fund_wallet(amount)
            return Transaction.objects.create(
                wallet=wallet,
                amount=amount,
                transaction_type=Transaction.TransactionType.DEPOSIT,
                status=Transaction.TransactionStatus.SUCCESS,
                **kwargs
            )
    # similarly for withdrawal, transfer…


class WalletService(BaseWalletService):
    pass