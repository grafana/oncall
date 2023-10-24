from django.utils.functional import cached_property
from rest_framework import mixins, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.alerts.models import AlertReceiveChannel
from apps.api.permissions import RBACPermission
from apps.api.serializers.team import TeamSerializer, TeamSerializerContext
from apps.auth_token.auth import PluginAuthentication
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from apps.schedules.ical_utils import get_oncall_users_for_multiple_schedules
from apps.user_management.models import Team
from common.api_helpers.mixins import PublicPrimaryKeyMixin


class TeamViewSet(PublicPrimaryKeyMixin, mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    authentication_classes = (
        MobileAppAuthTokenAuthentication,
        PluginAuthentication,
    )
    permission_classes = (IsAuthenticated, RBACPermission)
    rbac_permissions = {
        "list": [RBACPermission.Permissions.OTHER_SETTINGS_READ],
        "retrieve": [RBACPermission.Permissions.OTHER_SETTINGS_READ],
        "update": [RBACPermission.Permissions.OTHER_SETTINGS_WRITE],
    }

    serializer_class = TeamSerializer
    filter_backends = [SearchFilter]
    search_fields = ["name"]

    def get_queryset(self):
        return self.request.user.available_teams

    @cached_property
    def schedules_with_oncall_users(self):
        """
        The result of this method is cached and is reused for the whole lifetime of a request,
        since self.get_serializer_context() is called multiple times for every instance in the queryset.
        """
        team_ids = [t.id for t in self.filter_queryset(self.get_queryset())]
        team_schedules = self.request.user.organization.oncall_schedules.filter(team__id__in=team_ids)
        return get_oncall_users_for_multiple_schedules(team_schedules)

    def get_serializer_context(self) -> TeamSerializerContext:
        context = super().get_serializer_context()
        context.update({"schedules_with_oncall_users": self.schedules_with_oncall_users})
        return context

    def list(self, request, *args, **kwargs):
        general_team = [Team(public_primary_key="null", name="No team", email=None, avatar_url=None)]
        queryset = self.filter_queryset(self.get_queryset())

        if self.request.query_params.get("only_include_notifiable_teams", "false") == "true":
            # filters down to only teams that have a direct paging integration that is "contactable"
            orgs_direct_paging_integrations = AlertReceiveChannel.get_orgs_direct_paging_integrations(
                self.request.user.organization
            )
            contactable_direct_paging_integrations = [i for i in orgs_direct_paging_integrations if i.is_contactable]
            team_ids = [i.team.pk for i in contactable_direct_paging_integrations if i.team is not None]

            queryset = queryset.filter(pk__in=team_ids)

        teams = list(queryset)
        if self.request.query_params.get("include_no_team", "true") != "false":
            # Adds general team to the queryset in a way that it always shows up first (even when not searched for).
            queryset = general_team + teams
        else:
            queryset = teams

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
