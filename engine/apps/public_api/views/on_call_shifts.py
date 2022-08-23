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
from common.insight_log import EntityEvent, write_resource_insight_log


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
