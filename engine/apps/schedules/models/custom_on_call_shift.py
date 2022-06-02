import logging
from calendar import monthrange
from uuid import uuid4

import pytz
from django.apps import apps
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import JSONField
from django.utils import timezone
from django.utils.functional import cached_property
from icalendar.cal import Event
from recurring_ical_events import UnfoldableCalendar

from apps.schedules.tasks import drop_cached_ical_task
from apps.user_management.models import User
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def generate_public_primary_key_for_custom_oncall_shift():
    prefix = "O"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while CustomOnCallShift.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="CustomOnCallShift"
        )
        failure_counter += 1

    return new_public_primary_key


class CustomOnCallShift(models.Model):
    (
        FREQUENCY_DAILY,
        FREQUENCY_WEEKLY,
        FREQUENCY_MONTHLY,
    ) = range(3)

    FREQUENCY_CHOICES = (
        (FREQUENCY_DAILY, "Daily"),
        (FREQUENCY_WEEKLY, "Weekly"),
        (FREQUENCY_MONTHLY, "Monthly"),
    )

    PUBLIC_FREQUENCY_CHOICES_MAP = {
        FREQUENCY_DAILY: "daily",
        FREQUENCY_WEEKLY: "weekly",
        FREQUENCY_MONTHLY: "monthly",
    }

    (
        TYPE_SINGLE_EVENT,
        TYPE_RECURRENT_EVENT,
        TYPE_ROLLING_USERS_EVENT,
    ) = range(3)

    TYPE_CHOICES = (
        (TYPE_SINGLE_EVENT, "Single event"),
        (TYPE_RECURRENT_EVENT, "Recurrent event"),
        (TYPE_ROLLING_USERS_EVENT, "Rolling users"),
    )

    PUBLIC_TYPE_CHOICES_MAP = {
        TYPE_SINGLE_EVENT: "single_event",
        TYPE_RECURRENT_EVENT: "recurrent_event",
        TYPE_ROLLING_USERS_EVENT: "rolling_users",
    }

    (MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY) = range(7)

    WEEKDAY_CHOICES = (
        (MONDAY, "Monday"),
        (TUESDAY, "Tuesday"),
        (WEDNESDAY, "Wednesday"),
        (THURSDAY, "Thursday"),
        (FRIDAY, "Friday"),
        (SATURDAY, "Saturday"),
        (SUNDAY, "Sunday"),
    )

    ICAL_WEEKDAY_MAP = {
        MONDAY: "MO",
        TUESDAY: "TU",
        WEDNESDAY: "WE",
        THURSDAY: "TH",
        FRIDAY: "FR",
        SATURDAY: "SA",
        SUNDAY: "SU",
    }
    (
        SOURCE_WEB,
        SOURCE_API,
        SOURCE_SLACK,
        SOURCE_TERRAFORM,
    ) = range(4)

    SOURCE_CHOICES = (
        (SOURCE_WEB, "web"),
        (SOURCE_API, "api"),
        (SOURCE_SLACK, "slack"),
        (SOURCE_TERRAFORM, "terraform"),
    )
    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_custom_oncall_shift,
    )

    organization = models.ForeignKey(
        "user_management.Organization",
        on_delete=models.CASCADE,
        related_name="custom_on_call_shifts",
    )
    team = models.ForeignKey(
        "user_management.Team",
        on_delete=models.SET_NULL,
        related_name="custom_on_call_shifts",
        null=True,
        default=None,
    )
    name = models.CharField(max_length=200)
    time_zone = models.CharField(max_length=100, null=True, default=None)
    source = models.IntegerField(choices=SOURCE_CHOICES, default=SOURCE_API)
    users = models.ManyToManyField("user_management.User")  # users in single and recurrent events
    rolling_users = JSONField(null=True, default=None)  # [{user.pk: user.public_primary_key, ...},...]
    start_rotation_from_user_index = models.PositiveIntegerField(null=True, default=None)

    uuid = models.UUIDField(default=uuid4)  # event uuid
    type = models.IntegerField(choices=TYPE_CHOICES)  # "rolling_users", "recurrent_event", "single_event"

    start = models.DateTimeField()  # event start datetime
    duration = models.DurationField()  # duration in seconds

    frequency = models.IntegerField(choices=FREQUENCY_CHOICES, null=True, default=None)

    priority_level = models.IntegerField(default=0)

    interval = models.IntegerField(default=None, null=True)  # every n days/months - ical format

    # week_start in ical format
    week_start = models.IntegerField(choices=WEEKDAY_CHOICES, default=SUNDAY)  # for weekly events

    by_day = JSONField(
        default=None, null=True
    )  # [] BYDAY - (MO, TU); (1MO, -2TU) - for monthly and weekly freq - ical format
    by_month = JSONField(default=None, null=True)  # [] BYMONTH - what months (1, 2, 3, ...) - ical format
    by_monthday = JSONField(default=None, null=True)  # [] BYMONTHDAY - what days of month (1, 2, -3) - ical format

    class Meta:
        unique_together = ("name", "organization")

    def delete(self, *args, **kwargs):
        for schedule in self.schedules.all():
            drop_cached_ical_task.apply_async((schedule.pk,))
        super().delete(*args, **kwargs)

    @property
    def repr_settings_for_client_side_logging(self) -> str:
        """
        Example of execution:
            name: Demo recurrent event, team: example, source: terraform, type: Recurrent event, users: Alex,
            start: 2020-09-10T16:00:00+00:00, duration: 3:00:00, priority level: 0, frequency: Weekly, interval: 2,
            week start: 6, by day: ['MO', 'WE', 'FR'], by month: None, by monthday: None
        """
        if self.type == CustomOnCallShift.TYPE_ROLLING_USERS_EVENT:
            users_verbal = "empty"
            if self.rolling_users is not None:
                users_verbal = ""
                for users_dict in self.rolling_users:
                    users = self.organization.users.filter(public_primary_key__in=users_dict.values())
                    users_verbal += f"[{', '.join([user.username for user in users])}]"
            users_verbal = f"rolling users: {users_verbal}"
        else:
            users = self.users.all()
            users_verbal = f"{', '.join([user.username for user in users]) if users else 'empty'}"
        result = (
            f"name: {self.name}, team: {self.team.name if self.team else 'No team'},"
            f"{f' time_zone: {self.time_zone},' if self.time_zone else ''} "
            f"source: {self.get_source_display()}, type: {self.get_type_display()}, users: {users_verbal}, "
            f"start: {self.start.isoformat()}, duration: {self.duration}, priority level: {self.priority_level}"
        )
        if self.type != CustomOnCallShift.TYPE_SINGLE_EVENT:
            result += (
                f", frequency: {self.get_frequency_display()}, interval: {self.interval}, "
                f"week start: {self.week_start}, by day: {self.by_day}, by month: {self.by_month}, "
                f"by monthday: {self.by_monthday}"
            )
        return result

    def convert_to_ical(self, time_zone="UTC"):
        result = ""
        # use shift time_zone if it exists, otherwise use schedule or default time_zone
        time_zone = self.time_zone if self.time_zone is not None else time_zone
        # rolling_users shift converts to several ical events
        if self.type == CustomOnCallShift.TYPE_ROLLING_USERS_EVENT:
            event_ical = None
            users_queue = self.get_rolling_users()
            for counter, users in enumerate(users_queue, start=1):
                start = self.get_next_start_date(event_ical)
                for user_counter, user in enumerate(users, start=1):
                    event_ical = self.generate_ical(user, start, user_counter, counter, time_zone)
                    result += event_ical
        else:
            for user_counter, user in enumerate(self.users.all(), start=1):
                result += self.generate_ical(user, self.start, user_counter, time_zone=time_zone)
        return result

    def generate_ical(self, user, start, user_counter, counter=1, time_zone="UTC"):
        # create event for each user in a list because we can't parse multiple users from ical summary
        event = Event()
        event["uid"] = f"amixr-{self.uuid}-U{user_counter}-E{counter}-S{self.source}"
        event.add("summary", self.get_summary_with_user_for_ical(user))
        event.add("dtstart", self.convert_dt_to_schedule_timezone(start, time_zone))
        event.add("dtend", self.convert_dt_to_schedule_timezone(start + self.duration, time_zone))
        event.add("dtstamp", timezone.now())
        if self.event_ical_rules:
            event.add("rrule", self.event_ical_rules)
        try:
            event_in_ical = event.to_ical().decode("utf-8")
        except ValueError as e:
            logger.warning(f"Cannot convert event with pk {self.pk} to ical: {str(e)}")
            event_in_ical = ""
        return event_in_ical

    def get_summary_with_user_for_ical(self, user: User) -> str:
        summary = ""
        if self.priority_level > 0:
            summary += f"[L{self.priority_level}] "
        summary += f"{user.username} "
        return summary

    def get_next_start_date(self, event_ical):
        """Get date of the next event (for rolling_users shifts)"""
        if event_ical is None:
            return self.start
        current_event = Event.from_ical(event_ical)
        # take shift interval, not event interval. For rolling_users shift it is not the same.
        current_event["rrule"]["INTERVAL"] = self.interval or 1
        current_event_start = current_event["DTSTART"].dt
        next_event_start = current_event_start
        ONE_DAY = 1

        if self.frequency == CustomOnCallShift.FREQUENCY_DAILY:
            # test daily with byday
            next_event_start = current_event_start + timezone.timedelta(days=ONE_DAY)
        elif self.frequency == CustomOnCallShift.FREQUENCY_WEEKLY:
            DAYS_IN_A_WEEK = 7
            days_for_next_event = DAYS_IN_A_WEEK - current_event_start.weekday() + self.week_start
            if days_for_next_event > DAYS_IN_A_WEEK:
                days_for_next_event = days_for_next_event % DAYS_IN_A_WEEK
            next_event_start = current_event_start + timezone.timedelta(days=days_for_next_event)
        elif self.frequency == CustomOnCallShift.FREQUENCY_MONTHLY:
            DAYS_IN_A_MONTH = monthrange(self.start.year, self.start.month)[1]
            # count days before the next month starts
            days_for_next_event = DAYS_IN_A_MONTH - current_event_start.day + ONE_DAY
            if days_for_next_event > DAYS_IN_A_MONTH:
                days_for_next_event = days_for_next_event % DAYS_IN_A_MONTH
            next_event_start = current_event_start + timezone.timedelta(days=days_for_next_event)
        next_event = None
        # repetitions generate the next event shift according with the recurrence rules
        repetitions = UnfoldableCalendar(current_event).RepeatedEvent(
            current_event, next_event_start.replace(microsecond=0)
        )
        ical_iter = repetitions.__iter__()
        for event in ical_iter:
            if event.start.date() >= next_event_start.date():
                next_event = event
                break
        next_event_dt = next_event.start
        return next_event_dt

    @cached_property
    def event_ical_rules(self):
        # e.g. {'freq': ['WEEKLY'], 'interval': [2], 'byday': ['MO', 'WE', 'FR'], 'wkst': ['SU']}
        rules = {}
        if self.frequency is not None:
            rules["freq"] = [self.get_frequency_display().upper()]
            if self.event_interval is not None:
                rules["interval"] = [self.event_interval]
            if self.by_day is not None:
                rules["byday"] = self.by_day
            if self.by_month is not None:
                rules["bymonth"] = self.by_month
            if self.by_monthday is not None:
                rules["bymonthday"] = self.by_monthday
            if self.week_start is not None:
                rules["wkst"] = CustomOnCallShift.ICAL_WEEKDAY_MAP[self.week_start]
        return rules

    @cached_property
    def event_interval(self):
        if self.type == CustomOnCallShift.TYPE_ROLLING_USERS_EVENT:
            if self.rolling_users:
                if self.interval is not None:
                    return self.interval * len(self.rolling_users)
                else:
                    return len(self.rolling_users)
        return self.interval

    def convert_dt_to_schedule_timezone(self, dt, time_zone):
        start_naive = dt.replace(tzinfo=None)
        return pytz.timezone(time_zone).localize(start_naive, is_dst=None)

    def get_rolling_users(self):
        User = apps.get_model("user_management", "User")
        all_users_pks = set()
        users_queue = []
        if self.rolling_users is not None:
            # get all users pks from rolling_users field
            for users_dict in self.rolling_users:
                all_users_pks.update(users_dict.keys())
            users = User.objects.filter(pk__in=all_users_pks)
            # generate users_queue list with user objects
            if self.start_rotation_from_user_index is not None:
                rolling_users = (
                    self.rolling_users[self.start_rotation_from_user_index :]
                    + self.rolling_users[: self.start_rotation_from_user_index]
                )
            else:
                rolling_users = self.rolling_users
            for users_dict in rolling_users:
                users_list = list(users.filter(pk__in=users_dict.keys()))
                users_queue.append(users_list)
        return users_queue

    def add_rolling_users(self, rolling_users_list):
        result = []
        for users in rolling_users_list:
            result.append({user.pk: user.public_primary_key for user in users})
        self.rolling_users = result
        self.save(update_fields=["rolling_users"])
