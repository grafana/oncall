from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.api.serializers.team import TeamSerializer
from apps.auth_token.auth import MobileAppAuthTokenAuthentication, PluginAuthentication
from apps.user_management.models import Team


class TeamViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = (
        MobileAppAuthTokenAuthentication,
        PluginAuthentication,
    )
    permission_classes = (IsAuthenticated,)

    serializer_class = TeamSerializer

    def get_queryset(self):
        teams = list(self.request.user.teams.all())

        # dirty hack to render "General" team in team select on the frontend
        general_team = Team(public_primary_key=None, name="General", email=None, avatar_url=None)

        return teams + [general_team]
