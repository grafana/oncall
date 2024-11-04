from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.alerts.models import Alert
from apps.api.serializers.alert import AlertRawSerializer
from apps.auth_token.auth import PluginAuthentication


class AlertDetailView(APIView):
    authentication_classes = [PluginAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        try:
            alert = Alert.objects.get(public_primary_key=id)
        except Alert.DoesNotExist:
            raise NotFound()
        if alert.group.channel.organization != request.auth.organization:
            raise NotFound()
        serializer = AlertRawSerializer(alert)
        return Response(serializer.data)
