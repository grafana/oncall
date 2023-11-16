from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.api.permissions import RBACPermission
from apps.api.serializers.alert_group_table_settings import AlertGroupTableColumnsListSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.user_management.utils import alert_group_table_user_settings


class AlertGroupTableColumnsViewSet(ViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "get_columns": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "update_columns_settings": [RBACPermission.Permissions.ALERT_GROUPS_READ],
        "update_columns_list": [RBACPermission.Permissions.OTHER_SETTINGS_WRITE],
    }

    def get_columns(self, request):
        user = request.user
        return Response(alert_group_table_user_settings(user))

    def update_columns_list(self, request):
        """add/remove columns for organization"""
        user = request.user
        organization = request.auth.organization
        serializer = AlertGroupTableColumnsListSerializer(
            data=request.data, context={"request": request, "is_org_settings": True}
        )
        serializer.is_valid(raise_exception=True)
        columns = [column for column in request.data.get("visible", [])] + [
            column for column in request.data.get("hidden", [])
        ]
        organization.update_alert_group_table_columns(columns)
        return Response(alert_group_table_user_settings(user))

    def update_columns_settings(self, request):
        """select/hide/change order for user"""
        user = request.user
        serializer = AlertGroupTableColumnsListSerializer(
            data=request.data, context={"request": request, "is_org_settings": False}
        )
        serializer.is_valid(raise_exception=True)
        columns = [column for column in request.data.get("visible", [])]
        user.update_alert_group_table_columns_settings(columns)
        return Response(alert_group_table_user_settings(user))
