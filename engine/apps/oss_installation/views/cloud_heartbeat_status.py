from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication
from apps.oss_installation.models import CloudHeartbeat


class CloudHeartbeatStatusView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        response = {"status": CloudHeartbeat.status()}
        return Response(response)
