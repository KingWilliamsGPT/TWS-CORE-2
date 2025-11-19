from rest_framework.routers import SimpleRouter

from .views import (
    ProductViewSet,
)

product_app_router = SimpleRouter()

product_app_router.register(r"product", ProductViewSet, basename="product")
