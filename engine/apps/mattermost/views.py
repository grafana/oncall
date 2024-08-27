from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.permissions import RBACPermission
from apps.auth_token.auth import PluginAuthentication
from apps.mattermost.models import MattermostChannel
from apps.mattermost.serializers import MattermostChannelSerializer
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.insight_log.chatops_insight_logs import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log


class MattermostChannelViewSet(
    PublicPrimaryKeyMixin[MattermostChannel],
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "list": [RBACPermission.Permissions.CHATOPS_READ],
        "retrieve": [RBACPermission.Permissions.CHATOPS_READ],
        "create": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
        "destroy": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
    }

    serializer_class = MattermostChannelSerializer

    def get_queryset(self):
        return MattermostChannel.objects.filter(organization=self.request.user.organization)

    def perform_create(self, serializer):
        serializer.save()
        instance = serializer.instance
        write_chatops_insight_log(
            author=self.request.user,
            event_name=ChatOpsEvent.CHANNEL_CONNECTED,
            chatops_type=ChatOpsTypePlug.MATTERMOST.value,
            channel_name=instance.channel_name,
        )

    def perform_destroy(self, instance):
        write_chatops_insight_log(
            author=self.request.user,
            event_name=ChatOpsEvent.CHANNEL_DISCONNECTED,
            chatops_type=ChatOpsTypePlug.MATTERMOST.value,
            channel_name=instance.channel_name,
            channel_id=instance.channel_id,
        )
        instance.delete()
