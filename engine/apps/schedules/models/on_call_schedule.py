import datetime
import itertools

import icalendar
from django.apps import apps
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from icalendar.cal import Calendar
from polymorphic.managers import PolymorphicManager
from polymorphic.models import PolymorphicModel
from polymorphic.query import PolymorphicQuerySet

from apps.schedules.ical_utils import (
    fetch_ical_file_or_get_error,
    list_of_empty_shifts_in_schedule,
    list_of_gaps_in_schedule,
    list_of_oncall_shifts_from_ical,
    list_users_to_notify_from_ical,
)
from apps.schedules.models import CustomOnCallShift
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length


def generate_public_primary_key_for_oncall_schedule_channel():
    prefix = "S"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while OnCallSchedule.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="OnCallSchedule"
        )
        failure_counter += 1

    return new_public_primary_key


class OnCallScheduleQuerySet(PolymorphicQuerySet):
    def get_oncall_users(self, events_datetime=None):
        if events_datetime is None:
            events_datetime = timezone.datetime.now(timezone.utc)

        users = set()

        for schedule in self.all():
            schedule_oncall_users = list_users_to_notify_from_ical(schedule, events_datetime=events_datetime)
            if schedule_oncall_users is None:
                continue

            users.update(schedule_oncall_users)

        return list(users)


