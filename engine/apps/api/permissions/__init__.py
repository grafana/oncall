import enum
import typing

from django.conf import settings
from rest_framework import permissions
from rest_framework.authentication import BasicAuthentication, SessionAuthentication
from rest_framework.request import Request
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ViewSetMixin

from common.utils import getattrd

ACTION_PREFIX = "grafana-oncall-app"
RBAC_PERMISSIONS_ATTR = "rbac_permissions"
RBAC_OBJECT_PERMISSIONS_ATTR = "rbac_object_permissions"

ViewSetOrAPIView = typing.Union[ViewSet, APIView]


class GrafanaAPIPermission(typing.TypedDict):
    action: str


class Resources(enum.Enum):
    ALERT_GROUPS = "alert-groups"
    INTEGRATIONS = "integrations"
    ESCALATION_CHAINS = "escalation-chains"
    SCHEDULES = "schedules"
    CHATOPS = "chatops"
    OUTGOING_WEBHOOKS = "outgoing-webhooks"
    MAINTENANCE = "maintenance"
    API_KEYS = "api-keys"
    NOTIFICATIONS = "notifications"

    NOTIFICATION_SETTINGS = "notification-settings"
    USER_SETTINGS = "user-settings"
    OTHER_SETTINGS = "other-settings"


class Actions(enum.Enum):
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    TEST = "test"
    EXPORT = "export"
    UPDATE_SETTINGS = "update-settings"


class LegacyAccessControlRole(enum.IntEnum):
    ADMIN = 0
    EDITOR = 1
    VIEWER = 2

    @classmethod
    def choices(cls):
        return tuple((option.value, option.name) for option in cls)


class LegacyAccessControlCompatiblePermission:
    def __init__(self, resource: Resources, action: Actions, fallback_role: LegacyAccessControlRole) -> None:
        self.value = f"{ACTION_PREFIX}.{resource.value}:{action.value}"
        self.fallback_role = fallback_role


def get_most_authorized_role(
    permissions: typing.List[LegacyAccessControlCompatiblePermission],
) -> LegacyAccessControlRole:
    if not permissions:
        return LegacyAccessControlRole.VIEWER

    # ex. Admin is 0, Viewer is 2, thereby min makes sense here
    return min({p.fallback_role for p in permissions}, key=lambda r: r.value)


def user_is_authorized(user, required_permissions: typing.List[LegacyAccessControlCompatiblePermission]) -> bool:
    """
    This function checks whether `user` has all permissions in `required_permissions`. RBAC permissions are used
    if RBAC is enabled for the organization, otherwise the fallback basic role is checked.

    Parameters
    ----------
    user : apps.user_management.models.user.User
        The user to check permissions for
    required_permissions : typing.List[LegacyAccessControlCompatiblePermission]
        A list of permissions that a user must have to be considered authorized
    """
    if user.organization.is_rbac_permissions_enabled:
        user_permissions = [u["action"] for u in user.permissions]
        required_permissions = [p.value for p in required_permissions]
        return all(permission in user_permissions for permission in required_permissions)
    return user.role <= get_most_authorized_role(required_permissions).value


