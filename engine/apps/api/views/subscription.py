from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication


class SubscriptionView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        raise NotImplementedError
        organization = self.request.auth.organization
        user = self.request.user
        return Response(organization.get_subscription_web_report_for_user(user))
