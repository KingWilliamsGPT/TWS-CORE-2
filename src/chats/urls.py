from rest_framework.routers import SimpleRouter

from .views import (
    ChatViewSet,
)

chat_app_router = SimpleRouter()

chat_app_router.register(r"chat", ChatViewSet, basename="chat")
