from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin
from apps.api.serializers.integration_heartbeat import IntegrationHeartBeatSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.heartbeat.models import IntegrationHeartBeat
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.mixins import PublicPrimaryKeyMixin


class IntegrationHeartBeatView(
    PublicPrimaryKeyMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)
    action_permissions = {
        IsAdmin: (*MODIFY_ACTIONS, "activate", "deactivate"),
        AnyRole: (*READ_ACTIONS, "timeout_options"),
    }

    model = IntegrationHeartBeat
    serializer_class = IntegrationHeartBeatSerializer

    def get_queryset(self):
        alert_receive_channel_id = self.request.query_params.get("alert_receive_channel", None)
        lookup_kwargs = {}
        if alert_receive_channel_id:
            lookup_kwargs = {"alert_receive_channel__public_primary_key": alert_receive_channel_id}
        queryset = IntegrationHeartBeat.objects.filter(
            **lookup_kwargs,
            alert_receive_channel__organization=self.request.auth.organization,
            alert_receive_channel__team=self.request.user.current_team,
        )
        queryset = self.serializer_class.setup_eager_loading(queryset)
        return queryset

    def perform_create(self, serializer):
        serializer.save()
        instance = serializer.instance
        description = f"Heartbeat for integration {instance.alert_receive_channel.verbal_name} was created"
        create_organization_log(
            instance.alert_receive_channel.organization,
            self.request.user,
            OrganizationLogType.TYPE_HEARTBEAT_CREATED,
            description,
        )

    def perform_update(self, serializer):
        old_state = serializer.instance.repr_settings_for_client_side_logging
        serializer.save()
        new_state = serializer.instance.repr_settings_for_client_side_logging
        alert_receive_channel = serializer.instance.alert_receive_channel
        description = (
            f"Settings for heartbeat of integration "
            f"{alert_receive_channel.verbal_name} was changed "
            f"from:\n{old_state}\nto:\n{new_state}"
        )
        create_organization_log(
            alert_receive_channel.organization,
            self.request.user,
            OrganizationLogType.TYPE_HEARTBEAT_CHANGED,
            description,
        )

    @action(detail=False, methods=["get"])
    def timeout_options(self, request):
        choices = []
        for item in IntegrationHeartBeat.TIMEOUT_CHOICES:
            choices.append({"value": item[0], "display_name": item[1]})
        return Response(choices)
