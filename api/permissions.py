from rest_framework.permissions import BasePermission, SAFE_METHODS


class RolePermission(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_superuser', False):
            return True

        role = getattr(user, 'role', None)
        if request.method in SAFE_METHODS:
            allowed = getattr(view, 'read_roles', None)
            return True if allowed is None else role in allowed

        allowed = getattr(view, 'write_roles', None)
        return False if allowed is None else role in allowed


class IsAdminOrSelf(BasePermission):
    """Allow admins or users to access their own records."""

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_superuser', False) or getattr(user, 'role', None) == 'ADMIN':
            return True
        return getattr(obj, 'pk', None) == getattr(user, 'pk', None)
