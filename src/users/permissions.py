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
        errors = []
        for _ in range(1):
            if request.user.is_anonymous:
                errors.append(
                    {
                        "message": "Authentication credentials were not provided.",
                        "code": "not_authenticated",
                    }
                )
                break
            if not request.user.is_email_verified:
                errors.append(
                    {
                        "message": "Email not verified.",
                        "code": "email_not_verified",
                    }
                )
            # if not request.user.is_phone_number_verified:
            #     errors.append(
            #         {
            #             "message": "Phone number not verified.",
            #             "code": "phone_number_not_verified",
            #         }
            #     )
            if not request.user.is_active:
                errors.append(
                    {
                        "message": "User account is disabled.",
                        "code": "user_inactive",
                    }
                )
            break

        if errors:
            raise PermissionDenied({"errors": errors})

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
