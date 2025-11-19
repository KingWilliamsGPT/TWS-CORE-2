from rest_framework.routers import SimpleRouter

from .views import (
    OrderViewSet,
)

order_app_router = SimpleRouter()

order_app_router.register(r"order", OrderViewSet, basename="order")
