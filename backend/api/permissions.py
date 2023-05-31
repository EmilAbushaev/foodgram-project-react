from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешение для администратора или чтение для всех"""

    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS or (
            request.user.is_authenticated
            and (request.user.is_admin or request.user.is_superuser)
        )


class IsAdminAuthorOrReadOnly(permissions.IsAuthenticatedOrReadOnly):
    """Разрешение для администратора или автора, остальным чтение"""
    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or (request.user == obj.author)
                or request.user.is_staff)
