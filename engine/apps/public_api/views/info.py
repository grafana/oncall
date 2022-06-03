from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.throttlers.user_throttle import UserThrottle


class InfoView(APIView):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    def get(self, request):
        response = {"url": self.request.auth.organization.grafana_url}
        return Response(response)
