import copy
import datetime
import itertools
import logging
import typing
from calendar import monthrange
from uuid import uuid4

import pytz
from dateutil import relativedelta
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models, transaction
from django.db.models import JSONField
from django.forms.models import model_to_dict
from django.utils import timezone
from django.utils.functional import cached_property
from icalendar.cal import Event
from recurring_ical_events import UnfoldableCalendar

from apps.schedules.tasks import (
    drop_cached_ical_task,
    refresh_ical_final_schedule,
    schedule_notify_about_empty_shifts_in_schedule,
    schedule_notify_about_gaps_in_schedule,
)
from apps.user_management.models import User
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.schedules.models import OnCallSchedule


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
    parent_shift: typing.Optional["CustomOnCallShift"]
    schedules: "RelatedManager['OnCallSchedule']"

    (
        FREQUENCY_DAILY,
        FREQUENCY_WEEKLY,
        FREQUENCY_MONTHLY,
        FREQUENCY_HOURLY,
    ) = range(4)

    FREQUENCY_CHOICES = (
        (FREQUENCY_HOURLY, "Hourly"),
        (FREQUENCY_DAILY, "Daily"),
        (FREQUENCY_WEEKLY, "Weekly"),
        (FREQUENCY_MONTHLY, "Monthly"),
    )

    PUBLIC_FREQUENCY_CHOICES_MAP = {
        FREQUENCY_HOURLY: "hourly",
        FREQUENCY_DAILY: "daily",
        FREQUENCY_WEEKLY: "weekly",
        FREQUENCY_MONTHLY: "monthly",
    }

    WEB_FREQUENCY_CHOICES_MAP = {
        FREQUENCY_HOURLY: "hours",
        FREQUENCY_DAILY: "days",
        FREQUENCY_WEEKLY: "weeks",
        FREQUENCY_MONTHLY: "months",
    }

    (
        TYPE_SINGLE_EVENT,
        TYPE_RECURRENT_EVENT,
        TYPE_ROLLING_USERS_EVENT,
        TYPE_OVERRIDE,
    ) = range(4)

    TYPE_CHOICES = (
        (TYPE_SINGLE_EVENT, "Single event"),
        (TYPE_RECURRENT_EVENT, "Recurrent event"),
        (TYPE_ROLLING_USERS_EVENT, "Rolling users"),
        (TYPE_OVERRIDE, "Override"),
    )

    PUBLIC_TYPE_CHOICES_MAP = {
        TYPE_SINGLE_EVENT: "single_event",
        TYPE_RECURRENT_EVENT: "recurrent_event",
        TYPE_ROLLING_USERS_EVENT: "rolling_users",
        TYPE_OVERRIDE: "override",
    }

    WEB_TYPES = (
        TYPE_ROLLING_USERS_EVENT,
        TYPE_OVERRIDE,
    )

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
    ICAL_WEEKDAY_REVERSE_MAP = {v: k for k, v in ICAL_WEEKDAY_MAP.items()}

    WEB_WEEKDAY_MAP = {
        "MO": "Monday",
        "TU": "Tuesday",
        "WE": "Wednesday",
        "TH": "Thursday",
        "FR": "Friday",
        "SA": "Saturday",
        "SU": "Sunday",
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
    schedule = models.ForeignKey(
        "schedules.OnCallSchedule",
        on_delete=models.CASCADE,
        related_name="custom_shifts",
        null=True,
        default=None,
    )
    name = models.CharField(max_length=200, null=True, default=None)
    time_zone = models.CharField(max_length=100, null=True, default=None)
    source = models.IntegerField(choices=SOURCE_CHOICES, default=SOURCE_API)
    users = models.ManyToManyField("user_management.User")  # users in single and recurrent events
    rolling_users = JSONField(null=True, default=None)  # [{user.pk: user.public_primary_key, ...},...]
    start_rotation_from_user_index = models.PositiveIntegerField(null=True, default=None)

    uuid = models.UUIDField(default=uuid4)  # event uuid
    type = models.IntegerField(choices=TYPE_CHOICES)  # "rolling_users", "recurrent_event", "single_event", "override"

    start = models.DateTimeField()  # event start datetime
    duration = models.DurationField()  # duration in seconds

    rotation_start = models.DateTimeField()  # used for calculation users rotation and rotation start date

    frequency = models.IntegerField(choices=FREQUENCY_CHOICES, null=True, default=None)

    priority_level = models.IntegerField(default=0)

    interval = models.IntegerField(default=None, null=True)  # every n days/months - ical format

    until = models.DateTimeField(default=None, null=True)  # if set, when recurrence ends

    # week_start in ical format
    week_start = models.IntegerField(choices=WEEKDAY_CHOICES, default=SUNDAY)  # for weekly events

    by_day = JSONField(
        default=None, null=True
    )  # [] BYDAY - (MO, TU); (1MO, -2TU) - for monthly and weekly freq - ical format
    by_month = JSONField(default=None, null=True)  # [] BYMONTH - what months (1, 2, 3, ...) - ical format
    by_monthday = JSONField(default=None, null=True)  # [] BYMONTHDAY - what days of month (1, 2, -3) - ical format

    updated_shift = models.OneToOneField(
        "schedules.CustomOnCallShift",
        on_delete=models.SET_NULL,
        default=None,
        null=True,
        related_name="parent_shift",
    )

    def delete(self, *args, **kwargs):
        schedules_to_update = list(self.schedules.all())
        if self.schedule:
            schedules_to_update.append(self.schedule)

        force = kwargs.pop("force", False)
        # do soft delete for started shifts that were created for web schedule
        if self.schedule and self.event_is_started and not force:
            updated_until = timezone.now().replace(microsecond=0)
            if self.until is not None and updated_until >= self.until:
                # event is already finished
                return
            self.until = updated_until
            update_fields = ["until"]
            if self.type == self.TYPE_OVERRIDE:
                # since it is a single-time event, update override duration
                delta = self.until - self.start
                if delta < self.duration:
                    self.duration = delta
                    update_fields += ["duration"]
            self.save(update_fields=update_fields)
        elif self.schedule:
            # for web schedule shifts to be hard-deleted, update the rotation updated_shift links
            previous_shift = self.schedule.custom_shifts.filter(updated_shift=self).first()
            super().delete(*args, **kwargs)
            if previous_shift:
                previous_shift.updated_shift = self.updated_shift
                previous_shift.save(update_fields=["updated_shift"])
        else:
            super().delete(*args, **kwargs)

        for schedule in schedules_to_update:
            self.start_drop_ical_and_check_schedule_tasks(schedule)

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
        if self.type not in (CustomOnCallShift.TYPE_SINGLE_EVENT, CustomOnCallShift.TYPE_OVERRIDE):
            result += (
                f", frequency: {self.get_frequency_display()}, interval: {self.interval}, "
                f"week start: {self.week_start}, by day: {self.by_day}, by month: {self.by_month}, "
                f"by monthday: {self.by_monthday}, rotation start: {self.rotation_start.isoformat()}, "
                f"until: {self.until.isoformat() if self.until else None}"
            )
        return result

    @property
    def event_is_started(self):
        return bool(self.rotation_start <= timezone.now())

    @property
    def event_is_finished(self):
        if self.frequency is not None:
            is_finished = bool(self.until <= timezone.now()) if self.until else False
        else:
            is_finished = bool(self.start + self.duration <= timezone.now())

        return is_finished

    def _daily_by_day_to_ical(self, time_zone, start, users_queue):
        """Create ical weekly shifts to distribute user groups combining daily + by_day.

        e.g.
            by_day: [WED, FRI]
            users_queue: [user_group_1, user_group_2, user_group_3]
        will result in the following ical shift rules:
            user_group_1, weekly WED interval 3
            user_group_2, weekly FRI interval 3
            user_group_3, weekly WED interval 3
            user_group_1, weekly FRI interval 3
            user_group_2, weekly WED interval 3
            user_group_3, weekly FRI interval 3
        """
        result = ""
        # keep tracking of (users, day) combinations, and starting dates for each
        combinations = []
        starting_dates = []
        # we may need to iterate several times over users until we get a seen combination
        # use the group index as reference since user groups could repeat in the queue
        cycle_user_groups = itertools.cycle(range(len(users_queue)))
        orig_start = last_start = start
        all_rotations_checked = False
        # we need to go through each individual day
        day_by_day_rrule = copy.deepcopy(self.event_ical_rules)
        day_by_day_rrule["interval"] = 1
        for user_group_id in cycle_user_groups:
            for i in range(self.interval):
                if not start:  # means that rotation ends before next event starts
                    all_rotations_checked = True
                    break
                last_start = start
                day = CustomOnCallShift.ICAL_WEEKDAY_MAP[start.weekday()]
                # double-check day is valid (when until is set, we may get unexpected days)
                if day in self.by_day:
                    if (user_group_id, day, i) in combinations:
                        all_rotations_checked = True
                        break

                    starting_dates.append(start)
                    combinations.append((user_group_id, day, i))
                # get next event date following the original rule
                event_ical = self.generate_ical(start, 1, None, 1, time_zone, custom_rrule=day_by_day_rrule)
                start = self.get_rotation_date(event_ical, get_next_date=True, interval=1)
            if all_rotations_checked:
                break

        week_interval = 1
        if orig_start and last_start:
            # number of weeks used to cover all combinations
            week_interval = ((last_start - orig_start).days // 7) or 1
        counter = 1
        for (user_group_id, day, _), start in zip(combinations, starting_dates):
            users = users_queue[user_group_id]
            for user_counter, user in enumerate(users, start=1):
                # setup weekly events, for each user group/day combinations,
                # setting the right interval and the corresponding day
                custom_rrule = copy.deepcopy(self.event_ical_rules)
                custom_rrule["freq"] = ["WEEKLY"]
                custom_rrule["interval"] = [week_interval]
                custom_rrule["byday"] = [day]
                custom_event_ical = self.generate_ical(
                    start, user_counter, user, counter, time_zone, custom_rrule=custom_rrule
                )
                result += custom_event_ical
            counter += 1
        return result

    def convert_to_ical(self, time_zone="UTC", allow_empty_users=False):
        result = ""
        # use shift time_zone if it exists, otherwise use schedule or default time_zone
        time_zone = self.time_zone if self.time_zone is not None else time_zone
        # rolling_users shift converts to several ical events
        if self.type in (CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, CustomOnCallShift.TYPE_OVERRIDE):
            # generate initial iCal for counting rotation start date
            event_ical = self.generate_ical(self.start)
            rotations_created = 0
            all_rotation_checked = False

            users_queue = self.get_rolling_users()
            if not users_queue and not allow_empty_users:
                return result
            if not users_queue and allow_empty_users:
                users_queue = [[None]]
            if self.frequency is None:
                users_queue = users_queue[:1]

            # Get the date of the current rotation
            if self.start == self.rotation_start or self.frequency is None:
                start = self.start
            else:
                start = self.get_rotation_date(event_ical)

            # Make sure we respect the selected days if any when defining start date
            if self.frequency is not None and self.by_day and start is not None:
                start_day = CustomOnCallShift.ICAL_WEEKDAY_MAP[start.weekday()]
                if start_day not in self.by_day:
                    # when calculating first start date, make sure to sort days using week_start
                    sorted_days = [i % 7 for i in range(self.week_start, self.week_start + 7)]
                    selected_days = [CustomOnCallShift.ICAL_WEEKDAY_REVERSE_MAP[d] for d in self.by_day]
                    expected_start_day = [d for d in sorted_days if d in selected_days][0]
                    delta = (expected_start_day - start.weekday()) % 7
                    start = start + datetime.timedelta(days=delta)

            if self.frequency == CustomOnCallShift.FREQUENCY_DAILY and self.by_day:
                result = self._daily_by_day_to_ical(time_zone, start, users_queue)
                all_rotation_checked = True

            while not all_rotation_checked:
                for counter, users in enumerate(users_queue, start=1):
                    if not start:  # means that rotation ends before next event starts
                        all_rotation_checked = True
                        break
                    elif (
                        self.source == CustomOnCallShift.SOURCE_WEB and start + self.duration > self.rotation_start
                    ) or start >= self.rotation_start:
                        # event has already started, generate iCal for each user
                        for user_counter, user in enumerate(users, start=1):
                            event_ical = self.generate_ical(start, user_counter, user, counter, time_zone)
                            result += event_ical
                        rotations_created += 1
                    else:  # generate default iCal to calculate the date for the next rotation
                        event_ical = self.generate_ical(start)

                    if rotations_created == len(users_queue):  # means that we generated iCal for every user group
                        all_rotation_checked = True
                        break
                    # Use the flag 'get_next_date' to get the date of the next rotation
                    start = self.get_rotation_date(event_ical, get_next_date=True)
        else:
            for user_counter, user in enumerate(self.users.all(), start=1):
                result += self.generate_ical(self.start, user_counter, user, time_zone=time_zone)
        return result

    def generate_ical(self, start, user_counter=0, user=None, counter=1, time_zone="UTC", custom_rrule=None):
        event = Event()
        event["uid"] = f"oncall-{self.uuid}-PK{self.public_primary_key}-U{user_counter}-E{counter}-S{self.source}"
        if user:
            event.add("summary", self.get_summary_with_user_for_ical(user))
        event.add("dtstart", self.convert_dt_to_schedule_timezone(start, time_zone))
        dtend = start + self.duration
        if self.until:
            dtend = min(dtend, self.until)
        event.add("dtend", self.convert_dt_to_schedule_timezone(dtend, time_zone))
        event.add("dtstamp", self.rotation_start)
        if custom_rrule:
            event.add("rrule", custom_rrule)
        elif self.event_ical_rules:
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

    def get_rotation_date(self, event_ical, get_next_date=False, interval=None):
        """Get date of the next event (for rolling_users shifts)"""
        ONE_DAY = 1
        ONE_HOUR = 1

        def add_months(year, month, months_add):
            """
            Utility method for month calculation. E.g. (2022, 12) + 1 month = (2023, 1)
            """
            dt = datetime.datetime.min.replace(year=year, month=month) + relativedelta.relativedelta(months=months_add)
            return dt.year, dt.month

        current_event = Event.from_ical(event_ical)
        # take shift interval, not event interval. For rolling_users shift it is not the same.
        if interval is None:
            interval = self.interval or 1
        if "rrule" in current_event:
            # when triggering shift previews, there could be no rrule information yet
            # (e.g. initial empty weekly rotation has no rrule set)
            current_event["rrule"]["INTERVAL"] = interval
        current_event_start = current_event["DTSTART"].dt
        next_event_start = current_event_start
        # Calculate the minimum start date for the next event based on rotation frequency. We don't need to do this
        # for the first rotation, because in this case the min start date will be the same as the current event date.
        if get_next_date:
            if self.frequency == CustomOnCallShift.FREQUENCY_HOURLY:
                next_event_start = current_event_start + datetime.timedelta(hours=ONE_HOUR)
            elif self.frequency == CustomOnCallShift.FREQUENCY_DAILY:
                next_event_start = current_event_start + datetime.timedelta(days=ONE_DAY)
            elif self.frequency == CustomOnCallShift.FREQUENCY_WEEKLY:
                DAYS_IN_A_WEEK = 7
                # count days before the next week starts
                days_for_next_event = DAYS_IN_A_WEEK - current_event_start.weekday() + self.week_start
                if days_for_next_event > DAYS_IN_A_WEEK:
                    days_for_next_event = days_for_next_event % DAYS_IN_A_WEEK
                # count next event start date with respect to event interval
                next_event_start = current_event_start + datetime.timedelta(
                    days=days_for_next_event + DAYS_IN_A_WEEK * (interval - 1)
                )
            elif self.frequency == CustomOnCallShift.FREQUENCY_MONTHLY:
                DAYS_IN_A_MONTH = monthrange(current_event_start.year, current_event_start.month)[1]
                # count days before the next month starts
                days_for_next_event = DAYS_IN_A_MONTH - current_event_start.day + ONE_DAY
                # count next event start date with respect to event interval
                for i in range(1, interval):
                    year, month = add_months(current_event_start.year, current_event_start.month, i)
                    next_month_days = monthrange(year, month)[1]
                    days_for_next_event += next_month_days
                next_event_start = current_event_start + datetime.timedelta(days=days_for_next_event)

        end_date = None
        # get the period for calculating the current rotation end date for long events with frequency weekly and monthly
        if self.frequency == CustomOnCallShift.FREQUENCY_WEEKLY:
            DAYS_IN_A_WEEK = 7
            days_diff = 0
            # get the last day of the week with respect to the week_start
            if next_event_start.weekday() != self.week_start:
                days_diff = DAYS_IN_A_WEEK + next_event_start.weekday() - self.week_start
                days_diff %= DAYS_IN_A_WEEK
            end_date = next_event_start + datetime.timedelta(days=DAYS_IN_A_WEEK - days_diff - ONE_DAY)
        elif self.frequency == CustomOnCallShift.FREQUENCY_MONTHLY:
            # get the last day of the month
            current_day_number = next_event_start.day
            number_of_days = monthrange(next_event_start.year, next_event_start.month)[1]
            days_diff = number_of_days - current_day_number
            end_date = next_event_start + datetime.timedelta(days=days_diff)

        next_event = None
        # repetitions generate the next event shift according with the recurrence rules
        repetitions = UnfoldableCalendar(current_event).RepeatedEvent(
            current_event, next_event_start.replace(microsecond=0)
        )
        for event in repetitions.__iter__():
            if end_date:  # end_date exists for long events with frequency weekly and monthly
                if end_date >= event.start >= next_event_start:
                    if (
                        self.source == CustomOnCallShift.SOURCE_WEB and event.stop > self.rotation_start
                    ) or event.start >= self.rotation_start:
                        next_event = event
                        break
                elif end_date < event.start:
                    break
            else:
                if event.start >= next_event_start:
                    next_event = event
                    break

        next_event_dt = next_event.start if next_event is not None else next_event_start

        if self.until and next_event_dt > self.until:
            return
        return next_event_dt

    def get_last_event_date(self, date):
        """Get start date of the last event before the chosen date"""
        assert date >= self.start, "Chosen date should be later or equal to initial event start date"

        event_ical = self.generate_ical(self.start)
        initial_event = Event.from_ical(event_ical)
        # take shift interval, not event interval. For rolling_users shift it is not the same.
        interval = self.interval or 1
        if "rrule" in initial_event:
            # means that shift has frequency
            initial_event["rrule"]["INTERVAL"] = interval
        initial_event_start = initial_event["DTSTART"].dt

        last_event = None
        # repetitions generate the next event shift according with the recurrence rules
        repetitions = UnfoldableCalendar(initial_event).RepeatedEvent(
            initial_event, initial_event_start.replace(microsecond=0)
        )
        for event in repetitions.__iter__():
            if event.start > date:
                break
            last_event = event

        last_event_dt = last_event.start if last_event else initial_event_start

        return last_event_dt

    @cached_property
    def event_ical_rules(self):
        # e.g. {'freq': ['WEEKLY'], 'interval': [2], 'byday': ['MO', 'WE', 'FR'], 'wkst': ['SU']}
        rules = {}
        if self.frequency is not None:
            rules["freq"] = [self.get_frequency_display().upper()]
            if self.event_interval is not None:
                rules["interval"] = [self.event_interval]
            if self.by_day:
                rules["byday"] = self.by_day
            if self.by_month is not None:
                rules["bymonth"] = self.by_month
            if self.by_monthday is not None:
                rules["bymonthday"] = self.by_monthday
            if self.week_start is not None:
                rules["wkst"] = CustomOnCallShift.ICAL_WEEKDAY_MAP[self.week_start]
            if self.until is not None:
                # RRULE UNTIL values must be specified in UTC when DTSTART is timezone-aware
                rules["until"] = self.convert_dt_to_schedule_timezone(self.until, "UTC")
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
        if time_zone and time_zone.lower() == "etc/utc":
            # dateutil rrule breaks if Etc/UTC is given
            time_zone = "UTC"
        return pytz.timezone(time_zone).localize(start_naive, is_dst=None)

    def get_rolling_users(self):
        from apps.user_management.models import User

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
                if users_list:
                    users_queue.append(users_list)
        return users_queue

    def add_rolling_users(self, rolling_users_list):
        result = []
        for users in rolling_users_list:
            result.append({user.pk: user.public_primary_key for user in users})
        self.rolling_users = result
        self.save(update_fields=["rolling_users"])

    def get_rotation_user_index(self, date):
        START_ROTATION_INDEX = 0

        result = START_ROTATION_INDEX

        if not self.rolling_users or self.frequency is None:
            return START_ROTATION_INDEX

        # generate initial iCal for counting rotation start date
        event_ical = self.generate_ical(self.start, user_counter=0)

        # Get the date of the current rotation
        if self.start == self.rotation_start:
            start = self.start
        else:
            start = self.get_rotation_date(event_ical)

        if not start or start >= date:
            return START_ROTATION_INDEX

        # count how many times the rotation was triggered before the selected date
        while start or start < date:
            start = self.get_rotation_date(event_ical, get_next_date=True)
            if not start or start >= date:
                break
            event_ical = self.generate_ical(start, user_counter=0)
            result += 1

        result %= len(self.rolling_users)
        return result

    def refresh_schedule(self):
        if not self.schedule:
            # only trigger sync-refresh for web-created shifts
            return
        schedule = self.schedule.get_real_instance()
        schedule.refresh_ical_file()
        refresh_ical_final_schedule.apply_async((schedule.pk,))

    def start_drop_ical_and_check_schedule_tasks(self, schedule):
        drop_cached_ical_task.apply_async((schedule.pk,))
        schedule_notify_about_empty_shifts_in_schedule.apply_async((schedule.pk,))
        schedule_notify_about_gaps_in_schedule.apply_async((schedule.pk,))

    @cached_property
    def last_updated_shift(self):
        last_shift = self.updated_shift
        if last_shift is not None:
            while last_shift.updated_shift is not None:
                last_shift = last_shift.updated_shift
        return last_shift

    def create_or_update_last_shift(self, data):
        now = timezone.now().replace(microsecond=0)
        # rotation start date cannot be earlier than now
        data["rotation_start"] = max(data["rotation_start"], now)
        # prepare dict with params of existing instance with last updates and remove unique and m2m fields from it
        shift_to_update = self.last_updated_shift or self
        instance_data = model_to_dict(shift_to_update)
        fields_to_remove = ["id", "public_primary_key", "uuid", "users", "updated_shift"]
        for field in fields_to_remove:
            instance_data.pop(field)

        instance_data.update(data)
        instance_data["schedule"] = self.schedule
        instance_data["team"] = self.team
        # set new event start date to keep rotation index
        if instance_data["start"] == self.start:
            instance_data["start"] = self.get_last_event_date(now)
        # calculate rotation index to keep user rotation order
        start_rotation_from_user_index = self.get_rotation_user_index(now) + (self.start_rotation_from_user_index or 0)
        if start_rotation_from_user_index >= len(instance_data["rolling_users"]):
            start_rotation_from_user_index = 0
        instance_data["start_rotation_from_user_index"] = start_rotation_from_user_index

        if self.last_updated_shift is None or self.last_updated_shift.event_is_started:
            # create new shift
            with transaction.atomic():
                shift = CustomOnCallShift(**instance_data)
                shift.save()
                shift_to_update.until = data["rotation_start"]
                shift_to_update.updated_shift = shift
                shift_to_update.save(update_fields=["until", "updated_shift"])
        else:
            shift = self.last_updated_shift
            for key in instance_data:
                setattr(shift, key, instance_data[key])
            shift.save(update_fields=list(instance_data))

        return shift

    # Insight logs
    @property
    def insight_logs_type_verbal(self):
        return "oncall_shift"

    @property
    def insight_logs_verbal(self):
        return self.name

    @property
    def insight_logs_serialized(self):
        users_verbal = []
        if self.type == CustomOnCallShift.TYPE_ROLLING_USERS_EVENT:
            if self.rolling_users is not None:
                for users_dict in self.rolling_users:
                    users = self.organization.users.filter(public_primary_key__in=users_dict.values())
                    users_verbal.extend([user.username for user in users])
        else:
            users = self.users.all()
            users_verbal = [user.username for user in users]
        result = {
            "name": self.name,
            "source": self.get_source_display(),
            "type": self.get_type_display(),
            "users": users_verbal,
            "start": self.start.isoformat(),
            "duration": self.duration.seconds,
            "priority_level": self.priority_level,
        }
        if self.type not in (CustomOnCallShift.TYPE_SINGLE_EVENT, CustomOnCallShift.TYPE_OVERRIDE):
            result["frequency"] = self.get_frequency_display()
            result["interval"] = self.interval
            result["week_start"] = self.week_start
            result["by_day"] = self.by_day
            result["by_month"] = self.by_month
            result["by_monthday"] = self.by_monthday
            result["rotation_start"] = self.rotation_start.isoformat()
            if self.until:
                result["until"] = self.until.isoformat()
        if self.team:
            result["team"] = self.team.name
            result["team_id"] = self.team.public_primary_key
        else:
            result["team"] = "General"
        if self.time_zone:
            result["time_zone"] = self.time_zone
        return result

    @property
    def insight_logs_metadata(self):
        result = {}
        if self.team:
            result["team"] = self.team.name
            result["team_id"] = self.team.public_primary_key
        else:
            result["team"] = "General"
        if self.schedule:
            result["schedule"] = self.schedule.insight_logs_verbal
            result["schedule_id"] = self.schedule.public_primary_key

        return result
