"""Object-level permissions for notes, categories, and tags."""

from typing import Any

from django.utils import timezone
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.views import APIView


class IsOwner(permissions.BasePermission):
    """Permission allowing access only to the user who owns the object."""

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        """Check if request user matches object's owner user attribute."""
        if not request.user or not request.user.is_authenticated:
            return False
        return bool(obj.user == request.user)


class IsOwnerOrSharedReadOnly(permissions.BasePermission):
    """Permission allowing public read access to active shared notes."""

    def has_object_permission(self, request: Request, view: APIView, obj: Any) -> bool:
        """Allow read access if note is shared and unexpired, else require ownership."""
        if request.method in permissions.SAFE_METHODS and getattr(obj, "is_shared", False):
            expires_at = getattr(obj, "share_expires_at", None)
            if expires_at is None or expires_at > timezone.now():
                return True

        if not request.user or not request.user.is_authenticated:
            return False

        return bool(obj.user == request.user)
