from rest_framework.routers import SimpleRouter

from .views import (
    WalletViewSet,
)

wallet_router = SimpleRouter()

wallet_router.register(r'wallets', WalletViewSet, basename='wallets')
