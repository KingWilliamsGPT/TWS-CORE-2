from rest_framework.routers import SimpleRouter

from src.users.views import (
    UserViewSet,
)

users_router = SimpleRouter()

users_router.register(r'users', UserViewSet, basename='users') # reverse('users-{list|create|action}', kwargs={'action': 'me'})
