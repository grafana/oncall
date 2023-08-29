import datetime
import logging

import pytz
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
from apps.public_api.serializers.schedules_base import FinalShiftQueryParamsSerializer
from apps.public_api.throttlers.user_throttle import UserThrottle
from apps.schedules.ical_utils import ical_export_from_schedule
from apps.schedules.models import OnCallSchedule, OnCallScheduleWeb
from apps.schedules.models.on_call_schedule import ScheduleEvents, ScheduleFinalShifts
from apps.slack.tasks import update_slack_user_group_for_schedules
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.filters import ByTeamFilter
from common.api_helpers.mixins import RateLimitHeadersMixin, UpdateSerializerMixin
from common.api_helpers.paginators import FiftyPageSizePaginator
from common.insight_log import EntityEvent, write_resource_insight_log

logger = logging.getLogger(__name__)


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

    # self.get_object() is not used in export action because ScheduleExportAuthentication is used
    extra_actions_ignore_no_get_object = ["export"]

    def get_queryset(self):
        name = self.request.query_params.get("name", None)

        queryset = OnCallSchedule.objects.filter(organization=self.request.auth.organization).defer(
            # avoid requesting large text fields which are not used when listing schedules
            "prev_ical_file_primary",
            "prev_ical_file_overrides",
            "cached_ical_final_schedule",
        )

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
        serializer.save()
        instance = serializer.instance

        if instance.user_group is not None:
            update_slack_user_group_for_schedules.apply_async((instance.user_group.pk,))

        write_resource_insight_log(
            instance=serializer.instance,
            author=self.request.user,
            event=EntityEvent.CREATED,
        )

    def perform_update(self, serializer):
        if isinstance(serializer.instance, OnCallScheduleWeb):
            raise BadRequest(detail="Web schedule update is not enabled through API")

        prev_state = serializer.instance.insight_logs_serialized
        old_user_group = serializer.instance.user_group

        updated_schedule = serializer.save()

        if old_user_group is not None:
            update_slack_user_group_for_schedules.apply_async((old_user_group.pk,))

        if updated_schedule.user_group is not None and updated_schedule.user_group != old_user_group:
            update_slack_user_group_for_schedules.apply_async((updated_schedule.user_group.pk,))

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

    @action(methods=["get"], detail=True)
    def final_shifts(self, request, pk):
        schedule = self.get_object()

        serializer = FinalShiftQueryParamsSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        start_date = serializer.validated_data["start_date"]
        end_date = serializer.validated_data["end_date"]
        days_between_start_and_end = (end_date - start_date).days

        datetime_start = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=pytz.UTC)
        datetime_end = datetime_start + datetime.timedelta(
            days=days_between_start_and_end - 1, hours=23, minutes=59, seconds=59
        )

        final_schedule_events: ScheduleEvents = schedule.final_events(datetime_start, datetime_end)
        logger.info(
            f"Exporting oncall shifts for schedule {pk} between dates {start_date} and {end_date}. {len(final_schedule_events)} shift events were found."
        )

        data: ScheduleFinalShifts = [
            {
                "user_pk": user["pk"],
                "user_email": user["email"],
                "user_username": user["display_name"],
                "shift_start": event["start"],
                "shift_end": event["end"],
            }
            for event in final_schedule_events
            for user in event["users"]
        ]

        # right now we'll "mock out" the pagination related parameters (next and previous)
        # rather than use a Pagination class from drf (as currently it operates on querysets). We've decided on this
        # to make this response schema consistent with the rest of the public API + make it easy to add pagination
        # here in the future (should we decide to migrate "final_shifts" to an actual model)
        return Response(
            {
                "count": len(data),
                "next": None,
                "previous": None,
                "results": data,
                "current_page_number": 1,
                "page_size": 50,
                "total_pages": 1,
            }
        )
