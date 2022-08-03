import datetime

import pytz
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import OuterRef, Subquery
from django.db.utils import IntegrityError
from django.urls import reverse
from django.utils import dateparse, timezone
from django.utils.functional import cached_property
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import Response
from rest_framework.viewsets import ModelViewSet

from apps.api.permissions import MODIFY_ACTIONS, READ_ACTIONS, ActionPermission, AnyRole, IsAdmin, IsAdminOrEditor
from apps.api.serializers.schedule_base import ScheduleFastSerializer
from apps.api.serializers.schedule_polymorphic import (
    PolymorphicScheduleCreateSerializer,
    PolymorphicScheduleSerializer,
    PolymorphicScheduleUpdateSerializer,
)
from apps.auth_token.auth import PluginAuthentication
from apps.auth_token.constants import SCHEDULE_EXPORT_TOKEN_NAME
from apps.auth_token.models import ScheduleExportAuthToken
from apps.schedules.ical_utils import list_of_oncall_shifts_from_ical
from apps.schedules.models import OnCallSchedule
from apps.slack.models import SlackChannel
from apps.slack.tasks import update_slack_user_group_for_schedules
from apps.user_management.organization_log_creator import OrganizationLogType, create_organization_log
from common.api_helpers.exceptions import BadRequest, Conflict
from common.api_helpers.mixins import (
    CreateSerializerMixin,
    PublicPrimaryKeyMixin,
    ShortSerializerMixin,
    UpdateSerializerMixin,
)
from common.api_helpers.utils import create_engine_url

EVENTS_FILTER_BY_ROTATION = "rotation"
EVENTS_FILTER_BY_OVERRIDE = "override"
EVENTS_FILTER_BY_FINAL = "final"


