from django_filters import rest_framework as filters
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import EscalationChain
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers import EscalationChainSerializer
from apps.public_api.serializers.escalation_chains import EscalationChainUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from common.api_helpers.filters import ByTeamFilter
from common.api_helpers.mixins import RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator
from common.insight_logs import entity_created_insight_logs, entity_deleted_insight_logs, entity_updated_insight_logs


class EscalationChainView(RateLimitHeadersMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = EscalationChain
    serializer_class = EscalationChainSerializer
    update_serializer_class = EscalationChainUpdateSerializer

    pagination_class = FiftyPageSizePaginator

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ByTeamFilter

    def get_queryset(self):
        queryset = self.request.auth.organization.escalation_chains.all()

        name = self.request.query_params.get("name")
        if name is not None:
            queryset = queryset.filter(name=name)

        return queryset

    def get_object(self):
        public_primary_key = self.kwargs["pk"]

        try:
            return self.request.auth.organization.escalation_chains.get(public_primary_key=public_primary_key)
        except EscalationChain.DoesNotExist:
            raise NotFound

    def perform_create(self, serializer):
        serializer.save()
        entity_created_insight_logs(instance=serializer.serializer.instance, user=self.request.user)

    def perform_destroy(self, instance):
        entity_deleted_insight_logs(instance=instance, user=self.request.user)
        instance.delete()

    def perform_update(self, serializer):
        instance = serializer.instance
        old_state = instance.repr_settings_for_client_side_logging
        serializer.save()
        new_state = instance.repr_settings_for_client_side_logging
        entity_updated_insight_logs(
            instance=instance,
            user=self.request.user,
            before=old_state,
            after=new_state,
        )
