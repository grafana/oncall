from django.db.models import Count, Q
from emoji import emojize
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.alerts.models import EscalationChain
from apps.api.permissions import RBACPermission
from apps.api.serializers.escalation_chain import EscalationChainListSerializer, EscalationChainSerializer
from apps.auth_token.auth import PluginAuthentication
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.mixins import ListSerializerMixin, PublicPrimaryKeyMixin, TeamFilteringMixin
from common.insight_log import EntityEvent, write_resource_insight_log


class EscalationChainViewSet(TeamFilteringMixin, PublicPrimaryKeyMixin, ListSerializerMixin, viewsets.ModelViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)

    rbac_permissions = {
        "metadata": [RBACPermission.Permissions.ESCALATION_CHAINS_READ],
        "list": [RBACPermission.Permissions.ESCALATION_CHAINS_READ],
        "retrieve": [RBACPermission.Permissions.ESCALATION_CHAINS_READ],
        "details": [RBACPermission.Permissions.ESCALATION_CHAINS_READ],
        "create": [RBACPermission.Permissions.ESCALATION_CHAINS_WRITE],
        "update": [RBACPermission.Permissions.ESCALATION_CHAINS_WRITE],
        "destroy": [RBACPermission.Permissions.ESCALATION_CHAINS_WRITE],
        "copy": [RBACPermission.Permissions.ESCALATION_CHAINS_WRITE],
    }

    filter_backends = [SearchFilter]
    search_fields = ("^name",)

    serializer_class = EscalationChainSerializer
    list_serializer_class = EscalationChainListSerializer

    def get_queryset(self):
        queryset = (
            EscalationChain.objects.filter(
                organization=self.request.auth.organization,
                team=self.request.user.current_team,
            )
            .annotate(
                num_integrations=Count(
                    "channel_filters__alert_receive_channel",
                    distinct=True,
                    filter=Q(channel_filters__alert_receive_channel__deleted_at__isnull=True),
                )
            )
            .annotate(
                num_routes=Count(
                    "channel_filters",
                    distinct=True,
                    filter=Q(channel_filters__alert_receive_channel__deleted_at__isnull=True),
                )
            )
        )

        return queryset

    def perform_create(self, serializer):
        serializer.save()
        write_resource_insight_log(instance=serializer.instance, author=self.request.user, event=EntityEvent.CREATED)

    def perform_destroy(self, instance):
        write_resource_insight_log(
            instance=instance,
            author=self.request.user,
            event=EntityEvent.DELETED,
        )
        instance.delete()

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

    @action(methods=["post"], detail=True)
    def copy(self, request, pk):
        name = request.data.get("name")
        if name is None:
            raise BadRequest(detail={"name": ["This field may not be null."]})
        else:
            if EscalationChain.objects.filter(organization=request.auth.organization, name=name).exists():
                raise BadRequest(detail={"name": ["Escalation chain with this name already exists."]})

        obj = self.get_object()
        copy = obj.make_copy(name)
        serializer = self.get_serializer(copy)
        write_resource_insight_log(
            instance=copy,
            author=self.request.user,
            event=EntityEvent.CREATED,
        )
        return Response(serializer.data)

    @action(methods=["get"], detail=True)
    def details(self, request, pk):
        obj = self.get_object()
        channel_filters = obj.channel_filters.filter(alert_receive_channel__deleted_at__isnull=True).values(
            "public_primary_key",
            "filtering_term",
            "is_default",
            "alert_receive_channel__public_primary_key",
            "alert_receive_channel__verbal_name",
        )
        data = {}
        for channel_filter in channel_filters:
            channel_filter_data = {
                "display_name": "Default Route" if channel_filter["is_default"] else channel_filter["filtering_term"],
                "id": channel_filter["public_primary_key"],
            }
            data.setdefault(
                channel_filter["alert_receive_channel__public_primary_key"],
                {
                    "id": channel_filter["alert_receive_channel__public_primary_key"],
                    "display_name": emojize(channel_filter["alert_receive_channel__verbal_name"], use_aliases=True),
                    "channel_filters": [],
                },
            )["channel_filters"].append(channel_filter_data)
        return Response(data.values())
