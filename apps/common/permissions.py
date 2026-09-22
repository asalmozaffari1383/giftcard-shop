from rest_framework.permissions import BasePermission


class IsStaffRole(BasePermission):
    """Support/admin API access, not merely a self-reported role."""

    def has_permission(self, request, view):
        return bool(request.user.is_authenticated and request.user.is_active and
                    request.user.is_verified and request.user.is_staff and
                    (request.user.is_support or request.user.is_admin))


class IsAdminRole(IsStaffRole):
    def has_permission(self, request, view):
        return super().has_permission(request, view) and request.user.is_admin
