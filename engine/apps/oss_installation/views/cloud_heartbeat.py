from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import RBACPermission
from apps.auth_token.auth import PluginAuthentication
from apps.oss_installation.cloud_heartbeat import get_heartbeat_link, setup_heartbeat_integration
from apps.oss_installation.models import CloudConnector, CloudHeartbeat


class CloudHeartbeatView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)
    rbac_permissions = {
        "post": [RBACPermission.Permissions.OTHER_SETTINGS_WRITE],
    }

    def post(self, request):
        connector = CloudConnector.objects.first()
        if connector is not None:
            try:
                CloudHeartbeat.objects.get()
                return Response(status=status.HTTP_400_BAD_REQUEST, data={"detail": "Cloud heartbeat already exists"})
            except CloudHeartbeat.DoesNotExist:
                heartbeat = setup_heartbeat_integration()
                link = get_heartbeat_link(connector, heartbeat)
                return Response(status=status.HTTP_200_OK, data={"link": link})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"detail": "Grafana Cloud is not connected"})
