from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import RBACPermission
from apps.auth_token.auth import PluginAuthentication
from apps.base.models import LiveSetting
from apps.base.utils import live_settings
from apps.oss_installation.cloud_heartbeat import get_heartbeat_link
from apps.oss_installation.models import CloudConnector, CloudHeartbeat


class CloudConnectionView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)
    rbac_permissions = {
        "get": [RBACPermission.Permissions.OTHER_SETTINGS_READ],
        "delete": [RBACPermission.Permissions.OTHER_SETTINGS_WRITE],
    }

    def get(self, request):
        connector = CloudConnector.objects.first()
        heartbeat = CloudHeartbeat.objects.first()
        response = {
            "cloud_connection_status": connector is not None,
            "cloud_notifications_enabled": live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED,
            "cloud_heartbeat_enabled": live_settings.GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED,
            "cloud_heartbeat_link": get_heartbeat_link(connector, heartbeat),
            "cloud_heartbeat_status": heartbeat is not None and heartbeat.success,
        }
        return Response(response)

    def delete(self, request):
        s = LiveSetting.objects.filter(name="GRAFANA_CLOUD_ONCALL_TOKEN").first()
        if s is not None:
            s.value = None
            s.save()
        connector = CloudConnector.objects.first()
        if connector is None:
            return Response(status=status.HTTP_404_NOT_FOUND)
        connector.remove_sync()
        return Response(status=status.HTTP_204_NO_CONTENT)
