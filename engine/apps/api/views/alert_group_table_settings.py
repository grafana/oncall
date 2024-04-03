import typing

from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from apps.api.alert_group_table_columns import alert_group_table_user_settings
from apps.api.permissions import RBACPermission
from apps.api.serializers.alert_group_table_settings import (
    AlertGroupTableColumnsOrganizationSerializer,
    AlertGroupTableColumnsUserSerializer,
)
from apps.api.views.labels import LabelsFeatureFlagViewSet
from apps.auth_token.auth import PluginAuthentication
from apps.user_management.constants import default_columns
from apps.user_management.types import AlertGroupTableColumn


class AlertGroupTableColumnsViewSet(LabelsFeatureFlagViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "get_columns": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "update_user_columns": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "reset_user_columns": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "update_organization_columns": [RBACPermission.Permissions.OTHER_SETTINGS_WRITE],
    }

    def get_columns(self, request: Request) -> Response:
        return Response(alert_group_table_user_settings(request.user))

    def update_organization_columns(self, request: Request) -> Response:
        """add/remove columns for organization"""
        serializer = AlertGroupTableColumnsOrganizationSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        columns: typing.List[AlertGroupTableColumn] = serializer.validated_data.get(
            "visible", []
        ) + serializer.validated_data.get("hidden", [])
        request.auth.organization.update_alert_group_table_columns(columns)
        return Response(alert_group_table_user_settings(request.user))

    def update_user_columns(self, request: Request) -> Response:
        """select/hide/change order for user"""
        user = request.user
        serializer = AlertGroupTableColumnsUserSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        columns: typing.List[AlertGroupTableColumn] = serializer.validated_data.get("visible", [])
        user.update_alert_group_table_selected_columns(columns)
        return Response(alert_group_table_user_settings(user))

    def reset_user_columns(self, request: Request) -> Response:
        """set default alert group table settings for user"""
        user = request.user
        user.update_alert_group_table_selected_columns(default_columns())
        return Response(alert_group_table_user_settings(user))
