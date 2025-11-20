from django.conf import settings
from django.urls import path, re_path, include, reverse_lazy
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from rest_framework.routers import DefaultRouter


# from drf_yasg.views import get_schema_view
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from django.urls.resolvers import URLPattern, URLResolver
from django.utils.decorators import method_decorator
import django_rest_passwordreset.urls as drpr_urls
from django_rest_passwordreset.views import (
    ResetPasswordValidateToken,
    ResetPasswordConfirm,
    ResetPasswordRequestToken,
)

from src.users.auth import (
    TokenPairView__FirstFactor,
    TokenPairView__SecondFactor,
    RefreshTokenView,
)
from src.common.views import HealthCheckView
from src.social.views import exchange_token, complete_twitter_login
from src.files.urls import files_router
from src.users.urls import users_router, auth_router

# from src.common.urls import common_router
from src.wallet.urls import wallet_router
from src.paystack_app.urls import paystack_app_router
from src.bank_account_app.urls import bank_account_app_router
from src.notifications.urls import notification_app_router
from src.orders.urls import order_app_router
from src.products.urls import product_app_router
from src.chats.urls import chat_app_router


def tag_viewset(viewset_class, tag_name):
    """Apply Spectacular tags to all actions in a ViewSet."""
    actions = ["list", "create", "retrieve", "update", "partial_update", "destroy"]

    schema_kwargs = {a: extend_schema(tags=[tag_name]) for a in actions}
    viewset_class = extend_schema_view(**schema_kwargs)(viewset_class)

    # Handle @action-decorated custom methods
    for method_name in dir(viewset_class):
        method = getattr(viewset_class, method_name)
        if hasattr(method, "mapping"):  # identifies @action methods
            decorated = extend_schema(tags=[tag_name])
            viewset_class = extend_schema_view(**{method_name: decorated})(
                viewset_class
            )

    return viewset_class


def tag_router(router, tag_name):
    """Tags all viewsets in a router"""
    new_registry = []
    for prefix, viewset, basename in router.registry:
        tagged_viewset = tag_viewset(viewset, tag_name)
        new_registry.append((prefix, tagged_viewset, basename))
    router.registry = new_registry
    return router


sub_routers = [
    [users_router, "user"],
    [auth_router, "auth"],
    [files_router, "files"],
    # [common_router, "common"],
    [notification_app_router, "notifications"],
    [order_app_router, "orders"],
    [product_app_router, "products"],
    [chat_app_router, "chats"],
    [wallet_router, "wallets"],
    [paystack_app_router, "paystack"],
    [bank_account_app_router, "bank_account"],
]


router = DefaultRouter()

# router.registry.extend(users_router.registry)
# router.registry.extend(files_router.registry)
# router.registry.extend(common_router.registry)

for r in sub_routers:
    sub_router = tag_router(r[0], r[1])
    router.registry.extend(sub_router.registry)


def tag_endpoint(tag_name, view):
    """
    USECASE:
    >>> # class based view
    >>> path("my-endpoint/", tag_endpoint("mytag", MyView.as_view()))
    >>> # function based view
    >>> path("my-endpoint/", tag_endpoint("mytag", my_view_function))
    """
    return extend_schema(tags=[tag_name])(view)

@extend_schema(tags=["auth"])
class MyResetPasswordRequestToken(ResetPasswordRequestToken):
    pass

@extend_schema(tags=["auth"])
class MyResetPasswordValidateToken(ResetPasswordValidateToken):
    pass

@extend_schema(tags=["auth"])
class MyResetPasswordConfirm(ResetPasswordConfirm):
    pass


urlpatterns = [
    # admin panel
    # path('admin/', admin.site.urls),    # disable the django admin site
    # path('jet/', include('jet.urls')),  # Updated from url() to path()
    # summernote editor
    path("summernote/", include("django_summernote.urls")),
    # api
    path("api/v1/", include(router.urls)),
    # path(
    #     "api/v1/auth/password_reset/",
    #     include("django_rest_passwordreset.urls", namespace="password_reset"),
    # ),  
    path(
        "api/v1/auth/password/reset/",
        MyResetPasswordRequestToken.as_view(),
        name="password_reset",
    ),
    path(
        "api/v1/auth/password/reset/validate_token/",
        MyResetPasswordValidateToken.as_view(),
        name="password_reset_validate_token",
    ),
    path(
        "api/v1/auth/password/reset/confirm/",
        MyResetPasswordConfirm.as_view(),
        name="password_reset_confirm",
    ),
    # auth
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path(
        "api/v1/auth/login/1stfactor/",
        TokenPairView__FirstFactor.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/v1/auth/login/2ndfactor/",
        TokenPairView__SecondFactor.as_view(),
        name="token_obtain_pair2",
    ),
    path(
        "api/v1/auth/login/refresh/", RefreshTokenView.as_view(), name="token_refresh"
    ),
    # social login
    path("", include("social_django.urls", namespace="social")),  # Updated
    path(
        "api/v1/auth/social/complete/twitter/",
        tag_endpoint("auth", complete_twitter_login),
    ),
    re_path(
        r"^api/v1/auth/social/(?P<backend>[^/]+)/$",
        tag_endpoint("auth", exchange_token),
    ),
    # OpenAPI schema endpoint
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    # Swagger UI
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    # Redoc UI (optional)
    path("api/redocs/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("health/", HealthCheckView.as_view(), name="health-check"), 
    path("health/stats", include("health_check.urls")),
    # the 'api-root' from django rest-frameworks default router
    re_path(r"^$", RedirectView.as_view(url=reverse_lazy("api-root"), permanent=False)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
