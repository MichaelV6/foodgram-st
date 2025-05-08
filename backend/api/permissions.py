from rest_framework.permissions import (
    SAFE_METHODS,
    IsAuthenticated,
)

from users.models import User


class IsAuthorOrReadOnly(IsAuthenticated):
    def has_object_permission(self, request, view, obj):
        return request.method in SAFE_METHODS or obj.author == request.user

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or isinstance(request.user, User)
