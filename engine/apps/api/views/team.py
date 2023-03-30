from rest_framework import mixins, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from apps.api.permissions import RBACPermission
from apps.api.serializers.team import TeamSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.mobile_app.auth import MobileAppAuthTokenAuthentication
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

    def filter_queryset(self, queryset):
        """
        Adds general team to the queryset in a way that it works well with searching by name.
        """
        result = list(super().filter_queryset(queryset))
        general_team = Team(public_primary_key="null", name="No team", email=None, avatar_url=None)

        search = self.request.query_params.get(SearchFilter.search_param)
        if not search or search.lower() in general_team.name.lower():  # check if general team should be added
            return [general_team] + result

        return result
