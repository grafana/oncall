from rest_framework import mixins, viewsets
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated

from apps.api.serializers.user_group import UserGroupSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.slack.models import SlackUserGroup


class UserGroupViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)
    serializer_class = UserGroupSerializer

    filter_backends = (SearchFilter,)
    search_fields = ("name", "handle")

    def get_queryset(self):
        slack_team_identity = self.request.auth.organization.slack_team_identity
        if slack_team_identity is None:
            return SlackUserGroup.objects.none()

        return slack_team_identity.usergroups.all()
