from typing import Any

from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.viewsets import ViewSet


class ActionPermission(permissions.BasePermission):
    def has_permission(self, request: Request, view: ViewSet) -> bool:
        for permission, actions in getattr(view, "action_permissions", {}).items():
            if view.action in actions:
                return permission().has_permission(request, view)

        return False

    def has_object_permission(self, request: Request, view: ViewSet, obj: Any) -> bool:
        # action_object_permissions attr should be used in case permission check require lookup
        # for some object's properties e.g. team.
        if getattr(view, "action_object_permissions", None):
            for permission, actions in getattr(view, "action_object_permissions", {}).items():
                if view.action in actions:
                    return permission().has_object_permission(request, view, obj)
            return False
        else:
            # has_object_permission is called after has_permission, so return True if in view there is not
            # action_object_permission attr which mean no additional check involving object required
            return True
