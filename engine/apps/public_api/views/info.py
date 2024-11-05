from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import RBACPermission
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.throttlers import InfoThrottler


class InfoView(APIView):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "get": [RBACPermission.Permissions.OTHER_SETTINGS_READ],
    }

    throttle_classes = [InfoThrottler]

    def get(self, request):
        response = {"url": self.request.auth.organization.grafana_url}
        return Response(response)
