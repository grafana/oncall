from django_filters import rest_framework as filters
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import Response
from rest_framework.viewsets import ModelViewSet

from apps.auth_token.auth import ApiTokenAuthentication, ScheduleExportAuthentication
from apps.public_api.custom_renderers import CalendarRenderer
from apps.public_api.serializers import PolymorphicScheduleSerializer, PolymorphicScheduleUpdateSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.schedules.ical_utils import ical_export_from_schedule
from apps.schedules.models import OnCallSchedule, OnCallScheduleWeb
from apps.slack.tasks import update_slack_user_group_for_schedules
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import ByTeamFilter
from common.api_helpers.mixins import RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator
from common.insight_logs import entity_created_insight_logs, entity_deleted_insight_logs, entity_updated_insight_logs


class OnCallScheduleChannelView(RateLimitHeadersMixin, UpdateSerializerMixin, ModelViewSet):
    authentication_classes = (ApiTokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    throttle_classes = [UserThrottle]

    model = OnCallSchedule
    serializer_class = PolymorphicScheduleSerializer
    update_serializer_class = PolymorphicScheduleUpdateSerializer

    pagination_class = FiftyPageSizePaginator

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ByTeamFilter

    def get_queryset(self):
        name = self.request.query_params.get("name", None)

        queryset = OnCallSchedule.objects.filter(organization=self.request.auth.organization)

        if name is not None:
            queryset = queryset.filter(name=name)

        return queryset.order_by("id")

    def get_object(self):
        public_primary_key = self.kwargs["pk"]

        try:
            return OnCallSchedule.objects.filter(
                organization=self.request.auth.organization,
            ).get(public_primary_key=public_primary_key)
        except OnCallSchedule.DoesNotExist:
            raise NotFound

    def perform_create(self, serializer):
        if serializer.validated_data["type"] == "web":
            raise BadRequest(detail="Web schedule creation is not enabled through API")

        serializer.save()
        instance = serializer.instance

        if instance.user_group is not None:
            update_slack_user_group_for_schedules.apply_async((instance.user_group.pk,))

        entity_created_insight_logs(instance, self.request.user)

    def perform_update(self, serializer):
        if isinstance(serializer.instance, OnCallScheduleWeb):
            raise BadRequest(detail="Web schedule update is not enabled through API")

        old_state = serializer.instance.repr_settings_for_client_side_logging
        old_user_group = serializer.instance.user_group

        updated_schedule = serializer.save()

        if old_user_group is not None:
            update_slack_user_group_for_schedules.apply_async((old_user_group.pk,))

        if updated_schedule.user_group is not None and updated_schedule.user_group != old_user_group:
            update_slack_user_group_for_schedules.apply_async((updated_schedule.user_group.pk,))

        new_state = serializer.instance.repr_settings_for_client_side_logging
        entity_updated_insight_logs(updated_schedule, self.request.user, old_state, new_state)

    def perform_destroy(self, instance):
        entity_deleted_insight_logs(instance, self.request.user)

        instance.delete()

        if instance.user_group is not None:
            update_slack_user_group_for_schedules.apply_async((instance.user_group.pk,))

    @action(
        methods=["get"],
        detail=True,
        renderer_classes=(CalendarRenderer,),
        authentication_classes=(ScheduleExportAuthentication,),
        permission_classes=(IsAuthenticated,),
    )
    def export(self, request, pk):
        # Not using existing get_object method because it requires access to the organization user attribute
        export = ical_export_from_schedule(self.request.auth.schedule)
        return Response(export, status=status.HTTP_200_OK)
