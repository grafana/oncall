from rest_framework import mixins, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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

    def list(self, request, *args, **kwargs):
        """
        Adds general team to the queryset in a way that it always shows up first (even when not searched for).
        """
        general_team = Team(public_primary_key="null", name="No team", email=None, avatar_url=None)
        queryset = [general_team] + list(self.filter_queryset(self.get_queryset()))

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
