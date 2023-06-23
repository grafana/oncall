from django_filters import rest_framework as filters
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import EscalationChain
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers import EscalationChainSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from common.api_helpers.filters import ByTeamFilter
from common.api_helpers.mixins import RateLimitHeadersMixin
from common.api_helpers.paginators import FiftyPageSizePaginator
from common.insight_log import EntityEvent, write_resource_insight_log


class EscalationChainView(RateLimitHeadersMixin, ModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = EscalationChain
    serializer_class = EscalationChainSerializer

    pagination_class = FiftyPageSizePaginator

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ByTeamFilter

    def get_queryset(self):
        queryset = self.request.auth.organization.escalation_chains.all()

        name = self.request.query_params.get("name")
        if name is not None:
            queryset = queryset.filter(name=name)

        return queryset.order_by("id")

    def get_object(self):
        public_primary_key = self.kwargs["pk"]

        try:
            return self.request.auth.organization.escalation_chains.get(public_primary_key=public_primary_key)
        except EscalationChain.DoesNotExist:
            raise NotFound

    def perform_create(self, serializer):
        serializer.save()
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.CREATED,
        )

    def perform_destroy(self, instance):
        write_resource_insight_log(
            instance=instance,
            author=self.request.user,
            event=EntityEvent.DELETED,
        )
        instance.delete()

    def perform_update(self, serializer):
        instance = serializer.instance
        prev_state = instance.insight_logs_serialized
        serializer.save()
        new_state = instance.insight_logs_serialized
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )
