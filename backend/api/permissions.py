"""Custom permission classes for the Foodgram API application."""

from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """Permission class to allow editing objects only to their authors."""

    def has_object_permission(self, request, view, obj):
        """Allow object mutations only if the current user is the author."""
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user