class OnCallSchedule(PolymorphicModel):
    objects = PolymorphicManager.from_queryset(OnCallScheduleQuerySet)()

    # type of calendars in schedule
    TYPE_ICAL_PRIMARY, TYPE_ICAL_OVERRIDES, TYPE_CALENDAR = range(
        3
    )  # todo: discuss do we need the third type  (this types used for frontend)
    PRIMARY, OVERRIDES = range(2)
    CALENDAR_TYPE_VERBAL = {PRIMARY: "primary", OVERRIDES: "overrides"}

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_oncall_schedule_channel,
    )

    cached_ical_file_primary = models.TextField(null=True, default=None)
    prev_ical_file_primary = models.TextField(null=True, default=None)

    cached_ical_file_overrides = models.TextField(null=True, default=None)
    prev_ical_file_overrides = models.TextField(null=True, default=None)

    organization = models.ForeignKey(
        "user_management.Organization", on_delete=models.CASCADE, related_name="oncall_schedules"
    )

    team = models.ForeignKey(
        "user_management.Team",
        on_delete=models.SET_NULL,
        related_name="oncall_schedules",
        null=True,
        default=None,
    )

    name = models.CharField(max_length=200)
    channel = models.CharField(max_length=100, null=True, default=None)

    # Slack user group to be updated when on-call users change for this schedule
    user_group = models.ForeignKey(
        to="slack.SlackUserGroup", null=True, on_delete=models.SET_NULL, related_name="oncall_schedules"
    )

    # schedule reminder related fields
    class NotifyOnCallShiftFreq(models.IntegerChoices):
        NEVER = 0, "Never"
        EACH_SHIFT = 1, "Each shift"

    class NotifyEmptyOnCall(models.IntegerChoices):
        ALL = 0, "Notify all people in the channel"
        PREV = 1, "Mention person from the previous slot"
        NO_ONE = 2, "Inform about empty slot"

    current_shifts = models.TextField(null=False, default="{}")
    # Used to not drop current_shifts to use them when "Mention person from the previous slot"
    empty_oncall = models.BooleanField(default=True)
    notify_oncall_shift_freq = models.IntegerField(
        null=False,
        choices=NotifyOnCallShiftFreq.choices,
        default=NotifyOnCallShiftFreq.EACH_SHIFT,
    )
    mention_oncall_start = models.BooleanField(null=False, default=True)
    mention_oncall_next = models.BooleanField(null=False, default=False)
    notify_empty_oncall = models.IntegerField(
        null=False, choices=NotifyEmptyOnCall.choices, default=NotifyEmptyOnCall.ALL
    )

    # Gaps-checker related fields
    has_gaps = models.BooleanField(default=False)
    gaps_report_sent_at = models.DateField(null=True, default=None)

    # empty shifts checker related fields
    has_empty_shifts = models.BooleanField(default=False)
    empty_shifts_report_sent_at = models.DateField(null=True, default=None)

    class Meta:
        unique_together = ("name", "organization")

    @property
    def repr_settings_for_client_side_logging(self):
        """
        Example of execution:
            name: test, team: example, url: None
            slack reminder settings: notification frequency: Each shift, current shift notification: Yes,
            next shift notification: No, action for slot when no one is on-call: Notify all people in the channel
        """
        result = f"name: {self.name}, team: {self.team.name if self.team else 'No team'}"

        if self.organization.slack_team_identity:
            if self.channel:
                SlackChannel = apps.get_model("slack", "SlackChannel")
                sti = self.organization.slack_team_identity
                slack_channel = SlackChannel.objects.filter(slack_team_identity=sti, slack_id=self.channel).first()
                if slack_channel:
                    result += f", slack channel: {slack_channel.name}"

            if self.user_group is not None:
                result += f", user group: {self.user_group.handle}"

            result += (
                f"\nslack reminder settings: "
                f"notification frequency: {self.get_notify_oncall_shift_freq_display()}, "
                f"current shift notification: {'Yes' if self.mention_oncall_start else 'No'}, "
                f"next shift notification: {'Yes' if self.mention_oncall_next else 'No'}, "
                f"action for slot when no one is on-call: {self.get_notify_empty_oncall_display()}"
            )
        return result

    def get_icalendars(self):
        """Returns list of calendars. Primary calendar should always be the first"""
        calendar_primary = None
        calendar_overrides = None
        if self._ical_file_primary is not None:
            calendar_primary = icalendar.Calendar.from_ical(self._ical_file_primary)
        if self._ical_file_overrides is not None:
            calendar_overrides = icalendar.Calendar.from_ical(self._ical_file_overrides)
        return calendar_primary, calendar_overrides

    def get_prev_and_current_ical_files(self):
        """Returns list of tuples with prev and current iCal files for each calendar"""
        return [
            (self.prev_ical_file_primary, self.cached_ical_file_primary),
            (self.prev_ical_file_overrides, self.cached_ical_file_overrides),
        ]

    def check_gaps_for_next_week(self):
        today = timezone.now().date()
        gaps = list_of_gaps_in_schedule(self, today, today + timezone.timedelta(days=7))
        has_gaps = len(gaps) != 0
        self.has_gaps = has_gaps
        self.save(update_fields=["has_gaps"])
        return has_gaps

    def check_empty_shifts_for_next_week(self):
        today = timezone.now().date()
        empty_shifts = list_of_empty_shifts_in_schedule(self, today, today + timezone.timedelta(days=7))
        has_empty_shifts = len(empty_shifts) != 0
        self.has_empty_shifts = has_empty_shifts
        self.save(update_fields=["has_empty_shifts"])
        return has_empty_shifts

    def drop_cached_ical(self):
        self._drop_primary_ical_file()
        self._drop_overrides_ical_file()

    def refresh_ical_file(self):
        self._refresh_primary_ical_file()
        self._refresh_overrides_ical_file()

    def _ical_file_primary(self):
        raise NotImplementedError

    def _ical_file_overrides(self):
        raise NotImplementedError

    def _refresh_primary_ical_file(self):
        raise NotImplementedError

    def _refresh_overrides_ical_file(self):
        raise NotImplementedError

    def _drop_primary_ical_file(self):
        self.prev_ical_file_primary = self.cached_ical_file_primary
        self.cached_ical_file_primary = None
        self.save(update_fields=["cached_ical_file_primary", "prev_ical_file_primary"])

    def _drop_overrides_ical_file(self):
        self.prev_ical_file_overrides = self.cached_ical_file_overrides
        self.cached_ical_file_overrides = None
        self.save(update_fields=["cached_ical_file_overrides", "prev_ical_file_overrides"])

    def filter_events(self, user_timezone, starting_date, days, with_empty=False, with_gap=False, filter_by=None):
        """Return filtered events from schedule."""
        shifts = (
            list_of_oncall_shifts_from_ical(
                self, starting_date, user_timezone, with_empty, with_gap, days=days, filter_by=filter_by
            )
            or []
        )
        events = []
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

        # combine multiple-users same-shift events into one
        events = self._merge_events(events)

        return events

    def final_events(self, user_tz, starting_date, days):
        """Return schedule final events, after resolving shifts and overrides."""
        events = self.filter_events(user_tz, starting_date, days=days, with_empty=True, with_gap=True)
        events = self._resolve_schedule(events)
        return events

    def _resolve_schedule(self, events):
        """Calculate final schedule shifts considering rotations and overrides."""
        if not events:
            return []

        def event_cmp_key(e):
            """Sorting key criteria for events."""
            return (
                -e["calendar_type"] if e["calendar_type"] else 0,  # overrides: 1, shifts: 0, gaps: None
                -e["priority_level"] if e["priority_level"] else 0,
                e["start"],
            )

        def insort_event(eventlist, e):
            """Insert event keeping ordering criteria into already sorted event list."""
            idx = 0
            for i in eventlist:
                if event_cmp_key(e) > event_cmp_key(i):
                    idx += 1
                else:
                    break
            eventlist.insert(idx, e)

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

        # sort schedule events by (type desc, priority desc, start timestamp asc)
        events.sort(key=event_cmp_key)

        # iterate over events, reserving schedule slots based on their priority
        # if the expected slot was already scheduled for a higher priority event,
        # split the event, or fix start/end timestamps accordingly

        intervals = []
        resolved = []
        pending = events
        current_interval_idx = 0  # current scheduled interval being checked
        current_priority = None  # current priority level being resolved

        while pending:
            ev = pending.pop(0)

            if ev["calendar_type"] == OnCallSchedule.TYPE_ICAL_OVERRIDES:
                # include overrides from start
                resolved.append(ev)
                continue

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

            elif ev["start"] < intervals[current_interval_idx][0] and ev["end"] <= intervals[current_interval_idx][0]:
                # event starts and ends outside an already scheduled interval, add to resolved
                resolved.append(ev)

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
                    # reorder pending events after updating current event start date
                    # (ie. insert the event where it should be to keep the order criteria)
                    # TODO: switch to bisect insert on python 3.10 (or consider heapq)
                    insort_event(pending, ev)
                # done, go to next event

            elif ev["start"] >= intervals[current_interval_idx][0] and ev["end"] <= intervals[current_interval_idx][1]:
                # event inside an already scheduled interval, ignore (go to next)
                continue

            elif (
                ev["start"] >= intervals[current_interval_idx][0]
                and ev["start"] < intervals[current_interval_idx][1]
                and ev["end"] > intervals[current_interval_idx][1]
            ):
                # event starts inside a scheduled interval but ends out of it
                # update the event start timestamp to match the interval end
                ev["start"] = intervals[current_interval_idx][1]
                # unresolved, re-add to pending
                # TODO: switch to bisect insert on python 3.10 (or consider heapq)
                insort_event(pending, ev)

            elif ev["start"] >= intervals[current_interval_idx][1]:
                # event starts after the current interval, move to next interval and go through it
                current_interval_idx += 1
                # unresolved, re-add to pending
                # TODO: switch to bisect insert on python 3.10 (or consider heapq)
                insort_event(pending, ev)

        resolved.sort(key=lambda e: (e["start"], e["shift"]["pk"]))
        return resolved

    def _merge_events(self, events):
        """Merge user groups same-shift events."""
        if events:
            merged = [events[0]]
            current = merged[0]
            for next_event in events[1:]:
                if (
                    current["start"] == next_event["start"]
                    and current["shift"]["pk"] is not None
                    and current["shift"]["pk"] == next_event["shift"]["pk"]
                ):
                    current["users"] += next_event["users"]
                    current["missing_users"] += next_event["missing_users"]
                else:
                    merged.append(next_event)
                    current = next_event
            events = merged
        return events


