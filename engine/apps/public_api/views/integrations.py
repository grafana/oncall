from django.db.models import Count
from django_filters import rest_framework as filters
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import AlertReceiveChannel
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api import constants as public_api_constants
from apps.public_api.serializers import IntegrationSerializer, IntegrationUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.filters import ByTeamFilter
from common.api_helpers.mixins import (
    DemoTokenMixin,
    FilterSerializerMixin,
    RateLimitHeadersMixin,
    UpdateSerializerMixin,
)
from common.api_helpers.paginators import FiftyPageSizePaginator

from .maintaiable_object_mixin import MaintainableObjectMixin


class IntegrationView(
    RateLimitHeadersMixin,
    DemoTokenMixin,
    FilterSerializerMixin,
    UpdateSerializerMixin,
    MaintainableObjectMixin,
    ModelViewSet,
):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = AlertReceiveChannel
    serializer_class = IntegrationSerializer
    update_serializer_class = IntegrationUpdateSerializer

    pagination_class = FiftyPageSizePaginator

    demo_default_id = public_api_constants.DEMO_INTEGRATION_ID

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ByTeamFilter

    def get_queryset(self):
        queryset = AlertReceiveChannel.objects.filter(organization=self.request.auth.organization).order_by(
            "created_at"
        )
        queryset = self.serializer_class.setup_eager_loading(queryset)
        queryset = queryset.annotate(alert_groups_count_annotated=Count("alert_groups", distinct=True))
        return queryset

    def get_object(self):
        public_primary_key = self.kwargs["pk"]

        try:
            return self.get_queryset().get(public_primary_key=public_primary_key)
        except AlertReceiveChannel.DoesNotExist:
            raise NotFound

    def perform_update(self, serializer):
        old_state = serializer.instance.repr_settings_for_client_side_logging
        serializer.save()
        new_state = serializer.instance.repr_settings_for_client_side_logging
        description = f"Integration settings was changed from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(
            serializer.instance.organization,
            self.request.user,
            OrganizationLogType.TYPE_INTEGRATION_CHANGED,
            description,
        )

    def perform_destroy(self, instance):
        organization = instance.organization
        user = self.request.user
        description = f"Integration {instance.verbal_name} was deleted"
        create_organization_log(organization, user, OrganizationLogType.TYPE_INTEGRATION_DELETED, description)
        instance.delete()
