from rest_framework.routers import SimpleRouter

from .views import (
    PaystackViewSet,
)

paystack_app_router = SimpleRouter()

paystack_app_router.register(r'paystack', PaystackViewSet, basename='paystack')
