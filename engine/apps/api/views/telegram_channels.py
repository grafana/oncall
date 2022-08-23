from django.apps import apps
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin
from apps.api.serializers.telegram import TelegramToOrganizationConnectorSerializer
from apps.auth_token.auth import PluginAuthentication
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.insight_log.chatops_insight_logs import ChatOpsEvent, ChatOpsType, write_chatops_insight_log


class TelegramChannelViewSet(
    PublicPrimaryKeyMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)

    action_permissions = {
        IsAdmin: (*MODIFY_ACTIONS, "set_default"),
        AnyRole: READ_ACTIONS,
    }

    serializer_class = TelegramToOrganizationConnectorSerializer

    def get_queryset(self):
        TelegramToOrganizationConnector = apps.get_model("telegram", "TelegramToOrganizationConnector")
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
            chatops_type=ChatOpsType.TELEGRAM,
            channel_name=instance.channel_name,
        )
        instance.delete()
