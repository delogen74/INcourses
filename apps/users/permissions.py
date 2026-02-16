from rest_framework.permissions import BasePermission

from .models import UserRole


class IsOwnerOrEditor(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role in {UserRole.OWNER, UserRole.EDITOR})


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == UserRole.OWNER)


class HasServiceScope(BasePermission):
    required_scope = None

    def has_permission(self, request, view):
        token = getattr(request, 'service_token', None)
        return bool(token and self.required_scope in token.scopes)
