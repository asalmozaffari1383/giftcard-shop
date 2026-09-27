class AdminRoleRequiredMixin:
    """Restrict sensitive admin models to verified marketplace administrators."""

    @staticmethod
    def _has_admin_role(request):
        user = request.user
        return bool(
            user.is_authenticated
            and user.is_active
            and user.is_staff
            and (user.is_superuser or (user.is_verified and user.is_admin))
        )

    def has_module_permission(self, request):
        return self._has_admin_role(request)

    def has_view_permission(self, request, obj=None):
        return self._has_admin_role(request)

    def has_add_permission(self, request):
        return self._has_admin_role(request) and super().has_add_permission(request)

    def has_change_permission(self, request, obj=None):
        return self._has_admin_role(request) and super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return self._has_admin_role(request) and super().has_delete_permission(request, obj)
