from django.utils.functional import cached_property
from rest_framework import mixins, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
        """
        Adds general team to the queryset in a way that it always shows up first (even when not searched for).
        """
        general_team = Team(public_primary_key="null", name="No team", email=None, avatar_url=None)
        queryset = [general_team] + list(self.filter_queryset(self.get_queryset()))

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
