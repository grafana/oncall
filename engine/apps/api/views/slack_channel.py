from rest_framework import mixins
from rest_framework.filters import SearchFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from apps.api.serializers.slack_channel import SlackChannelSerializer
from apps.auth_token.auth import PluginAuthentication
from apps.slack.models import SlackChannel
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.api_helpers.paginators import HundredPageSizePaginator


class SlackChannelView(PublicPrimaryKeyMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, GenericViewSet):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated,)

    pagination_class = HundredPageSizePaginator

    model = SlackChannel
    filter_backends = (SearchFilter,)
    serializer_class = SlackChannelSerializer
    search_fields = ["name"]

    def get_queryset(self):
        organization = self.request.auth.organization
        slack_team_identity = organization.slack_team_identity
        queryset = SlackChannel.objects.filter(
            slack_team_identity=slack_team_identity,
            is_archived=False,
        )

        return queryset.order_by("id")
