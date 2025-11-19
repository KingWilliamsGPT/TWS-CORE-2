import uuid
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator

from .exceptions import InsufficientFundsError


class Wallet(models.Model):
    """
        This can be used to represent user's Wallet, user's LockedFunds, etc
        
        DO NOT:
        - Directly edit the balance field, use fund_wallet and withdraw_from_wallet
            WHY:
            - To have a consistent history of transactions
            - To have a single point of failure
        - NEVER CALL `.fund_wallet()` or `.withdraw_from_wallet()` outside of an atomic transaction PLEASE EJO
            WHY:
            - If different processes try to update a users `balance` bro race conditions could occur, LOCKING the Wallet table row with Atomic transactions will prevent this.
    """
    
    class WalletStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        SUSPENDED = 'suspended', 'Suspended'
        CLOSED = 'closed', 'Closed'
        
    class WalletType(models.TextChoices):
        MAIN = 'main', 'Main Wallet'
        SAVINGS = 'savings', 'Savings Wallet'
        LOCKED = 'locked', 'Locked Funds'
        # GOAL = 'goal', 'Goal Savings'  # Dreamia I'm comming baby
        # BONUS = 'bonus', 'Bonus Wallet'
    
    class Meta:
        indexes = [
            models.Index(fields=["user"])
        ]
        constraints = [ # database constraints
            models.CheckConstraint(check=models.Q(balance__gte=0), name='wallet_balance_non_negative'),
            models.UniqueConstraint(fields=['user', 'wallet_type'], name='unique_wallet_per_user_type'),
        ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='wallets')
    wallet_name = models.CharField(max_length=255, default="User_Default_Wallet")
    
    balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    status = models.CharField(
        max_length=15,
        choices=WalletStatus.choices,
        default=WalletStatus.ACTIVE
    )
    wallet_type = models.CharField(
        max_length=20,
        choices=WalletType.choices,
        default=WalletType.MAIN
    )

    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    # MeToMany
    # - transactions: Transaction
    # - incoming_transfers: Transaction
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
    
    def fund_wallet(self, amount: str, to_save=True):
        # Use this in atomic transactions with select_for_update()
        self.balance += Decimal(amount)
        if to_save:
            self.save()
        
    def withdraw_from_wallet(self, amount: str, to_save=True):
        # Use this in atomic transactions with select_for_update()
        amount = Decimal(amount)
        if amount > self.balance:
            raise InsufficientFundsError()
        self.balance -= amount
        if to_save:
            self.save()
        
    def is_active(self):
        return self.status == self.WalletStatus.ACTIVE
    
    def is_suspended(self):
        return self.status == self.WalletStatus.SUSPENDED
    
    def is_closed(self):
        return self.status == self.WalletStatus.CLOSED
    
    def can_receive_funds(self):
        return self.is_active()
    
    def can_send_funds(self):
        return self.is_active()
