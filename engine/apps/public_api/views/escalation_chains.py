from django_filters import rest_framework as filters
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import EscalationChain
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers import EscalationChainSerializer
from apps.public_api.serializers.escalation_chains import EscalationChainUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.filters import ByTeamFilter
from common.api_helpers.mixins import RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


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

        instance = serializer.instance
        description = f"Escalation chain {instance.name} was created"
        create_organization_log(
            instance.organization,
            self.request.user,
            OrganizationLogType.TYPE_ESCALATION_CHAIN_CREATED,
            description,
        )

    def perform_destroy(self, instance):
        instance.delete()

        description = f"Escalation chain {instance.name} was deleted"
        create_organization_log(
            instance.organization,
            self.request.user,
            OrganizationLogType.TYPE_ESCALATION_CHAIN_DELETED,
            description,
        )

    def perform_update(self, serializer):
        instance = serializer.instance
        old_state = instance.repr_settings_for_client_side_logging

        serializer.save()

        new_state = instance.repr_settings_for_client_side_logging
        description = f"Escalation chain {instance.name} was changed from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(
            instance.organization,
            self.request.user,
            OrganizationLogType.TYPE_ESCALATION_CHAIN_CHANGED,
            description,
        )
