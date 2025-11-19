# import os

# import django
# from django.core.asgi import get_asgi_application
# from channels.routing import ProtocolTypeRouter, URLRouter
# from channels.auth import AuthMiddlewareStack

# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "src.config.local")

# django.setup()
# from src.chats import routing 


# application = ProtocolTypeRouter({
#     "http": get_asgi_application(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(routing.websocket_urlpatterns)
#     ),
# })


import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.config.local')

django_app = get_asgi_application()
from src.chats import routing 

class DebugMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        if scope["type"] == "websocket":
            print("INCOMING WEBSOCKET PATH:", scope["path"])
        return await self.inner(scope, receive, send)

application = ProtocolTypeRouter({
    "http": django_app,
    "websocket": DebugMiddleware(
        AuthMiddlewareStack(
            URLRouter(routing.websocket_urlpatterns)
        )
    ),
})

