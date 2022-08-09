from django_filters import rest_framework as filters
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.alerts.models import CustomButton
from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers.action import ActionCreateSerializer, ActionUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from common.api_helpers.filters import ByTeamFilter
from common.api_helpers.mixins import PublicPrimaryKeyMixin, RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator
from common.insight_logs import entity_created_insight_logs, entity_deleted_insight_logs, entity_updated_insight_logs


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
        entity_created_insight_logs(serializer.instance, self.request.user)

    def perform_update(self, serializer):
        old_state = serializer.instance.insight_logs_dict
        serializer.save()
        new_state = serializer.instance.insight_logs_dict
        entity_updated_insight_logs(serializer.instance, self.request.user, old_state, new_state)

    def perform_destroy(self, instance):
        entity_deleted_insight_logs(instance, self.request.user)
        instance.delete()
