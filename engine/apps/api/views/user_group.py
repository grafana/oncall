from rest_framework import mixins, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from apps.api.permissions import RBACPermission
from apps.api.serializers.user_group import UserGroupSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.slack.models import SlackUserGroup
from common.api_helpers.mixins import PublicPrimaryKeyMixin


class UserGroupViewSet(
    PublicPrimaryKeyMixin[SlackUserGroup], mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, RBACPermission)
    serializer_class = UserGroupSerializer

    rbac_permissions = {
        "list": [RBACPermission.Permissions.CHATOPS_READ],
        "retrieve": [RBACPermission.Permissions.CHATOPS_READ],
    }

    filter_backends = (SearchFilter,)
    search_fields = ("name", "handle")

    def get_queryset(self):
        slack_team_identity = self.request.auth.organization.slack_team_identity
        if slack_team_identity is None:
            return SlackUserGroup.objects.none()

        return slack_team_identity.usergroups.all()
