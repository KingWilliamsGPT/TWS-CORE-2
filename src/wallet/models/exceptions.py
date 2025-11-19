from django.core.exceptions import ValidationError

class FinanceError(ValidationError):
    pass

class InsufficientFundsError(FinanceError):
    pass

class ImmutableError(FinanceError):
    pass

class InvalidTransaction(FinanceError):
    """When a Transaction instance has improper fields."""