from rest_framework.routers import SimpleRouter

from .views import (
    BankAccountViewSet,
)

bank_account_app_router = SimpleRouter()

bank_account_app_router.register(
    r"bank_account", BankAccountViewSet, basename="bank_account"
)
