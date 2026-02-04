from django.conf import settings
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.api.permissions import RBACPermission
from apps.api.serializers.zoom import ZoomChannelSerializer
from apps.auth_token.auth import PluginAuthentication
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.insight_log import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log


class ZoomChannelView(
    PublicPrimaryKeyMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet,
):
    """
    API ViewSet for managing Zoom channels.
    """
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    serializer_class = ZoomChannelSerializer

    rbac_permissions = {
        "list": [RBACPermission.Permissions.CHATOPS_READ],
        "retrieve": [RBACPermission.Permissions.CHATOPS_READ],
        "create": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
        "destroy": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
        "set_default": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
    }

    def get_queryset(self):
        if not getattr(settings, 'FEATURE_ZOOM_INTEGRATION_ENABLED', False):
            from apps.zoom.models import ZoomChannel
            return ZoomChannel.objects.none()

        from apps.zoom.models import ZoomChannel
        organization = self.request.auth.organization
        return ZoomChannel.objects.filter(organization=organization).order_by("id")

    def perform_create(self, serializer):
        serializer.save()
        write_chatops_insight_log(
            author=self.request.user,
            event_name=ChatOpsEvent.CHANNEL_CONNECTED,
            chatops_type=ChatOpsTypePlug.ZOOM.value,
            channel_name=serializer.instance.channel_name,
        )

    def perform_destroy(self, instance):
        channel_name = instance.channel_name
        instance.delete()
        write_chatops_insight_log(
            author=self.request.user,
            event_name=ChatOpsEvent.CHANNEL_DISCONNECTED,
            chatops_type=ChatOpsTypePlug.ZOOM.value,
            channel_name=channel_name,
        )

    @action(detail=True, methods=["post"])
    def set_default(self, request, pk=None):
        """Set this channel as the default Zoom channel for the organization."""
        instance = self.get_object()
        instance.make_channel_default(request.user)
        write_chatops_insight_log(
            author=request.user,
            event_name=ChatOpsEvent.DEFAULT_CHANNEL_CHANGED,
            chatops_type=ChatOpsTypePlug.ZOOM.value,
            channel_name=instance.channel_name,
        )
        return Response(status=status.HTTP_200_OK)
