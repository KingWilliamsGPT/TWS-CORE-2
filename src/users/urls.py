from rest_framework.routers import SimpleRouter

from src.users.views import (
    UserViewSet,
    AuthRouterViewSet,
)

users_router = SimpleRouter()
users_router.register(r'users', UserViewSet, basename='users') # reverse('users-{list|create|action}', kwargs={'action': 'me'})


auth_router = SimpleRouter()
auth_router.register(r'auth', AuthRouterViewSet, basename='auth') # reverse('auth-{list|create|action}', kwargs={'action': 'login'})