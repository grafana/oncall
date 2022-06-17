from django_filters import rest_framework as filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import CustomButton
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers.action import ActionCreateSerializer, ActionUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.filters import ByTeamFilter
from common.api_helpers.mixins import PublicPrimaryKeyMixin, RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator


class ActionView(RateLimitHeadersMixin, PublicPrimaryKeyMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)
    pagination_class = FiftyPageSizePaginator
    throttle_classes = [UserThrottle]

    model = CustomButton
    serializer_class = ActionCreateSerializer
    update_serializer_class = ActionUpdateSerializer

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ByTeamFilter

    def get_queryset(self):
        action_name = self.request.query_params.get("name", None)
        queryset = CustomButton.objects.filter(organization=self.request.auth.organization)

        if action_name:
            queryset = queryset.filter(name=action_name)

        return queryset

    def perform_create(self, serializer):
        serializer.save()
        instance = serializer.instance
        organization = self.request.auth.organization
        user = self.request.user
        description = f"Custom action {instance.name} was created"
        create_organization_log(organization, user, OrganizationLogType.TYPE_CUSTOM_ACTION_CREATED, description)

    def perform_update(self, serializer):
        organization = self.request.auth.organization
        user = self.request.user
        old_state = serializer.instance.repr_settings_for_client_side_logging
        serializer.save()
        new_state = serializer.instance.repr_settings_for_client_side_logging
        description = f"Custom action {serializer.instance.name} was changed " f"from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(organization, user, OrganizationLogType.TYPE_CUSTOM_ACTION_CHANGED, description)

    def perform_destroy(self, instance):
        organization = self.request.auth.organization
        user = self.request.user
        description = f"Custom action {instance.name} was deleted"
        create_organization_log(organization, user, OrganizationLogType.TYPE_CUSTOM_ACTION_DELETED, description)
        instance.delete()
