import uuid
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator
from .exceptions import InvalidTransaction


_Wallet = "wallet.Wallet"


class TransactionQuerySet(models.QuerySet):
    def withdrawals(self):
        return self.filter(transaction_type=Transaction.TransactionType.WITHDRAWAL)

    def successful(self):
        return self.filter(status=Transaction.TransactionStatus.SUCCESS)


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        DEPOSIT = 'deposit', 'Deposit'
        WITHDRAWAL = 'withdrawal', 'Withdrawal'
        TRANSFER = 'transfer', 'Transfer'
        
    class TransactionStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        REVERSED = 'reversed', 'Reversed'
    
    class TransactionSource(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        API = 'api', 'API'
        SYSTEM = 'system', 'System'
        WEBHOOK = 'webhook', 'Webhook'
    
    class Meta:
        constraints = [ # database constraints
            models.CheckConstraint(check=models.Q(amount__gte=0), name='transaction_amount_non_negative'),
        ]
        indexes = [
            models.Index(fields=["wallet", "transaction_type", "created_at"]),
            models.Index(fields=["reference"]),
        ]
        ordering = ['-created_at']
    
    objects = TransactionQuerySet.as_manager()
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    wallet = models.ForeignKey(_Wallet, on_delete=models.CASCADE, related_name='transactions')
    
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    transaction_type = models.CharField(
        max_length=15,
        choices=TransactionType.choices,
        default=TransactionType.DEPOSIT,
    )
    status = models.CharField(
        max_length=10,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
    )
    narration = models.TextField(blank=True)
    reference = models.CharField(max_length=100, unique=True)  # for webhook referencing
    receiver = models.ForeignKey(  # Optional sha for in app transfers
        _Wallet,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='incoming_transfers'
    )
    # FOR REVERSED TRANSACTIONS
    is_reversal = models.BooleanField(default=False)
    reversed_from = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='reversal'
    )
    # TO TRACK WHERE THE TRANSACTION CAME FROM
    source = models.CharField(
        max_length=10,
        choices=TransactionSource.choices,
        default=TransactionSource.SYSTEM
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    metadata = models.JSONField(default=dict, blank=True)

    def save(self, *args, **kwargs):
        # self.full_clean() #->.clean() # DON'T CALL HERE, slows down BULK operations
        if not self.reference:
            self.reference = str(uuid.uuid4())
        super().save(*args, **kwargs)
        
    def clean(self):
        if self.transaction_type == self.TransactionType.TRANSFER and not self.receiver:
            raise InvalidTransaction("Transfers must have a receiver.")
    
    def __str__(self):
        return f"<Txn {self.reference}: {self.transaction_type} ₦{self.amount} ({self.status})>"
