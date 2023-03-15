from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.serializers.team import TeamSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
from apps.user_management.models import Team


class TeamViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    authentication_classes = (
        MobileAppAuthTokenAuthentication,
        PluginAuthentication,
    )
    permission_classes = (IsAuthenticated,)

    serializer_class = TeamSerializer

    def get_queryset(self):
        teams = list(self.request.user.available_teams())

        # option for resources without team
        general_team = Team(public_primary_key="null", name="no team", email=None, avatar_url=None)
        # all_teams = Team(public_primary_key="visible_across_all_teams", name="shared across all teams", email=None, avatar_url=None)

        return [general_team] + teams
