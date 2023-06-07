from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers.slack_channel import SlackChannelSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.slack.models import SlackChannel
from common.api_helpers.mixins import RateLimitHeadersMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class SlackChannelView(RateLimitHeadersMixin, mixins.ListModelMixin, GenericViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = FiftyPageSizePaginator
    throttle_classes = [UserThrottle]

    model = SlackChannel
    serializer_class = SlackChannelSerializer

    def get_queryset(self):
        channel_name = self.request.query_params.get("channel_name", None)

        queryset = SlackChannel.objects.filter(
            slack_team_identity__organizations=self.request.auth.organization,
            is_archived=False,
        ).distinct()

        if channel_name:
            queryset = queryset.filter(name=channel_name)

        return queryset.order_by("id")
