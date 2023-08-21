from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication
from common.api_helpers.mixins import ALL_TEMPLATE_NAMES, NOTIFICATION_CHANNEL_OPTIONS


class PreviewTemplateOptionsView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(
            {
                "notification_channel_options": NOTIFICATION_CHANNEL_OPTIONS,
                "template_name_options": ALL_TEMPLATE_NAMES,
            }
        )
