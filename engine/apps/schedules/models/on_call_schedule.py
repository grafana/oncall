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

    def _generate_ical_file_from_shifts(self, qs):
        """Generate iCal events file from custom on-call shifts."""
        ical = None
        if qs.exists():
            end_line = "END:VCALENDAR"
            calendar = Calendar()
            calendar.add("prodid", "-//web schedule//oncall//")
            calendar.add("version", "2.0")
            calendar.add("method", "PUBLISH")
            ical_file = calendar.to_ical().decode()
            ical = ical_file.replace(end_line, "").strip()
            ical = f"{ical}\r\n"
            for event in qs.all():
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
