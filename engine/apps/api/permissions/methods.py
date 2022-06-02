from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet


class MethodPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: ViewSet) -> bool:
        for permission, methods in getattr(view, "method_permissions", {}).items():
            if request.method in methods:
                return permission().has_permission(request, view)

        return False
