from django.db.models import Count, Q
from django_filters import rest_framework as filters
from emoji import emojize
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.alerts.models import EscalationChain
from apps.api.permissions import RBACPermission
from apps.api.serializers.escalation_chain import (
    EscalationChainListSerializer,
    EscalationChainSerializer,
    FilterEscalationChainSerializer,
)
from apps.auth_token.auth import PluginAuthentication
from apps.user_management.models import Team
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import ByTeamModelFieldFilterMixin, ModelFieldFilterMixin, TeamModelMultipleChoiceFilter
from common.api_helpers.mixins import (
    FilterSerializerMixin,
    ListSerializerMixin,
    PublicPrimaryKeyMixin,
    TeamFilteringMixin,
)
from common.insight_log import EntityEvent, write_resource_insight_log


class EscalationChainFilter(ByTeamModelFieldFilterMixin, ModelFieldFilterMixin, filters.FilterSet):
    team = TeamModelMultipleChoiceFilter()


class EscalationChainViewSet(
    TeamFilteringMixin,
    PublicPrimaryKeyMixin,
    FilterSerializerMixin,
    ListSerializerMixin,
    viewsets.ModelViewSet,
):
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
        "filters": [RBACPermission.Permissions.ESCALATION_CHAINS_READ],
    }

    filter_backends = [SearchFilter, filters.DjangoFilterBackend]
    search_fields = ("name",)
    filterset_class = EscalationChainFilter

    serializer_class = EscalationChainSerializer
    list_serializer_class = EscalationChainListSerializer

    filter_serializer_class = FilterEscalationChainSerializer

    def get_queryset(self, ignore_filtering_by_available_teams=False):
        is_filters_request = self.request.query_params.get("filters", "false") == "true"

        queryset = EscalationChain.objects.filter(
            organization=self.request.auth.organization,
        )

        if not ignore_filtering_by_available_teams:
            queryset = queryset.filter(*self.available_teams_lookup_args).distinct()

        if is_filters_request:
            # Do not annotate num_integrations and num_routes for filters request,
            # only fetch public_primary_key and name fields needed by FilterEscalationChainSerializer
            return queryset.only("public_primary_key", "name")

        queryset = queryset.annotate(
            num_integrations=Count(
                "channel_filters__alert_receive_channel",
                distinct=True,
                filter=Q(channel_filters__alert_receive_channel__deleted_at__isnull=True),
            )
        ).annotate(
            num_routes=Count(
                "channel_filters",
                distinct=True,
                filter=Q(channel_filters__alert_receive_channel__deleted_at__isnull=True),
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
        obj = self.get_object()

        name = request.data.get("name")
        team_id = request.data.get("team")
        if team_id == "null":
            team_id = None

        if not name:
            raise BadRequest(detail={"name": ["This field may not be null."]})
        else:
            if EscalationChain.objects.filter(organization=request.auth.organization, name=name).exists():
                raise BadRequest(detail={"name": ["Escalation chain with this name already exists."]})

        try:
            team = request.user.available_teams.get(public_primary_key=team_id) if team_id else None
        except Team.DoesNotExist:
            return Response(data={"error_code": "wrong_team"}, status=status.HTTP_403_FORBIDDEN)
        copy = obj.make_copy(name, team)
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
                    "display_name": emojize(channel_filter["alert_receive_channel__verbal_name"], language="alias"),
                    "channel_filters": [],
                },
            )["channel_filters"].append(channel_filter_data)
        return Response(data.values())

    @action(methods=["get"], detail=False)
    def filters(self, request):
        filter_name = request.query_params.get("search", None)
        api_root = "/api/internal/v1/"

        filter_options = [
            {
                "name": "team",
                "type": "team_select",
                "href": api_root + "teams/",
                "global": True,
            },
        ]

        if filter_name is not None:
            filter_options = list(filter(lambda f: filter_name in f["name"], filter_options))

        return Response(filter_options)
