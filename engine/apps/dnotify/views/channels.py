from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.auth_token.auth import PluginAuthentication


class ChannelView(APIView):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request, format=None):
        """Sample view to return available channels information."""
        # this could get information from a db model instead
        channels = [
            {"id": "channel-1", "name": "Channel 1"},
            {"id": "channel-2", "name": "Channel 2"},
        ]
        return Response(channels)
