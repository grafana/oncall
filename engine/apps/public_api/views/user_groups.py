from rest_framework import mixins
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import GenericViewSet

from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers.user_groups import UserGroupSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.slack.models import SlackUserGroup
from common.api_helpers.mixins import RateLimitHeadersMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class UserGroupView(RateLimitHeadersMixin, mixins.ListModelMixin, GenericViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = FiftyPageSizePaginator
    throttle_classes = [UserThrottle]

    model = SlackUserGroup
    serializer_class = UserGroupSerializer

    def get_queryset(self):
        slack_handle = self.request.query_params.get("slack_handle", None)
        queryset = SlackUserGroup.objects.filter(
            slack_team_identity__organizations=self.request.auth.organization
        ).distinct()
        if slack_handle:
            queryset = queryset.filter(handle=slack_handle)
        return queryset.order_by("id")