class OnCallScheduleICal(OnCallSchedule):
    # For the ical schedule both primary and overrides icals are imported via ical url
    ical_url_primary = models.CharField(max_length=500, null=True, default=None)
    ical_file_error_primary = models.CharField(max_length=200, null=True, default=None)

    ical_url_overrides = models.CharField(max_length=500, null=True, default=None)
    ical_file_error_overrides = models.CharField(max_length=200, null=True, default=None)

    @cached_property
    def _ical_file_primary(self):
        """
        Download iCal file imported from calendar
        """
        cached_ical_file = self.cached_ical_file_primary
        if self.ical_url_primary is not None and self.cached_ical_file_primary is None:
            self.cached_ical_file_primary, self.ical_file_error_primary = fetch_ical_file_or_get_error(
                self.ical_url_primary
            )
            self.save(update_fields=["cached_ical_file_primary", "ical_file_error_primary"])
            cached_ical_file = self.cached_ical_file_primary
        return cached_ical_file

    @cached_property
    def _ical_file_overrides(self):
        """
        Download iCal file imported from calendar
        """
        cached_ical_file = self.cached_ical_file_overrides
        if self.ical_url_overrides is not None and self.cached_ical_file_overrides is None:
            self.cached_ical_file_overrides, self.ical_file_error_overrides = fetch_ical_file_or_get_error(
                self.ical_url_overrides
            )
            self.save(update_fields=["cached_ical_file_overrides", "ical_file_error_overrides"])
            cached_ical_file = self.cached_ical_file_overrides
        return cached_ical_file

    def _refresh_primary_ical_file(self):
        self.prev_ical_file_primary = self.cached_ical_file_primary
        if self.ical_url_primary is not None:
            self.cached_ical_file_primary, self.ical_file_error_primary = fetch_ical_file_or_get_error(
                self.ical_url_primary,
            )
        self.save(update_fields=["cached_ical_file_primary", "prev_ical_file_primary", "ical_file_error_primary"])

    def _refresh_overrides_ical_file(self):
        self.prev_ical_file_overrides = self.cached_ical_file_overrides
        if self.ical_url_overrides is not None:
            self.cached_ical_file_overrides, self.ical_file_error_overrides = fetch_ical_file_or_get_error(
                self.ical_url_overrides,
            )
        self.save(update_fields=["cached_ical_file_overrides", "prev_ical_file_overrides", "ical_file_error_overrides"])

    @property
    def repr_settings_for_client_side_logging(self):
        result = super().repr_settings_for_client_side_logging
        result += (
            f", primary calendar url: {self.ical_url_primary}, " f"overrides calendar url: {self.ical_url_overrides}"
        )
        return result


