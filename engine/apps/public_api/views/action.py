from django_filters import rest_framework as filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from apps.alerts.models import CustomButton
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers.action import ActionSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from common.api_helpers.filters import ByTeamFilter
from common.api_helpers.mixins import PublicPrimaryKeyMixin, RateLimitHeadersMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class ActionView(RateLimitHeadersMixin, PublicPrimaryKeyMixin, ReadOnlyModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = FiftyPageSizePaginator
    throttle_classes = [UserThrottle]

    model = CustomButton
    serializer_class = ActionSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ByTeamFilter

    def get_queryset(self):
        action_name = self.request.query_params.get("name", None)
        queryset = CustomButton.objects.filter(organization=self.request.auth.organization)

        if action_name:
            queryset = queryset.filter(name=action_name)

        return queryset.order_by("id")
