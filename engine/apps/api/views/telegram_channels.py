from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import RBACPermission
from apps.api.serializers.telegram import TelegramToOrganizationConnectorSerializer
from apps.auth_token.auth import PluginAuthentication
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.insight_log.chatops_insight_logs import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log


class TelegramChannelViewSet(
    PublicPrimaryKeyMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.CHATOPS_READ],
        "list": [RBACPermission.Permissions.CHATOPS_READ],
        "retrieve": [RBACPermission.Permissions.CHATOPS_READ],
        "destroy": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
        "set_default": [RBACPermission.Permissions.CHATOPS_UPDATE_SETTINGS],
    }

    serializer_class = TelegramToOrganizationConnectorSerializer

    def get_queryset(self):
        from apps.telegram.models import TelegramToOrganizationConnector

        return TelegramToOrganizationConnector.objects.filter(organization=self.request.user.organization)

    @action(detail=True, methods=["post"])
    def set_default(self, request, pk):
        telegram_channel = self.get_object()
        telegram_channel.make_channel_default(request.user)

        return Response(status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        user = self.request.user
        write_chatops_insight_log(
            author=user,
            event_name=ChatOpsEvent.CHANNEL_DISCONNECTED,
            chatops_type=ChatOpsTypePlug.TELEGRAM.value,
            channel_name=instance.channel_name,
        )
        instance.delete()
