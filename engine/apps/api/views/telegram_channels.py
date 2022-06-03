from django.apps import apps
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin
from apps.api.serializers.telegram import TelegramToOrganizationConnectorSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.mixins import PublicPrimaryKeyMixin


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
        organization = user.organization

        description = f"Telegram channel @{instance.channel_name} was disconnected from organization"
        create_organization_log(organization, user, OrganizationLogType.TYPE_TELEGRAM_CHANNEL_DISCONNECTED, description)
        instance.delete()
