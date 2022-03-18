from rest_framework import permissions

from src.models.models import UserTypes


class IsUserOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        return obj == request.user


class IsCarMerchantAndAuthed(permissions.BasePermission):

    def has_permission(self, request, view):
        dd = request.user.is_staff and request.user.is_superuser and request.user.user_type == UserTypes.Admin
        return not dd and request.user.is_authenticated


