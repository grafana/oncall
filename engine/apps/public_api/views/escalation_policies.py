from django.db.models import Q
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import EscalationPolicy
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers import EscalationPolicySerializer, EscalationPolicyUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from common.api_helpers.mixins import RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator
from common.insight_log import EntityEvent, write_resource_insight_log


class EscalationPolicyView(RateLimitHeadersMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = EscalationPolicy
    serializer_class = EscalationPolicySerializer
    update_serializer_class = EscalationPolicyUpdateSerializer

    pagination_class = FiftyPageSizePaginator

    def get_queryset(self):
        escalation_chain_id = self.request.query_params.get("escalation_chain_id", None)
        queryset = EscalationPolicy.objects.filter(
            Q(escalation_chain__organization=self.request.auth.organization),
            Q(step__in=EscalationPolicy.PUBLIC_STEP_CHOICES_MAP) | Q(step__isnull=True),
        )
        queryset = self.serializer_class.setup_eager_loading(queryset)

        if escalation_chain_id:
            queryset = queryset.filter(escalation_chain__public_primary_key=escalation_chain_id)

        return queryset.order_by("escalation_chain", "order")

    def get_object(self):
        public_primary_key = self.kwargs["pk"]

        try:
            return EscalationPolicy.objects.filter(
                Q(escalation_chain__organization=self.request.auth.organization),
                Q(step__in=EscalationPolicy.PUBLIC_STEP_CHOICES_MAP) | Q(step__isnull=True),
            ).get(public_primary_key=public_primary_key)
        except EscalationPolicy.DoesNotExist:
            raise NotFound

    def perform_create(self, serializer):
        serializer.save()
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.CREATED,
        )

    def perform_update(self, serializer):
        prev_state = serializer.instance.insight_logs_serialized
        serializer.save()
        new_state = serializer.instance.insight_logs_serialized
        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.UPDATED,
            prev_state=prev_state,
            new_state=new_state,
        )

    def perform_destroy(self, instance):
        write_resource_insight_log(
            instance=instance,
            author=self.request.user,
            event=EntityEvent.DELETED,
        )
        instance.delete()
