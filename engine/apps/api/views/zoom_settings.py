from django.conf import settings
from rest_framework import status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import RBACPermission
from apps.auth_token.auth import PluginAuthentication
from common.insight_log import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log


class ZoomSettingsAPIView(views.APIView):
    """
    API View for Zoom integration settings.
    """
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "get": [RBACPermission.Permissions.CHATOPS_READ],
        "delete": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
    }

    def get(self, request):
        """Get current Zoom settings for the organization."""
        if not getattr(settings, 'FEATURE_ZOOM_INTEGRATION_ENABLED', False):
            return Response(
                {"detail": "Zoom integration is not enabled"},
                status=status.HTTP_400_BAD_REQUEST
            )

        organization = request.auth.organization

        from apps.zoom.models import ZoomChannel

        channels = ZoomChannel.objects.filter(organization=organization)
        default_channel = channels.filter(is_default_channel=True).first()

        return Response({
            "zoom_configured": True,
            "default_channel": {
                "id": default_channel.public_primary_key,
                "channel_id": default_channel.channel_id,
                "channel_name": default_channel.channel_name,
            } if default_channel else None,
            "channels_count": channels.count(),
        })

    def delete(self, request):
        """Disconnect Zoom integration for the organization (remove all channels)."""
        if not getattr(settings, 'FEATURE_ZOOM_INTEGRATION_ENABLED', False):
            return Response(
                {"detail": "Zoom integration is not enabled"},
                status=status.HTTP_400_BAD_REQUEST
            )

        organization = request.auth.organization

        from apps.zoom.models import ZoomChannel

        channels = ZoomChannel.objects.filter(organization=organization)
        channels_count = channels.count()
        channels.delete()

        write_chatops_insight_log(
            author=request.user,
            event_name=ChatOpsEvent.WORKSPACE_DISCONNECTED,
            chatops_type=ChatOpsTypePlug.ZOOM.value,
            channels_removed=channels_count,
        )

        return Response(status=status.HTTP_204_NO_CONTENT)


class SetDefaultZoomChannel(views.APIView):
    """
    API View for setting the default Zoom channel.
    """
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "post": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
    }

    def post(self, request):
        """Set the default Zoom channel for the organization."""
        if not getattr(settings, 'FEATURE_ZOOM_INTEGRATION_ENABLED', False):
            return Response(
                {"detail": "Zoom integration is not enabled"},
                status=status.HTTP_400_BAD_REQUEST
            )

        channel_id = request.data.get("id")
        if not channel_id:
            return Response(
                {"detail": "Channel ID is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        organization = request.auth.organization

        from apps.zoom.models import ZoomChannel

        try:
            channel = ZoomChannel.objects.get(
                organization=organization,
                public_primary_key=channel_id
            )
        except ZoomChannel.DoesNotExist:
            return Response(
                {"detail": "Channel not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        channel.make_channel_default()

        write_chatops_insight_log(
            author=request.user,
            event_name=ChatOpsEvent.DEFAULT_CHANNEL_CHANGED,
            chatops_type=ChatOpsTypePlug.ZOOM.value,
            channel_name=channel.channel_name,
        )

        return Response({
            "id": channel.public_primary_key,
            "channel_id": channel.channel_id,
            "channel_name": channel.channel_name,
            "is_default_channel": True,
        })
