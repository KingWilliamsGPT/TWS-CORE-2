from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        """If this is a GET/HEAD/OPTIONS request OR the user is authenticated, allow access."""

        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


class IsVerifiedUser(permissions.BasePermission):

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if not request.user.is_active:
            raise PermissionDenied(
                {
                    "message": "You need to complete the onboarding process to perform this action.",
                    "details": {
                        "onboarding_status": request.user.onboarding_status,
                        "onboarding_flow": request.user.get_onboarding_flow(),
                    },
                    "code": "onboarding_incomplete",
                }
            )
        
        if not request.user.is_onboarding_complete():
            raise PermissionDenied(
                {
                    "errors": [
                        {
                            "message": "You need to complete the onboarding process to perform this action.",
                            "details": {
                                "onboarding_status": request.user.onboarding_status,
                                "onboarding_flow": request.user.get_onboarding_flow(),
                            },
                            "code": "onboarding_incomplete",
                        }
                    ]
                }
            )

        return True


class IsVerifiedAdminUser(IsVerifiedUser):
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        if not request.user.is_staff:
            raise PermissionDenied(
                {
                    "errors": [
                        {
                            "message": "You do not have permission to perform this action.",
                            "code": "not_admin",
                        }
                    ]
                }
            )

        return True
