from rest_framework.routers import SimpleRouter

from .views import (
    NotificationViewSet,
)

notification_app_router = SimpleRouter()

notification_app_router.register(
    r"notification", NotificationViewSet, basename="notification"
)
