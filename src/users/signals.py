from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings

from src.wallet.models import Wallet


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallets(sender, instance, created, **kwargs):
    if not created:
        return

    # I'll auto create these user wallets for new users
    default_wallet_types = [
        Wallet.WalletType.MAIN,
        Wallet.WalletType.SAVINGS,
        Wallet.WalletType.LOCKED,
    ]

    for wallet_type in default_wallet_types:
        Wallet.objects.get_or_create(
            user=instance,
            wallet_type=wallet_type,
            balance=Decimal('0.00'),
            wallet_name=wallet_type.title(),
        )