class RBACPermission(permissions.BasePermission):
    class Permissions:
        ALERT_GROUPS_READ = LegacyAccessControlCompatiblePermission(
            Resources.ALERT_GROUPS, Actions.READ, LegacyAccessControlRole.VIEWER
        )
        ALERT_GROUPS_WRITE = LegacyAccessControlCompatiblePermission(
            Resources.ALERT_GROUPS, Actions.WRITE, LegacyAccessControlRole.EDITOR
        )

        INTEGRATIONS_READ = LegacyAccessControlCompatiblePermission(
            Resources.INTEGRATIONS, Actions.READ, LegacyAccessControlRole.VIEWER
        )
        INTEGRATIONS_TEST = LegacyAccessControlCompatiblePermission(
            Resources.INTEGRATIONS, Actions.TEST, LegacyAccessControlRole.EDITOR
        )
        INTEGRATIONS_WRITE = LegacyAccessControlCompatiblePermission(
            Resources.INTEGRATIONS, Actions.WRITE, LegacyAccessControlRole.ADMIN
        )

        ESCALATION_CHAINS_READ = LegacyAccessControlCompatiblePermission(
            Resources.ESCALATION_CHAINS, Actions.READ, LegacyAccessControlRole.VIEWER
        )
        ESCALATION_CHAINS_WRITE = LegacyAccessControlCompatiblePermission(
            Resources.ESCALATION_CHAINS, Actions.WRITE, LegacyAccessControlRole.ADMIN
        )

        SCHEDULES_READ = LegacyAccessControlCompatiblePermission(
            Resources.SCHEDULES, Actions.READ, LegacyAccessControlRole.VIEWER
        )
        SCHEDULES_WRITE = LegacyAccessControlCompatiblePermission(
            Resources.SCHEDULES, Actions.WRITE, LegacyAccessControlRole.EDITOR
        )
        SCHEDULES_EXPORT = LegacyAccessControlCompatiblePermission(
            Resources.SCHEDULES, Actions.EXPORT, LegacyAccessControlRole.EDITOR
        )

        CHATOPS_READ = LegacyAccessControlCompatiblePermission(
            Resources.CHATOPS, Actions.READ, LegacyAccessControlRole.VIEWER
        )
        CHATOPS_WRITE = LegacyAccessControlCompatiblePermission(
            Resources.CHATOPS, Actions.WRITE, LegacyAccessControlRole.EDITOR
        )
        CHATOPS_UPDATE_SETTINGS = LegacyAccessControlCompatiblePermission(
            Resources.CHATOPS, Actions.UPDATE_SETTINGS, LegacyAccessControlRole.ADMIN
        )

        OUTGOING_WEBHOOKS_READ = LegacyAccessControlCompatiblePermission(
            Resources.OUTGOING_WEBHOOKS, Actions.READ, LegacyAccessControlRole.VIEWER
        )
        OUTGOING_WEBHOOKS_WRITE = LegacyAccessControlCompatiblePermission(
            Resources.OUTGOING_WEBHOOKS, Actions.WRITE, LegacyAccessControlRole.ADMIN
        )

        MAINTENANCE_READ = LegacyAccessControlCompatiblePermission(
            Resources.MAINTENANCE, Actions.READ, LegacyAccessControlRole.VIEWER
        )
        MAINTENANCE_WRITE = LegacyAccessControlCompatiblePermission(
            Resources.MAINTENANCE, Actions.WRITE, LegacyAccessControlRole.EDITOR
        )

        API_KEYS_READ = LegacyAccessControlCompatiblePermission(
            Resources.API_KEYS, Actions.READ, LegacyAccessControlRole.ADMIN
        )
        API_KEYS_WRITE = LegacyAccessControlCompatiblePermission(
            Resources.API_KEYS, Actions.WRITE, LegacyAccessControlRole.ADMIN
        )

        NOTIFICATIONS_READ = LegacyAccessControlCompatiblePermission(
            Resources.NOTIFICATIONS, Actions.READ, LegacyAccessControlRole.EDITOR
        )

        NOTIFICATION_SETTINGS_READ = LegacyAccessControlCompatiblePermission(
            Resources.NOTIFICATION_SETTINGS, Actions.READ, LegacyAccessControlRole.VIEWER
        )
        NOTIFICATION_SETTINGS_WRITE = LegacyAccessControlCompatiblePermission(
            Resources.NOTIFICATION_SETTINGS, Actions.WRITE, LegacyAccessControlRole.EDITOR
        )

        USER_SETTINGS_READ = LegacyAccessControlCompatiblePermission(
            Resources.USER_SETTINGS, Actions.READ, LegacyAccessControlRole.VIEWER
        )
        USER_SETTINGS_WRITE = LegacyAccessControlCompatiblePermission(
            Resources.USER_SETTINGS, Actions.WRITE, LegacyAccessControlRole.EDITOR
        )
        USER_SETTINGS_ADMIN = LegacyAccessControlCompatiblePermission(
            Resources.USER_SETTINGS, Actions.ADMIN, LegacyAccessControlRole.ADMIN
        )

        OTHER_SETTINGS_READ = LegacyAccessControlCompatiblePermission(
            Resources.OTHER_SETTINGS, Actions.READ, LegacyAccessControlRole.VIEWER
        )
        OTHER_SETTINGS_WRITE = LegacyAccessControlCompatiblePermission(
            Resources.OTHER_SETTINGS, Actions.WRITE, LegacyAccessControlRole.ADMIN
        )

    @staticmethod
    def _get_view_action(request: Request, view: ViewSetOrAPIView) -> str:
        """
        For right now this needs to support being used in both a ViewSet as well as APIView, we use both interchangably

        Note: `request.method` is returned uppercase
        """
        return view.action if isinstance(view, ViewSetMixin) else request.method.lower()

    def has_permission(self, request: Request, view: ViewSetOrAPIView) -> bool:
        # the django-debug-toolbar UI makes OPTIONS calls. Without this statement the debug UI can't gather the
        # necessary info it needs to work properly
        if settings.DEBUG and request.method == "OPTIONS":
            return True

        action = self._get_view_action(request, view)

        rbac_permissions: RBACPermissionsAttribute = getattr(view, RBAC_PERMISSIONS_ATTR, None)

        # first check that the rbac_permissions dict attribute is defined
        assert (
            rbac_permissions is not None
        ), f"Must define a {RBAC_PERMISSIONS_ATTR} dict on the ViewSet that is consuming the RBACPermission class"

        action_required_permissions: typing.Union[None, typing.List] = rbac_permissions.get(action, None)

        # next check that the action in question is defined within the rbac_permissions dict attribute
        assert (
            action_required_permissions is not None
        ), f"""Each action must be defined within the {RBAC_PERMISSIONS_ATTR} dict on the ViewSet.
\nIf an action requires no permissions, its value should explicitly be set to an empty list"""

        return user_is_authorized(request.user, action_required_permissions)

    def has_object_permission(self, request: Request, view: ViewSetOrAPIView, obj: typing.Any) -> bool:
        rbac_object_permissions: RBACObjectPermissionsAttribute = getattr(view, RBAC_OBJECT_PERMISSIONS_ATTR, None)

        if rbac_object_permissions:
            action = self._get_view_action(request, view)

            for permission_class, actions in rbac_object_permissions.items():
                if action in actions:
                    return permission_class.has_object_permission(request, view, obj)
            return False

        # has_object_permission is called after has_permission, so return True if in view there is not
        # RBAC_OBJECT_PERMISSIONS_ATTR attr which mean no additional check involving object required
        return True


