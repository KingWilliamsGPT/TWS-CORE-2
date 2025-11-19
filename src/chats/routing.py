from django.urls import path
from .consumers import AppConsumer

websocket_urlpatterns = [
    path("api/v1/ws/", AppConsumer.as_asgi()),
]
