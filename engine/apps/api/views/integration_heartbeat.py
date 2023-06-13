from rest_framework import mixins, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.api.permissions import RBACPermission
from apps.api.serializers.integration_heartbeat import IntegrationHeartBeatSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.heartbeat.models import IntegrationHeartBeat
from common.api_helpers.mixins import PublicPrimaryKeyMixin, TeamFilteringMixin
from common.insight_log import EntityEvent, write_resource_insight_log


class IntegrationHeartBeatView(
    TeamFilteringMixin,
    PublicPrimaryKeyMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)
    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "list": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "retrieve": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "timeout_options": [RBACPermission.Permissions.INTEGRATIONS_READ],
        "create": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "update": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "partial_update": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "activate": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
        "deactivate": [RBACPermission.Permissions.INTEGRATIONS_WRITE],
    }

    model = IntegrationHeartBeat
    serializer_class = IntegrationHeartBeatSerializer

    TEAM_LOOKUP = "alert_receive_channel__team"

    def get_queryset(self, ignore_filtering_by_available_teams=False):
        alert_receive_channel_id = self.request.query_params.get("alert_receive_channel", None)
        lookup_kwargs = {}
        if alert_receive_channel_id:
            lookup_kwargs = {"alert_receive_channel__public_primary_key": alert_receive_channel_id}
        queryset = IntegrationHeartBeat.objects.filter(
            alert_receive_channel__organization=self.request.auth.organization,
            **lookup_kwargs,
        )
        if not ignore_filtering_by_available_teams:
            queryset = queryset.filter(*self.available_teams_lookup_args).distinct()
        queryset = self.serializer_class.setup_eager_loading(queryset)
        return queryset

    def perform_create(self, serializer):
        serializer.save()
        instance = serializer.instance
        write_resource_insight_log(
            instance=instance,
            author=self.request.user,
            event=EntityEvent.CREATED,
        )

    def perform_update(self, serializer):
        prev_state = serializer.instance.insight_logs_serialized
        serializer.save()
        new_state = serializer.instance.insight_logs_serialized
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

    @action(detail=False, methods=["get"])
    def timeout_options(self, request):
        choices = []
        for item in IntegrationHeartBeat.TIMEOUT_CHOICES:
            choices.append({"value": item[0], "display_name": item[1]})
        return Response(choices)
