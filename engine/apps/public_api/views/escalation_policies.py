from django.db.models import Q
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import EscalationPolicy
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api import constants as public_api_constants
from apps.public_api.serializers import EscalationPolicySerializer, EscalationPolicyUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.mixins import DemoTokenMixin, RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class EscalationPolicyView(RateLimitHeadersMixin, DemoTokenMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = EscalationPolicy
    serializer_class = EscalationPolicySerializer
    update_serializer_class = EscalationPolicyUpdateSerializer

    pagination_class = FiftyPageSizePaginator

    demo_default_id = public_api_constants.DEMO_ESCALATION_POLICY_ID_1

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
        instance = serializer.instance
        organization = self.request.auth.organization
        user = self.request.user
        escalation_chain = instance.escalation_chain
        description = (
            f"Escalation step '{instance.step_type_verbal}' with order {instance.order} was created for "
            f"escalation chain '{escalation_chain.name}'"
        )
        create_organization_log(organization, user, OrganizationLogType.TYPE_ESCALATION_STEP_CREATED, description)

    def perform_update(self, serializer):
        organization = self.request.auth.organization
        user = self.request.user
        old_state = serializer.instance.repr_settings_for_client_side_logging
        serializer.save()
        new_state = serializer.instance.repr_settings_for_client_side_logging
        escalation_chain = serializer.instance.escalation_chain
        description = (
            f"Settings for escalation step of escalation chain '{escalation_chain.name}' was changed "
            f"from:\n{old_state}\nto:\n{new_state}"
        )
        create_organization_log(organization, user, OrganizationLogType.TYPE_ESCALATION_STEP_CHANGED, description)

    def perform_destroy(self, instance):
        organization = self.request.auth.organization
        user = self.request.user
        escalation_chain = instance.escalation_chain
        description = (
            f"Escalation step '{instance.step_type_verbal}' with order {instance.order} of "
            f"escalation chain '{escalation_chain.name}' was deleted"
        )
        create_organization_log(organization, user, OrganizationLogType.TYPE_ESCALATION_STEP_DELETED, description)
        instance.delete()
