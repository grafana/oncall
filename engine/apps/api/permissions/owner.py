from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet

from apps.api.permissions.roles import IsAdmin, IsEditor
from common.utils import getattrd


class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request: Request, view: ViewSet, obj: Any) -> bool:
        ownership_field = getattr(view, "ownership_field", None)
        if ownership_field is None:
            owner = obj
        else:
            owner = getattrd(obj, ownership_field)

        return owner == request.user


IsOwnerOrAdmin = IsOwner | IsAdmin

IsOwnerOrAdminOrEditor = IsOwner | IsAdmin | IsEditor