class OnCallScheduleCalendar(OnCallSchedule):
    # For the calendar schedule only overrides ical is imported via ical url.
    ical_url_overrides = models.CharField(max_length=500, null=True, default=None)
    ical_file_error_overrides = models.CharField(max_length=200, null=True, default=None)

    # Primary ical is generated from custom_on_call_shifts.
    time_zone = models.CharField(max_length=100, default="UTC")
    custom_on_call_shifts = models.ManyToManyField("schedules.CustomOnCallShift", related_name="schedules")

    @cached_property
    def _ical_file_primary(self):
        """
        Return cached ical file with iCal events from custom on-call shifts
        """
        if self.cached_ical_file_primary is None:
            self.cached_ical_file_primary = self._generate_ical_file_primary()
            self.save(update_fields=["cached_ical_file_primary"])
        return self.cached_ical_file_primary

    @cached_property
    def _ical_file_overrides(self):
        """
        Download iCal file imported from calendar
        """
        cached_ical_file = self.cached_ical_file_overrides
        if self.ical_url_overrides is not None and self.cached_ical_file_overrides is None:
            self.cached_ical_file_overrides, self.ical_file_error_overrides = fetch_ical_file_or_get_error(
                self.ical_url_overrides
            )
            self.save(update_fields=["cached_ical_file_overrides", "ical_file_error_overrides"])
            cached_ical_file = self.cached_ical_file_overrides
        return cached_ical_file

    def _refresh_primary_ical_file(self):
        self.prev_ical_file_primary = self.cached_ical_file_primary
        self.cached_ical_file_primary = self._generate_ical_file_primary()
        self.save(
            update_fields=[
                "cached_ical_file_primary",
                "prev_ical_file_primary",
            ]
        )

    def _refresh_overrides_ical_file(self):
        self.prev_ical_file_overrides = self.cached_ical_file_overrides
        if self.ical_url_overrides is not None:
            self.cached_ical_file_overrides, self.ical_file_error_overrides = fetch_ical_file_or_get_error(
                self.ical_url_overrides,
            )
        self.save(update_fields=["cached_ical_file_overrides", "prev_ical_file_overrides", "ical_file_error_overrides"])

    def _generate_ical_file_primary(self):
        """
        Generate iCal events file from custom on-call shifts (created via API)
        """
        ical = None
        if self.custom_on_call_shifts.exists():
            end_line = "END:VCALENDAR"
            calendar = Calendar()
            calendar.add("prodid", "-//My calendar product//amixr//")
            calendar.add("version", "2.0")
            calendar.add("method", "PUBLISH")
            ical_file = calendar.to_ical().decode()
            ical = ical_file.replace(end_line, "").strip()
            ical = f"{ical}\r\n"
            for event in self.custom_on_call_shifts.all():
                ical += event.convert_to_ical(self.time_zone)
            ical += f"{end_line}\r\n"
        return ical

    @property
    def repr_settings_for_client_side_logging(self):
        result = super().repr_settings_for_client_side_logging
        result += f", overrides calendar url: {self.ical_url_overrides}"
        return result


