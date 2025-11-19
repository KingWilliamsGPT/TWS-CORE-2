from django.conf import settings
from django.db import models
from django.utils import timezone

from .banks_enum import Banks, banks


class BankAccount(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bank_accounts",
        db_index=True,
    )
    bank_code = models.CharField(
        max_length=20,
        choices=Banks.choices,
        db_index=True,
    )
    account_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique account number as provided by the bank",
    )
    account_name = models.CharField(
        max_length=255,
        help_text="Account holder's full name as registered with the bank",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Mark if this is the user's default bank account",
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Indicates if the bank belongs to the user and has been verified",
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "bank_code", "account_number"],
                name="unique_user_bank_account",
            )
        ]

    def get_bank_display(self):
        return banks.get(self.bank_code, ["Unknown Bank", "UNKNOWN_BANK"])[0]

    def __str__(self):
        return (
            f"{self.account_name} - {self.get_bank_display()} ({self.account_number})"
        )
