from urllib.parse import urljoin

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import IsAdmin
from apps.auth_token.auth import PluginAuthentication
from apps.base.utils import live_settings
from apps.oss_installation.models import CloudConnector, CloudHeartbeat


class CloudConnectionView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, IsAdmin)

    def get(self, request):
        connector = CloudConnector.objects.first()
        heartbeat = CloudHeartbeat.objects.first()
        response = {
            "cloud_connection_status": connector is not None,
            "cloud_notifications_enabled": live_settings.GRAFANA_CLOUD_NOTIFICATIONS_ENABLED,
            "cloud_heartbeat_enabled": live_settings.GRAFANA_CLOUD_ONCALL_HEARTBEAT_ENABLED,
            "cloud_heartbeat_link": self._get_heartbeat_link(connector, heartbeat),
            "cloud_heartbeat_status": heartbeat is not None and heartbeat.success,
        }
        return Response(response)

    def _get_heartbeat_link(self, connector, heartbeat):
        if connector is None:
            return None
        if heartbeat is None:
            return None
        return urljoin(connector.cloud_url, f"a/grafana-oncall-app/?page=integrations1&id={heartbeat.integration_id}")