class OnCallScheduleWeb(OnCallSchedule):
    time_zone = models.CharField(max_length=100, default="UTC")

    def _generate_ical_file_from_shifts(self, qs, extra_shifts=None):
        """Generate iCal events file from custom on-call shifts."""
        ical = None
        if qs.exists() or extra_shifts is not None:
            if extra_shifts is None:
                extra_shifts = []
            end_line = "END:VCALENDAR"
            calendar = Calendar()
            calendar.add("prodid", "-//web schedule//oncall//")
            calendar.add("version", "2.0")
            calendar.add("method", "PUBLISH")
            ical_file = calendar.to_ical().decode()
            ical = ical_file.replace(end_line, "").strip()
            ical = f"{ical}\r\n"
            for event in itertools.chain(qs.all(), extra_shifts):
                ical += event.convert_to_ical(self.time_zone)
            ical += f"{end_line}\r\n"
        return ical

    def _generate_ical_file_primary(self):
        qs = self.custom_shifts.exclude(type=CustomOnCallShift.TYPE_OVERRIDE)
        return self._generate_ical_file_from_shifts(qs)

    def _generate_ical_file_overrides(self):
        qs = self.custom_shifts.filter(type=CustomOnCallShift.TYPE_OVERRIDE)
        return self._generate_ical_file_from_shifts(qs)

    @cached_property
    def _ical_file_primary(self):
        """Return cached ical file with iCal events from custom on-call shifts."""
        if self.cached_ical_file_primary is None:
            self.cached_ical_file_primary = self._generate_ical_file_primary()
            self.save(update_fields=["cached_ical_file_primary"])
        return self.cached_ical_file_primary

    def _refresh_primary_ical_file(self):
        self.prev_ical_file_primary = self.cached_ical_file_primary
        self.cached_ical_file_primary = self._generate_ical_file_primary()
        self.save(update_fields=["cached_ical_file_primary", "prev_ical_file_primary"])

    @cached_property
    def _ical_file_overrides(self):
        """Return cached ical file with iCal events from custom on-call overrides shifts."""
        if self.cached_ical_file_overrides is None:
            self.cached_ical_file_overrides = self._generate_ical_file_overrides()
            self.save(update_fields=["cached_ical_file_overrides"])
        return self.cached_ical_file_overrides

    def _refresh_overrides_ical_file(self):
        self.prev_ical_file_overrides = self.cached_ical_file_overrides
        self.cached_ical_file_overrides = self._generate_ical_file_overrides()
        self.save(update_fields=["cached_ical_file_overrides", "prev_ical_file_overrides"])

    def preview_shift(self, custom_shift, user_tz, starting_date, days, updated_shift_pk=None):
        """Return unsaved rotation and final schedule preview events."""
        if custom_shift.type == CustomOnCallShift.TYPE_OVERRIDE:
            qs = self.custom_shifts.filter(type=CustomOnCallShift.TYPE_OVERRIDE)
            ical_attr = "cached_ical_file_overrides"
            ical_property = "_ical_file_overrides"
        elif custom_shift.type == CustomOnCallShift.TYPE_ROLLING_USERS_EVENT:
            qs = self.custom_shifts.exclude(type=CustomOnCallShift.TYPE_OVERRIDE)
            ical_attr = "cached_ical_file_primary"
            ical_property = "_ical_file_primary"
        else:
            raise ValueError("Invalid shift type")

        def _invalidate_cache(schedule, prop_name):
            """Invalidate cached property cache"""
            try:
                delattr(schedule, prop_name)
            except AttributeError:
                pass

        extra_shifts = [custom_shift]
        if updated_shift_pk is not None:
            try:
                update_shift = qs.get(public_primary_key=updated_shift_pk)
            except CustomOnCallShift.DoesNotExist:
                pass
            else:
                if update_shift.event_is_started:
                    update_shift.until = custom_shift.rotation_start
                    extra_shifts.append(update_shift)
                custom_shift.public_primary_key = updated_shift_pk
                qs = qs.exclude(public_primary_key=updated_shift_pk)

        ical_file = self._generate_ical_file_from_shifts(qs, extra_shifts=extra_shifts)

        original_value = getattr(self, ical_attr)
        _invalidate_cache(self, ical_property)
        setattr(self, ical_attr, ical_file)

        # filter events using a temporal overriden calendar including the not-yet-saved shift
        events = self.filter_events(user_tz, starting_date, days=days, with_empty=True, with_gap=True)
        shift_events = [e for e in events if e["shift"]["pk"] == custom_shift.public_primary_key]
        final_events = self._resolve_schedule(events)

        _invalidate_cache(self, ical_property)
        setattr(self, ical_attr, original_value)

        return shift_events, final_events
