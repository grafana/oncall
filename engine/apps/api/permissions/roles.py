from typing import Any

from rest_framework import permissions
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet

from common.constants.role import Role


class RolePermission(permissions.BasePermission):
    ROLE = None

    def has_permission(self, request: Request, view: ViewSet) -> bool:
        return request.user.role == type(self).ROLE

    def has_object_permission(self, request: Request, view: ViewSet, obj: Any) -> bool:
        return self.has_permission(request, view)


class IsAdmin(RolePermission):
    ROLE = Role.ADMIN


class IsEditor(RolePermission):
    ROLE = Role.EDITOR


class IsViewer(RolePermission):
    ROLE = Role.VIEWER


IsAdminOrEditor = IsAdmin | IsEditor
AnyRole = IsAdmin | IsEditor | IsViewer


class IsStaff(permissions.BasePermission):
    STAFF_AUTH_CLASSES = [BasicAuthentication, SessionAuthentication]

    def has_permission(self, request: Request, view: ViewSet) -> bool:
        user = request.user
        if not any(isinstance(request._authenticator, x) for x in self.STAFF_AUTH_CLASSES):
            return False
        if user and user.is_authenticated:
            return user.is_staff
        return False

    def has_object_permission(self, request: Request, view: ViewSet, obj: Any) -> bool:
        return self.has_permission(request, view)
