from rest_framework import viewsets
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticated

from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers.teams import TeamSerializer
from apps.public_api.tf_sync import is_request_from_terraform, sync_teams_on_tf_request
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.user_management.models import Team
from common.api_helpers.mixins import PublicPrimaryKeyMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class TeamView(PublicPrimaryKeyMixin, RetrieveModelMixin, ListModelMixin, viewsets.GenericViewSet):
    serializer_class = TeamSerializer
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    model = Team
    pagination_class = FiftyPageSizePaginator
    throttle_classes = [UserThrottle]

    def get_queryset(self):
        if is_request_from_terraform(self.request):
            sync_teams_on_tf_request(self.request.auth.organization)
        name = self.request.query_params.get("name", None)
        queryset = self.request.auth.organization.teams.all()
        if name:
            queryset = queryset.filter(name=name)
        return queryset.order_by("id")
