import csv
import logging
from datetime import date

from django.http import HttpResponse
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
from apps.schedules.models.on_call_schedule import ScheduleEvents
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
    def oncall_shifts_export(self, request, pk):
        schedule = self.get_object()

        if not isinstance(schedule, OnCallScheduleWeb):
            return Response(
                "OnCall shifts exports are currently only available for web calendars",
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_date_field_name = "start_date"
        end_date_field_name = "end_date"

        def _field_is_required(field_name):
            return Response(f"{field_name} is required", status=status.HTTP_400_BAD_REQUEST)

        def _field_is_invalid_date(field_name):
            return Response(
                f"{field_name} is not a valid date, must be in any valid ISO 8601 format",
                status=status.HTTP_400_BAD_REQUEST,
            )

        def _convert_date(value):
            if not value:
                return None

            try:
                return date.fromisoformat(value)
            except ValueError:
                return None

        start_date_str = request.query_params.get(start_date_field_name, None)
        start_date = _convert_date(start_date_str)

        end_date_str = request.query_params.get(end_date_field_name, None)
        end_date = _convert_date(end_date_str)

        if start_date_str is None:
            return _field_is_required(start_date_field_name)
        elif start_date is None:
            return _field_is_invalid_date(start_date_field_name)
        elif end_date_str is None:
            return _field_is_required(end_date_field_name)
        elif end_date is None:
            return _field_is_invalid_date(end_date_field_name)

        if start_date > end_date:
            return Response(
                f"{start_date_field_name} must be less than or equal to {end_date_field_name}",
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename='export.csv'"

        user_pk_field_name = "user_pk"
        shift_start_field_name = "shift_start"
        shift_end_field_name = "shift_end"
        writer = csv.DictWriter(response, fieldnames=[user_pk_field_name, shift_start_field_name, shift_end_field_name])
        writer.writeheader()

        final_schedule_events: ScheduleEvents = schedule.final_events("UTC", start_date, (end_date - start_date).days)

        logger.info(
            f"Exporting oncall shifts for schedule {pk} between dates {start_date_str} and {end_date_str}. {len(final_schedule_events)} shift events were found."
        )

        for event in final_schedule_events:
            shift_start = event["start"]
            shift_end = event["end"]
            for user in event["users"]:
                writer.writerow(
                    {
                        user_pk_field_name: user["pk"],
                        shift_start_field_name: shift_start,
                        shift_end_field_name: shift_end,
                    }
                )

        return response
