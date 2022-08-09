from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.auth_token.auth import ApiTokenAuthentication
from apps.public_api.serializers import CustomOnCallShiftSerializer, CustomOnCallShiftUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.schedules.models import CustomOnCallShift
from common.api_helpers.filters import ByTeamFilter
from common.api_helpers.mixins import RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator
from common.insight_logs import entity_created_insight_logs, entity_deleted_insight_logs, entity_updated_insight_logs


class CustomOnCallShiftView(RateLimitHeadersMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = CustomOnCallShift
    serializer_class = CustomOnCallShiftSerializer
    update_serializer_class = CustomOnCallShiftUpdateSerializer

    pagination_class = FiftyPageSizePaginator

    filter_backends = [DjangoFilterBackend]
    filterset_class = ByTeamFilter

    def get_queryset(self):
        name = self.request.query_params.get("name", None)
        schedule_id = self.request.query_params.get("schedule_id", None)

        queryset = CustomOnCallShift.objects.filter(organization=self.request.auth.organization)

        if schedule_id:
            queryset = queryset.filter(schedules__public_primary_key=schedule_id)
        if name:
            queryset = queryset.filter(name=name)
        return queryset.order_by("schedules")

    def get_object(self):
        public_primary_key = self.kwargs["pk"]

        try:
            return CustomOnCallShift.objects.filter(
                organization=self.request.auth.organization,
            ).get(public_primary_key=public_primary_key)
        except CustomOnCallShift.DoesNotExist:
            raise NotFound

    def perform_create(self, serializer):
        serializer.save()
        entity_created_insight_logs(instance=serializer.instance, user=self.request.user)

    def perform_update(self, serializer):
        old_state = serializer.instance.repr_settings_for_client_side_logging
        serializer.save()
        new_state = serializer.instance.repr_settings_for_client_side_logging
        entity_updated_insight_logs(
            instance=serializer.instance, user=self.request.user, before=old_state, after=new_state
        )

    def perform_destroy(self, instance):
        entity_deleted_insight_logs(instance=instance, user=self.request.user)
        instance.delete()