class ScheduleView(
    PublicPrimaryKeyMixin, ShortSerializerMixin, CreateSerializerMixin, UpdateSerializerMixin, ModelViewSet
):
    authentication_classes = (PluginAuthentication,)
    permission_classes = (IsAuthenticated, ActionPermission)
    action_permissions = {
        IsAdmin: (
            *MODIFY_ACTIONS,
            "reload_ical",
        ),
        IsAdminOrEditor: ("export_token",),
        AnyRole: (
            *READ_ACTIONS,
            "events",
            "filter_events",
            "next_shifts_per_user",
            "notify_empty_oncall_options",
            "notify_oncall_shift_freq_options",
            "mention_options",
        ),
    }

    queryset = OnCallSchedule.objects.all()
    serializer_class = PolymorphicScheduleSerializer
    create_serializer_class = PolymorphicScheduleCreateSerializer
    update_serializer_class = PolymorphicScheduleUpdateSerializer
    short_serializer_class = ScheduleFastSerializer

    @cached_property
    def can_update_user_groups(self):
        """
        This property is needed to be propagated down to serializers,
        since it makes an API call to Slack and the response should be cached.
        """
        slack_team_identity = self.request.auth.organization.slack_team_identity

        if slack_team_identity is None:
            return False

        user_group = slack_team_identity.usergroups.first()
        if user_group is None:
            return False

        return user_group.can_be_updated

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context.update({"can_update_user_groups": self.can_update_user_groups})
        return context

    def get_queryset(self):
        is_short_request = self.request.query_params.get("short", "false") == "true"
        organization = self.request.auth.organization
        queryset = OnCallSchedule.objects.filter(
            organization=organization,
            team=self.request.user.current_team,
        )
        if not is_short_request:
            slack_channels = SlackChannel.objects.filter(
                slack_team_identity=organization.slack_team_identity,
                slack_id=OuterRef("channel"),
            )
            queryset = queryset.annotate(
                slack_channel_name=Subquery(slack_channels.values("name")[:1]),
                slack_channel_pk=Subquery(slack_channels.values("public_primary_key")[:1]),
            )
            queryset = self.serializer_class.setup_eager_loading(queryset)
        return queryset

    def get_object(self):
        # Override this method because we want to get object from organization instead of concrete team.
        pk = self.kwargs["pk"]
        organization = self.request.auth.organization
        slack_channels = SlackChannel.objects.filter(
            slack_team_identity=organization.slack_team_identity,
            slack_id=OuterRef("channel"),
        )
        queryset = organization.oncall_schedules.filter(public_primary_key=pk,).annotate(
            slack_channel_name=Subquery(slack_channels.values("name")[:1]),
            slack_channel_pk=Subquery(slack_channels.values("public_primary_key")[:1]),
        )

        try:
            obj = queryset.get()
        except ObjectDoesNotExist:
            raise NotFound

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj

    def original_get_object(self):
        return super().get_object()

    def perform_create(self, serializer):
        schedule = serializer.save()
        if schedule.user_group is not None:
            update_slack_user_group_for_schedules.apply_async((schedule.user_group.pk,))
        organization = self.request.auth.organization
        user = self.request.user
        description = f"Schedule {schedule.name} was created"
        create_organization_log(organization, user, OrganizationLogType.TYPE_SCHEDULE_CREATED, description)

    def perform_update(self, serializer):
        organization = self.request.auth.organization
        user = self.request.user
        old_schedule = serializer.instance
        old_state = old_schedule.repr_settings_for_client_side_logging
        old_user_group = serializer.instance.user_group

        updated_schedule = serializer.save()

        if old_user_group is not None:
            update_slack_user_group_for_schedules.apply_async((old_user_group.pk,))

        if updated_schedule.user_group is not None and updated_schedule.user_group != old_user_group:
            update_slack_user_group_for_schedules.apply_async((updated_schedule.user_group.pk,))

        new_state = updated_schedule.repr_settings_for_client_side_logging
        description = f"Schedule {updated_schedule.name} was changed from:\n{old_state}\nto:\n{new_state}"
        create_organization_log(organization, user, OrganizationLogType.TYPE_SCHEDULE_CHANGED, description)

    def perform_destroy(self, instance):
        organization = self.request.auth.organization
        user = self.request.user
        description = f"Schedule {instance.name} was deleted"
        create_organization_log(organization, user, OrganizationLogType.TYPE_SCHEDULE_DELETED, description)
        instance.delete()

        if instance.user_group is not None:
            update_slack_user_group_for_schedules.apply_async((instance.user_group.pk,))

    def get_request_timezone(self):
        user_tz = self.request.query_params.get("user_tz", "UTC")
        try:
            pytz.timezone(user_tz)
        except pytz.exceptions.UnknownTimeZoneError:
            raise BadRequest(detail="Invalid tz format")
        date = timezone.now().date()
        date_param = self.request.query_params.get("date")
        if date_param is not None:
            try:
                date = dateparse.parse_date(date_param)
            except ValueError:
                raise BadRequest(detail="Invalid date format")
            else:
                if date is None:
                    raise BadRequest(detail="Invalid date format")

        return user_tz, date

    def _filter_events(self, schedule, user_timezone, starting_date, days, with_empty, with_gap):
        shifts = (
            list_of_oncall_shifts_from_ical(schedule, starting_date, user_timezone, with_empty, with_gap, days=days)
            or []
        )
        events = []
        # for start, end, users, priority_level, source in shifts:
        for shift in shifts:
            all_day = type(shift["start"]) == datetime.date
            is_gap = shift.get("is_gap", False)
            shift_json = {
                "all_day": all_day,
                "start": shift["start"],
                # fix confusing end date for all-day event
                "end": shift["end"] - timezone.timedelta(days=1) if all_day else shift["end"],
                "users": [
                    {
                        "display_name": user.username,
                        "pk": user.public_primary_key,
                    }
                    for user in shift["users"]
                ],
                "missing_users": shift["missing_users"],
                "priority_level": shift["priority"] if shift["priority"] != 0 else None,
                "source": shift["source"],
                "calendar_type": shift["calendar_type"],
                "is_empty": len(shift["users"]) == 0 and not is_gap,
                "is_gap": is_gap,
                "is_override": shift["calendar_type"] == OnCallSchedule.TYPE_ICAL_OVERRIDES,
                "shift": {
                    "pk": shift["shift_pk"],
                },
            }
            events.append(shift_json)

        return events

    @action(detail=True, methods=["get"])
    def events(self, request, pk):
        user_tz, date = self.get_request_timezone()
        with_empty = self.request.query_params.get("with_empty", False) == "true"
        with_gap = self.request.query_params.get("with_gap", False) == "true"

        schedule = self.original_get_object()
        events = self._filter_events(schedule, user_tz, date, days=1, with_empty=with_empty, with_gap=with_gap)

        slack_channel = (
            {
                "id": schedule.slack_channel_pk,
                "slack_id": schedule.channel,
                "display_name": schedule.slack_channel_name,
            }
            if schedule.channel is not None
            else None
        )

        result = {
            "id": schedule.public_primary_key,
            "name": schedule.name,
            "type": PolymorphicScheduleSerializer().to_resource_type(schedule),
            "slack_channel": slack_channel,
            "events": events,
        }
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def filter_events(self, request, pk):
        user_tz, date = self.get_request_timezone()
        filter_by = self.request.query_params.get("type")

        valid_filters = (EVENTS_FILTER_BY_ROTATION, EVENTS_FILTER_BY_OVERRIDE, EVENTS_FILTER_BY_FINAL)
        if filter_by is not None and filter_by not in valid_filters:
            raise BadRequest(detail="Invalid type value")
        resolve_schedule = filter_by is None or filter_by == EVENTS_FILTER_BY_FINAL

        starting_date = date if self.request.query_params.get("date") else None
        if starting_date is None:
            # default to current week start
            starting_date = date - datetime.timedelta(days=date.weekday())

        try:
            days = int(self.request.query_params.get("days", 7))  # fallback to a week
        except ValueError:
            raise BadRequest(detail="Invalid days format")

        schedule = self.original_get_object()
        events = self._filter_events(
            schedule, user_tz, starting_date, days=days, with_empty=True, with_gap=resolve_schedule
        )

        if filter_by == EVENTS_FILTER_BY_OVERRIDE:
            events = [e for e in events if e["calendar_type"] == OnCallSchedule.OVERRIDES]
        elif filter_by == EVENTS_FILTER_BY_ROTATION:
            events = [e for e in events if e["calendar_type"] == OnCallSchedule.PRIMARY]
        else:  # resolve_schedule
            events = self._resolve_schedule(events)

        result = {
            "id": schedule.public_primary_key,
            "name": schedule.name,
            "type": PolymorphicScheduleSerializer().to_resource_type(schedule),
            "events": events,
        }
        return Response(result, status=status.HTTP_200_OK)

    def _resolve_schedule(self, events):
        """Calculate final schedule shifts considering rotations and overrides."""
        if not events:
            return []

        # sort schedule events by (type desc, priority desc, start timestamp asc)
        events.sort(
            key=lambda e: (
                -e["calendar_type"] if e["calendar_type"] else 0,  # overrides: 1, shifts: 0, gaps: None
                -e["priority_level"] if e["priority_level"] else 0,
                e["start"],
            )
        )

        def _merge_intervals(evs):
            """Keep track of scheduled intervals."""
            if not evs:
                return []
            intervals = [[e["start"], e["end"]] for e in evs]
            result = [intervals[0]]
            for interval in intervals[1:]:
                previous_interval = result[-1]
                if previous_interval[0] <= interval[0] <= previous_interval[1]:
                    previous_interval[1] = max(previous_interval[1], interval[1])
                else:
                    result.append(interval)
            return result

        # iterate over events, reserving schedule slots based on their priority
        # if the expected slot was already scheduled for a higher priority event,
        # split the event, or fix start/end timestamps accordingly

        # include overrides from start
        resolved = [e for e in events if e["calendar_type"] == OnCallSchedule.TYPE_ICAL_OVERRIDES]
        intervals = _merge_intervals(resolved)

        pending = events[len(resolved) :]
        if not pending:
            return resolved

        current_event_idx = 0  # current event to resolve
        current_interval_idx = 0  # current scheduled interval being checked
        current_priority = pending[0]["priority_level"]  # current priority level being resolved

        while current_event_idx < len(pending):
            ev = pending[current_event_idx]

            if ev["priority_level"] != current_priority:
                # update scheduled intervals on priority change
                # and start from the beginning for the new priority level
                resolved.sort(key=lambda e: e["start"])
                intervals = _merge_intervals(resolved)
                current_interval_idx = 0
                current_priority = ev["priority_level"]

            if current_interval_idx >= len(intervals):
                # event outside scheduled intervals, add to resolved
                resolved.append(ev)
                current_event_idx += 1
            elif ev["start"] < intervals[current_interval_idx][0] and ev["end"] <= intervals[current_interval_idx][0]:
                # event starts and ends outside an already scheduled interval, add to resolved
                resolved.append(ev)
                current_event_idx += 1
            elif ev["start"] < intervals[current_interval_idx][0] and ev["end"] > intervals[current_interval_idx][0]:
                # event starts outside interval but overlaps with an already scheduled interval
                # 1. add a split event copy to schedule the time before the already scheduled interval
                to_add = ev.copy()
                to_add["end"] = intervals[current_interval_idx][0]
                resolved.append(to_add)
                # 2. check if there is still time to be scheduled after the current scheduled interval ends
                if ev["end"] > intervals[current_interval_idx][1]:
                    # event ends after current interval, update event start timestamp to match the interval end
                    # and process the updated event as any other event
                    ev["start"] = intervals[current_interval_idx][1]
                else:
                    # done, go to next event
                    current_event_idx += 1
            elif ev["start"] >= intervals[current_interval_idx][0] and ev["end"] <= intervals[current_interval_idx][1]:
                # event inside an already scheduled interval, ignore (go to next)
                current_event_idx += 1
            elif (
                ev["start"] >= intervals[current_interval_idx][0]
                and ev["start"] < intervals[current_interval_idx][1]
                and ev["end"] > intervals[current_interval_idx][1]
            ):
                # event starts inside a scheduled interval but ends out of it
                # update the event start timestamp to match the interval end
                ev["start"] = intervals[current_interval_idx][1]
                # move to next interval and process the updated event as any other event
                current_interval_idx += 1
            elif ev["start"] >= intervals[current_interval_idx][1]:
                # event starts after the current interval, move to next interval and go through it
                current_interval_idx += 1

        resolved.sort(key=lambda e: e["start"])
        return resolved

    @action(detail=True, methods=["get"])
    def next_shifts_per_user(self, request, pk):
        """Return next shift for users in schedule."""
        user_tz, _ = self.get_request_timezone()
        now = timezone.now()
        starting_date = now.date()
        schedule = self.original_get_object()
        shift_events = self._filter_events(schedule, user_tz, starting_date, days=30, with_empty=False, with_gap=False)
        events = self._resolve_schedule(shift_events)

        users = {}
        for e in events:
            user = e["users"][0]["pk"] if e["users"] else None
            if user is not None and user not in users and e["end"] > now:
                users[user] = e

        result = {"users": users}
        return Response(result, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def type_options(self, request):
        # TODO: check if it needed
        choices = []
        for item in OnCallSchedule.SCHEDULE_CHOICES:
            choices.append({"value": str(item[0]), "display_name": item[1]})
        return Response(choices)

    @action(detail=True, methods=["post"])
    def reload_ical(self, request, pk):
        schedule = self.original_get_object()
        schedule.drop_cached_ical()
        schedule.check_empty_shifts_for_next_week()
        schedule.check_gaps_for_next_week()

        if schedule.user_group is not None:
            update_slack_user_group_for_schedules.apply_async((schedule.user_group.pk,))

        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=["get", "post", "delete"])
    def export_token(self, request, pk):
        schedule = self.original_get_object()

        if self.request.method == "GET":
            try:
                token = ScheduleExportAuthToken.objects.get(user_id=self.request.user.id, schedule_id=schedule.id)
            except ScheduleExportAuthToken.DoesNotExist:
                raise NotFound

            response = {
                "created_at": token.created_at,
                "revoked_at": token.revoked_at,
                "active": token.active,
            }

            return Response(response, status=status.HTTP_200_OK)

        if self.request.method == "POST":
            try:
                instance, token = ScheduleExportAuthToken.create_auth_token(
                    request.user, request.user.organization, schedule
                )
            except IntegrityError:
                raise Conflict("Schedule export token for user already exists")

            export_url = create_engine_url(
                reverse("api-public:schedules-export", kwargs={"pk": schedule.public_primary_key})
                + f"?{SCHEDULE_EXPORT_TOKEN_NAME}={token}"
            )

            data = {"token": token, "created_at": instance.created_at, "export_url": export_url}

            return Response(data, status=status.HTTP_201_CREATED)

        if self.request.method == "DELETE":
            try:
                token = ScheduleExportAuthToken.objects.get(user_id=self.request.user.id, schedule_id=schedule.id)
                token.delete()
            except ScheduleExportAuthToken.DoesNotExist:
                raise NotFound

            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def notify_oncall_shift_freq_options(self, request):
        options = []
        for choice in OnCallSchedule.NotifyOnCallShiftFreq.choices:
            options.append(
                {
                    "value": choice[0],
                    "display_name": choice[1],
                }
            )
        return Response(options)

    @action(detail=False, methods=["get"])
    def notify_empty_oncall_options(self, request):
        options = []
        for choice in OnCallSchedule.NotifyEmptyOnCall.choices:
            options.append(
                {
                    "value": choice[0],
                    "display_name": choice[1],
                }
            )
        return Response(options)

    @action(detail=False, methods=["get"])
    def mention_options(self, request):
        options = [
            {
                "value": False,
                "display_name": "Inform in channel without mention",
            },
            {
                "value": True,
                "display_name": "Mention person in slack",
            },
        ]
        return Response(options)
