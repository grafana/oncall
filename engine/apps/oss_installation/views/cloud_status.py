from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication
from apps.oss_installation.models import CloudOrganizationConnector


class CloudConnectionStatusView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        connector = CloudOrganizationConnector.objects.filter(organization=request.user.organization).first()

        response = {
            "cloud_connection_status": connector is not None,
        }
        return Response(response)