class IsOwner(permissions.BasePermission):
    def __init__(self, ownership_field: typing.Optional[str] = None) -> None:
        self.ownership_field = ownership_field

    def has_object_permission(self, request: Request, _view: ViewSet, obj: typing.Any) -> bool:
        owner = obj if self.ownership_field is None else getattrd(obj, self.ownership_field)
        return owner == request.user


class HasRBACPermissions(permissions.BasePermission):
    def __init__(self, required_permissions: typing.List[LegacyAccessControlCompatiblePermission]) -> None:
        self.required_permissions = required_permissions

    def has_object_permission(self, request: Request, _view: ViewSetOrAPIView, _obj: typing.Any) -> bool:
        return user_is_authorized(request.user, self.required_permissions)


class IsOwnerOrHasRBACPermissions(permissions.BasePermission):
    def __init__(
        self,
        required_permissions: typing.List[LegacyAccessControlCompatiblePermission],
        ownership_field: typing.Optional[str] = None,
    ) -> None:
        self.IsOwner = IsOwner(ownership_field)
        self.HasRBACPermissions = HasRBACPermissions(required_permissions)

    def has_object_permission(self, request: Request, view: ViewSetOrAPIView, obj: typing.Any) -> bool:
        return self.IsOwner.has_object_permission(request, view, obj) or self.HasRBACPermissions.has_object_permission(
            request, view, obj
        )


class IsStaff(permissions.BasePermission):
    STAFF_AUTH_CLASSES = [BasicAuthentication, SessionAuthentication]

    def has_permission(self, request: Request, _view: ViewSet) -> bool:
        user = request.user
        if not any(isinstance(request._authenticator, x) for x in self.STAFF_AUTH_CLASSES):
            return False
        if user and user.is_authenticated:
            return user.is_staff
        return False


RBACPermissionsAttribute = typing.Dict[str, typing.List[LegacyAccessControlCompatiblePermission]]
RBACObjectPermissionsAttribute = typing.Dict[permissions.BasePermission, typing.List[str]]


# The below is legacy, it is only needed currently for backward compatibility w/ users running
# older "pinned" version of Grafana in Grafana Cloud
_DONT_USE_LEGACY_VIEWER_PERMISSIONS = []
_DONT_USE_LEGACY_EDITOR_PERMISSIONS = ["update_incidents", "update_own_settings", "view_other_users"]
_DONT_USE_LEGACY_ADMIN_PERMISSIONS = _DONT_USE_LEGACY_EDITOR_PERMISSIONS + [
    "update_alert_receive_channels",
    "update_escalation_policies",
    "update_notification_policies",
    "update_general_log_channel_id",
    "update_other_users_settings",
    "update_integrations",
    "update_schedules",
    "update_custom_actions",
    "update_api_tokens",
    "update_teams",
    "update_maintenances",
    "update_global_settings",
    "send_demo_alert",
]

DONT_USE_LEGACY_PERMISSION_MAPPING: typing.Dict[LegacyAccessControlRole, typing.List[str]] = {
    LegacyAccessControlRole.VIEWER: _DONT_USE_LEGACY_VIEWER_PERMISSIONS,
    LegacyAccessControlRole.EDITOR: _DONT_USE_LEGACY_EDITOR_PERMISSIONS,
    LegacyAccessControlRole.ADMIN: _DONT_USE_LEGACY_ADMIN_PERMISSIONS,
}
