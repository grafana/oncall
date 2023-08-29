import copy
import datetime
import itertools
import re
import typing
from collections import defaultdict
from enum import Enum

import icalendar
import pytz
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q
from django.db.utils import DatabaseError
from django.utils import timezone
from django.utils.functional import cached_property
from polymorphic.managers import PolymorphicManager
from polymorphic.models import PolymorphicModel
from polymorphic.query import PolymorphicQuerySet

from apps.schedules.constants import (
    EXPORT_WINDOW_DAYS_AFTER,
    EXPORT_WINDOW_DAYS_BEFORE,
    ICAL_COMPONENT_VEVENT,
    ICAL_DATETIME_END,
    ICAL_DATETIME_STAMP,
    ICAL_DATETIME_START,
    ICAL_LAST_MODIFIED,
    ICAL_PRIORITY,
    ICAL_STATUS,
    ICAL_STATUS_CANCELLED,
    ICAL_SUMMARY,
    ICAL_UID,
)
from apps.schedules.ical_utils import (
    create_base_icalendar,
    fetch_ical_file_or_get_error,
    get_oncall_users_for_multiple_schedules,
    list_of_empty_shifts_in_schedule,
    list_of_oncall_shifts_from_ical,
)
from apps.schedules.models import CustomOnCallShift
from apps.user_management.models import User
from common.database import NON_POLYMORPHIC_CASCADE, NON_POLYMORPHIC_SET_NULL
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import EscalationPolicy
    from apps.auth_token.models import ScheduleExportAuthToken
    from apps.schedules.models import ShiftSwapRequest
    from apps.slack.models import SlackUserGroup
    from apps.user_management.models import Organization, Team


RE_ICAL_SEARCH_USERNAME = r"SUMMARY:(\[L[0-9]+\] )?{}"
RE_ICAL_FETCH_USERNAME = re.compile(r"SUMMARY:(?:\[L[0-9]+\] )?([^\s]+)")


# Utility classes for schedule quality report
class QualityReportCommentType(str, Enum):
    INFO = "info"
    WARNING = "warning"


class QualityReportComment(typing.TypedDict):
    type: QualityReportCommentType
    text: str


class QualityReportOverloadedUser(typing.TypedDict):
    id: str
    username: str
    score: int


QualityReportOverloadedUsers = typing.List[QualityReportOverloadedUser]
QualityReportComments = typing.List[QualityReportComment]


class QualityReport(typing.TypedDict):
    total_score: int
    comments: QualityReportComments
    overloaded_users: QualityReportOverloadedUsers


class ScheduleEventUser(typing.TypedDict):
    display_name: str
    pk: str
    email: str
    avatar_full: str


class SwapRequest(typing.TypedDict):
    pk: str
    user: typing.Optional[ScheduleEventUser]


class MaybeSwappedScheduleEventUser(ScheduleEventUser):
    swap_request: typing.Optional[SwapRequest]


class ScheduleEventShift(typing.TypedDict):
    pk: str


class ScheduleEvent(typing.TypedDict):
    all_day: bool
    start: datetime.datetime
    end: datetime.datetime
    users: typing.List[MaybeSwappedScheduleEventUser]
    missing_users: typing.List[str]
    priority_level: typing.Optional[int]
    source: typing.Optional[str]
    calendar_type: typing.Optional[int]
    is_empty: bool
    is_gap: bool
    is_override: bool
    shift: ScheduleEventShift


class ScheduleFinalShift(typing.TypedDict):
    user_pk: str
    user_email: str
    user_username: str
    shift_start: str
    shift_end: str


ScheduleEvents = typing.List[ScheduleEvent]
ScheduleEventIntervals = typing.List[typing.List[datetime.datetime]]
ScheduleFinalShifts = typing.List[ScheduleFinalShift]
DurationMap = typing.Dict[str, datetime.timedelta]


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
        return get_oncall_users_for_multiple_schedules(self, events_datetime)

    def related_to_user(self, user):
        username_regex = RE_ICAL_SEARCH_USERNAME.format(user.username)
        return self.filter(
            Q(cached_ical_file_primary__regex=username_regex)
            | Q(cached_ical_file_primary__contains=user.email)
            | Q(cached_ical_file_overrides__regex=username_regex)
            | Q(cached_ical_file_overrides__contains=user.email),
            organization=user.organization,
        )


class OnCallSchedule(PolymorphicModel):
    custom_shifts: "RelatedManager['CustomOnCallShift']"
    organization: "Organization"
    shift_swap_requests: "RelatedManager['ShiftSwapRequest']"
    slack_user_group: typing.Optional["SlackUserGroup"]
    team: typing.Optional["Team"]

    objects: models.Manager["OnCallSchedule"] = PolymorphicManager.from_queryset(OnCallScheduleQuerySet)()

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

    cached_ical_final_schedule = models.TextField(null=True, default=None)

    organization = models.ForeignKey(
        "user_management.Organization", on_delete=NON_POLYMORPHIC_CASCADE, related_name="oncall_schedules"
    )

    team = models.ForeignKey(
        "user_management.Team",
        on_delete=NON_POLYMORPHIC_SET_NULL,
        related_name="oncall_schedules",
        null=True,
        default=None,
    )

    name = models.CharField(max_length=200)
    channel = models.CharField(max_length=100, null=True, default=None)

    # Slack user group to be updated when on-call users change for this schedule
    user_group = models.ForeignKey(
        to="slack.SlackUserGroup", null=True, on_delete=NON_POLYMORPHIC_SET_NULL, related_name="oncall_schedules"
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

    @property
    def web_page_link(self) -> str:
        return f"{self.organization.web_link}schedules"

    @property
    def web_detail_page_link(self) -> str:
        return f"{self.web_page_link}/{self.public_primary_key}"

    def get_icalendars(self) -> typing.Tuple[typing.Optional[icalendar.Calendar], typing.Optional[icalendar.Calendar]]:
        """Returns list of calendars. Primary calendar should always be the first"""
        # if self._ical_file_(primary|overrides) is None -> no cache, will trigger a refresh
        # if self._ical_file_(primary|overrides) == "" -> cached value for an empty schedule
        if self._ical_file_primary:
            calendar_primary: icalendar.Calendar = icalendar.Calendar.from_ical(self._ical_file_primary)
        else:
            calendar_primary = None

        if self._ical_file_overrides:
            calendar_overrides: icalendar.Calendar = icalendar.Calendar.from_ical(self._ical_file_overrides)
        else:
            calendar_overrides = None

        return calendar_primary, calendar_overrides

    def get_prev_and_current_ical_files(self):
        """Returns list of tuples with prev and current iCal files for each calendar"""
        return [
            (self.prev_ical_file_primary, self.cached_ical_file_primary),
            (self.prev_ical_file_overrides, self.cached_ical_file_overrides),
        ]

    def check_gaps_for_next_week(self) -> bool:
        today = timezone.now()
        events = self.final_events(today, today + datetime.timedelta(days=7))
        gaps = [event for event in events if event["is_gap"] and not event["is_empty"]]
        has_gaps = len(gaps) != 0
        self.has_gaps = has_gaps
        self.save(update_fields=["has_gaps"])
        return has_gaps

    def check_empty_shifts_for_next_week(self):
        today = timezone.now().date()
        empty_shifts = list_of_empty_shifts_in_schedule(self, today, today + datetime.timedelta(days=7))
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

    @property
    def _ical_file_primary(self):
        raise NotImplementedError

    @property
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

    def related_users(self):
        """Return users referenced in the schedule."""
        usernames = []
        if self.cached_ical_file_primary:
            usernames += RE_ICAL_FETCH_USERNAME.findall(self.cached_ical_file_primary)
        if self.cached_ical_file_overrides:
            usernames += RE_ICAL_FETCH_USERNAME.findall(self.cached_ical_file_overrides)
        return self.organization.users.filter(username__in=usernames)

    def filter_events(
        self,
        datetime_start: datetime.datetime,
        datetime_end: datetime.datetime,
        with_empty: bool = False,
        with_gap: bool = False,
        filter_by: str | None = None,
        all_day_datetime: bool = False,
        ignore_untaken_swaps: bool = False,
        from_cached_final: bool = False,
    ) -> ScheduleEvents:
        """Return filtered events from schedule."""
        shifts = (
            list_of_oncall_shifts_from_ical(
                self,
                datetime_start,
                datetime_end,
                with_empty,
                with_gap,
                filter_by=filter_by,
                from_cached_final=from_cached_final,
            )
            or []
        )
        events: ScheduleEvents = []
        for shift in shifts:
            start = shift["start"]
            all_day = type(start) == datetime.date
            # fix confusing end date for all-day event
            end = shift["end"] - datetime.timedelta(days=1) if all_day else shift["end"]
            if all_day and all_day_datetime:
                start = datetime.datetime.combine(start, datetime.datetime.min.time(), tzinfo=pytz.UTC)
                end = datetime.datetime.combine(end, datetime.datetime.max.time(), tzinfo=pytz.UTC).replace(
                    microsecond=0
                )
            is_gap = shift.get("is_gap", False)
            shift_json: ScheduleEvent = {
                "all_day": all_day,
                "start": start,
                "end": end,
                "users": [
                    {
                        "display_name": user.username,
                        "email": user.email,
                        "pk": user.public_primary_key,
                        "avatar_full": user.avatar_full_url,
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

        # annotate events with swap request details swapping users as needed
        events = self._apply_swap_requests(
            events, datetime_start, datetime_end, ignore_untaken_swaps=ignore_untaken_swaps
        )

        return events

    def final_events(
        self,
        datetime_start: datetime.datetime,
        datetime_end: datetime.datetime,
        with_empty: bool = True,
        with_gap: bool = True,
        ignore_untaken_swaps: bool = False,
    ) -> ScheduleEvents:
        """Return schedule final events, after resolving shifts and overrides."""
        events = self.filter_events(
            datetime_start,
            datetime_end,
            with_empty=with_empty,
            with_gap=with_gap,
            all_day_datetime=True,
            ignore_untaken_swaps=ignore_untaken_swaps,
        )
        events = self._resolve_schedule(events, datetime_start, datetime_end)
        return events

    def filter_swap_requests(
        self, datetime_start: datetime.datetime, datetime_end: datetime.time
    ) -> "RelatedManager['ShiftSwapRequest']":
        swap_requests = self.shift_swap_requests.filter(  # starting before but ongoing
            swap_start__lt=datetime_start, swap_end__gte=datetime_start
        ).union(
            self.shift_swap_requests.filter(  # starting after but before end
                swap_start__gte=datetime_start, swap_start__lte=datetime_end
            )
        )
        swap_requests = swap_requests.order_by("created_at")
        return swap_requests

    def refresh_ical_final_schedule(self):
        now = timezone.now()
        # window to consider: from now, -15 days + 6 months
        delta = EXPORT_WINDOW_DAYS_BEFORE
        days = EXPORT_WINDOW_DAYS_AFTER + delta
        datetime_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=delta)
        datetime_end = datetime_start + datetime.timedelta(days=days - 1, hours=23, minutes=59, seconds=59)

        # setup calendar with final schedule shift events
        calendar = create_base_icalendar(self.name)
        events = self.final_events(datetime_start, datetime_end, ignore_untaken_swaps=True)
        updated_ids = set()
        for e in events:
            for u in e["users"]:
                event = icalendar.Event()
                event.add(ICAL_SUMMARY, u["display_name"])
                event.add(ICAL_DATETIME_START, e["start"])
                event.add(ICAL_DATETIME_END, e["end"])
                event.add(ICAL_DATETIME_STAMP, now)
                event.add(ICAL_LAST_MODIFIED, now)
                # set priority based on primary/overrides
                # 0: undefined priority, 1: high priority
                event.add(ICAL_PRIORITY, e["calendar_type"])
                event_uid = "{}-{}-{}".format(e["shift"]["pk"], e["start"].strftime("%Y%m%d%H%S"), u["pk"])
                event[ICAL_UID] = event_uid
                calendar.add_component(event)
                updated_ids.add(event_uid)

        # check previously cached final schedule for potentially cancelled events
        if self.cached_ical_final_schedule:
            previous = icalendar.Calendar.from_ical(self.cached_ical_final_schedule)
            for component in previous.walk():
                if component.name == ICAL_COMPONENT_VEVENT and component[ICAL_UID] not in updated_ids:
                    # check if event was ended or cancelled, update ical
                    dtend = component.get(ICAL_DATETIME_END)
                    dtend_datetime = dtend.dt if dtend else None
                    if dtend_datetime and type(dtend_datetime) == datetime.date:
                        # shift or overrides coming from ical calendars can be all day events, change to datetime
                        dtend_datetime = datetime.datetime.combine(
                            dtend.dt, datetime.datetime.min.time(), tzinfo=pytz.UTC
                        )
                    if dtend_datetime and dtend_datetime < datetime_start:
                        # event ended before window start
                        continue
                    is_cancelled = component.get(ICAL_STATUS)
                    last_modified = component.get(ICAL_LAST_MODIFIED)
                    if is_cancelled and last_modified and last_modified.dt < datetime_start:
                        # drop already ended events older than the window we consider
                        continue
                    elif is_cancelled and not last_modified:
                        # set last_modified if it was missing (e.g. from previous export ical implementation)
                        component[ICAL_LAST_MODIFIED] = icalendar.vDatetime(now).to_ical()
                    elif not is_cancelled:
                        # set the event as cancelled
                        component[ICAL_DATETIME_END] = component[ICAL_DATETIME_START]
                        component[ICAL_STATUS] = ICAL_STATUS_CANCELLED
                        component[ICAL_LAST_MODIFIED] = icalendar.vDatetime(now).to_ical()
                    # include just cancelled events as well as those that were cancelled during the time window
                    calendar.add_component(component)

        ical_data = calendar.to_ical().decode()
        self.cached_ical_final_schedule = ical_data
        self.save(update_fields=["cached_ical_final_schedule"])

    def upcoming_shift_for_user(self, user, days=7):
        now = timezone.now()
        # consider an extra day before to include events from UTC yesterday
        datetime_start = now - datetime.timedelta(days=1)
        datetime_end = datetime_start + datetime.timedelta(days=days)

        current_shift = upcoming_shift = None

        if self.cached_ical_final_schedule is None:
            # no final schedule info available
            return None, None

        events = self.filter_events(datetime_start, datetime_end, all_day_datetime=True, from_cached_final=True)
        for e in events:
            if e["end"] < now:
                # shift is finished, ignore
                continue
            users = {u["pk"] for u in e["users"]}
            if user.public_primary_key in users:
                if e["start"] < now and e["end"] > now:
                    # shift is in progress
                    current_shift = e
                    continue
                upcoming_shift = e
                break

        return current_shift, upcoming_shift

    def quality_report(self, date: typing.Optional[datetime.datetime], days: typing.Optional[int]) -> QualityReport:
        """
        Return schedule quality report to be used by the web UI.
        TODO: Add scores on "inside working hours" and "balance outside working hours" when
        TODO: working hours editor is implemented in the web UI.
        """
        # get events to consider for calculation
        if date is None:
            today = timezone.now()
            date = today - datetime.timedelta(days=7 - today.weekday())  # start of next week in UTC
        if days is None:
            days = 52 * 7  # consider next 52 weeks (~1 year)
        datetime_end = date + datetime.timedelta(days=days - 1, hours=23, minutes=59, seconds=59)

        events = self.final_events(date, datetime_end)
        # an event is “good” if it's not a gap and not empty
        good_events: ScheduleEvents = [event for event in events if not event["is_gap"] and not event["is_empty"]]
        if not good_events:
            return {
                "total_score": 0,
                "comments": [{"type": QualityReportCommentType.WARNING, "text": "Schedule is empty"}],
                "overloaded_users": [],
            }

        def event_duration(ev: ScheduleEvent) -> datetime.timedelta:
            return ev["end"] - ev["start"]

        def timedelta_sum(deltas: typing.Iterable[datetime.timedelta]) -> datetime.timedelta:
            return sum(deltas, start=datetime.timedelta())

        def score_to_percent(value: float) -> int:
            return round(value * 100)

        def get_duration_map(evs: ScheduleEvents) -> DurationMap:
            """Return a map of user PKs to total duration of events they are in."""
            result: DurationMap = defaultdict(datetime.timedelta)
            for ev in evs:
                for user in ev["users"]:
                    user_pk = user["pk"]
                    result[user_pk] += event_duration(ev)

            return result

        def get_balance_score_by_duration_map(dur_map: DurationMap) -> float:
            """
            Return a score between 0 and 1, based on how balanced the durations are in the duration map.
            The formula is taken from https://github.com/grafana/oncall/issues/118#issuecomment-1161787854.
            """
            if len(dur_map) <= 1:
                return 1

            result = 0.0
            for key_1, key_2 in itertools.combinations(dur_map, 2):
                duration_1 = dur_map[key_1]
                duration_2 = dur_map[key_2]

                result += min(duration_1, duration_2) / max(duration_1, duration_2)

            number_of_pairs = len(dur_map) * (len(dur_map) - 1) // 2
            return result / number_of_pairs

        # calculate good event score
        good_events_duration = timedelta_sum(event_duration(event) for event in good_events)
        good_event_score = min(good_events_duration / datetime.timedelta(days=days), 1)
        good_event_score = score_to_percent(good_event_score)

        # calculate balance score
        duration_map = get_duration_map(good_events)
        balance_score = get_balance_score_by_duration_map(duration_map)
        balance_score = score_to_percent(balance_score)

        # calculate overloaded users
        overloaded_users: QualityReportOverloadedUsers = []

        if balance_score >= 95:  # tolerate minor imbalance
            balance_score = 100
        else:
            average_duration = timedelta_sum(duration_map.values()) / len(duration_map)
            overloaded_user_pks = [
                user_pk
                for user_pk, duration in duration_map.items()
                if score_to_percent(duration / average_duration) > 100
            ]
            usernames = {
                u.public_primary_key: u.username
                for u in User.objects.filter(public_primary_key__in=overloaded_user_pks).only(
                    "public_primary_key", "username"
                )
            }
            for user_pk in overloaded_user_pks:
                score = score_to_percent(duration_map[user_pk] / average_duration) - 100
                username = usernames.get(user_pk) or "unknown"  # fallback to "unknown" if user is not found
                overloaded_users.append({"id": user_pk, "username": username, "score": score})

            # show most overloaded users first
            overloaded_users.sort(key=lambda u: (-u["score"], u["username"]))

        # generate comments regarding gaps
        comments: QualityReportComments = []
        if good_event_score == 100:
            comments.append({"type": QualityReportCommentType.INFO, "text": "Schedule has no gaps"})
        else:
            not_covered = 100 - good_event_score
            comments.append(
                {"type": QualityReportCommentType.WARNING, "text": f"Schedule has gaps ({not_covered}% not covered)"}
            )

        # generate comments regarding balance
        if balance_score == 100:
            comments.append({"type": QualityReportCommentType.INFO, "text": "Schedule is perfectly balanced"})
        else:
            comments.append(
                {"type": QualityReportCommentType.WARNING, "text": "Schedule has balance issues (see overloaded users)"}
            )

        # calculate total score (weighted sum of good event score and balance score)
        total_score = round((good_event_score + balance_score) / 2)

        return {
            "total_score": total_score,
            "comments": comments,
            "overloaded_users": overloaded_users,
        }

    def _apply_swap_requests(
        self,
        events: ScheduleEvents,
        datetime_start: datetime.datetime,
        datetime_end: datetime.datetime,
        ignore_untaken_swaps: bool = False,
    ) -> ScheduleEvents:
        """Apply swap requests details to schedule events."""
        # get swaps requests affecting this schedule / time range
        swaps = self.filter_swap_requests(datetime_start, datetime_end)

        def _insert_event(index: int, event: ScheduleEvent) -> int:
            # add event, if any, to events list in the specified index
            # return incremented index if the event was added
            if event is None:
                return index
            events.insert(index, event)
            return index + 1

        # apply swaps sequentially
        for swap in swaps:
            if swap.is_past_due or (ignore_untaken_swaps and not swap.is_taken):
                # ignore expired requests, or untaken if specified
                continue
            i = 0
            while i < len(events):
                event = events.pop(i)

                if event["start"] >= swap.swap_end or event["end"] <= swap.swap_start:
                    # event outside the swap period, keep as it is and continue
                    i = _insert_event(i, event)
                    continue

                users = set(u["pk"] for u in event["users"])
                if swap.beneficiary.public_primary_key in users:
                    # swap request affects current event

                    split_before = None
                    if event["start"] < swap.swap_start:
                        # partially included start -> split
                        split_before = copy.deepcopy(event)
                        split_before["end"] = swap.swap_start
                        # update event to swap
                        event["start"] = swap.swap_start

                    split_after = None
                    if event["end"] > swap.swap_end:
                        # partially included end -> split
                        split_after = copy.deepcopy(event)
                        split_after["start"] = swap.swap_end
                        # update event to swap
                        event["end"] = swap.swap_end

                    # identify user to swap
                    user_to_swap = None
                    for u in event["users"]:
                        if u["pk"] == swap.beneficiary.public_primary_key:
                            user_to_swap = u
                            break

                    # apply swap changes to event user
                    swap_details = {"pk": swap.public_primary_key}
                    if swap.benefactor:
                        # swap is taken, update user in shift
                        user_to_swap["pk"] = swap.benefactor.public_primary_key
                        user_to_swap["display_name"] = swap.benefactor.username
                        user_to_swap["email"] = swap.benefactor.email
                        user_to_swap["avatar_full"] = swap.benefactor.avatar_full_url
                        # add beneficiary user to details
                        swap_details["user"] = {
                            "display_name": swap.beneficiary.username,
                            "email": swap.beneficiary.email,
                            "pk": swap.beneficiary.public_primary_key,
                            "avatar_full": swap.beneficiary.avatar_full_url,
                        }
                    user_to_swap["swap_request"] = swap_details

                    # update events list
                    # keep first split event in its original index
                    i = _insert_event(i, split_before)
                    # insert updated swap-related event
                    i = _insert_event(i, event)
                    # keep second split event after swap
                    i = _insert_event(i, split_after)
                else:
                    # event for different user(s), keep as it is and continue
                    i = _insert_event(i, event)

        return events

    def _resolve_schedule(
        self, events: ScheduleEvents, datetime_start: datetime.datetime, datetime_end: datetime.datetime
    ) -> ScheduleEvents:
        """Calculate final schedule shifts considering rotations and overrides.

        Exclude events that after split/update are out of the requested (datetime_start, datetime_end) range.
        """
        if not events:
            return []

        def event_start_cmp_key(e: ScheduleEvent) -> datetime.datetime:
            return e["start"]

        def event_cmp_key(e: ScheduleEvent) -> typing.Tuple[int, int, datetime.datetime]:
            """Sorting key criteria for events."""
            start = event_start_cmp_key(e)
            return (
                -e["calendar_type"] if e["calendar_type"] else 0,  # overrides: 1, shifts: 0, gaps: None
                -e["priority_level"] if e["priority_level"] else 0,
                start,
            )

        def insort_event(eventlist: ScheduleEvents, e: ScheduleEvent) -> None:
            """Insert event keeping ordering criteria into already sorted event list."""
            idx = 0
            for i in eventlist:
                if event_cmp_key(e) > event_cmp_key(i):
                    idx += 1
                else:
                    break
            eventlist.insert(idx, e)

        def _merge_intervals(evs: ScheduleEvents) -> ScheduleEventIntervals:
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
        resolved: ScheduleEvents = []
        pending: ScheduleEvents = events
        current_interval_idx = 0  # current scheduled interval being checked
        current_type: typing.Optional[int] = OnCallSchedule.TYPE_ICAL_OVERRIDES  # current calendar type
        current_priority: typing.Optional[int] = None  # current priority level being resolved

        while pending:
            ev = pending.pop(0)

            if ev["is_empty"]:
                # exclude events without active users
                continue

            if ev["start"] >= datetime_end or ev["end"] <= datetime_start:
                # avoid including split events which now are outside the requested time range
                continue

            # api/terraform shifts could be missing a priority; assume None means 0
            priority = ev["priority_level"] or 0
            if priority != current_priority or current_type != ev["calendar_type"]:
                # update scheduled intervals on priority change
                # and start from the beginning for the new priority level
                # also for calendar event type (overrides first, then apply regular shifts)
                resolved.sort(key=event_start_cmp_key)
                intervals = _merge_intervals(resolved)
                current_interval_idx = 0
                current_priority = priority
                current_type = ev["calendar_type"]

            if current_interval_idx >= len(intervals):
                # event outside scheduled intervals, add to resolved
                # only if still starts before datetime_end
                if ev["start"] < datetime_end:
                    resolved.append(ev)

            elif ev["start"] < intervals[current_interval_idx][0] and ev["end"] <= intervals[current_interval_idx][0]:
                # event starts and ends outside an already scheduled interval, add to resolved
                resolved.append(ev)

            elif ev["start"] < intervals[current_interval_idx][0] and ev["end"] > intervals[current_interval_idx][0]:
                # event starts outside interval but overlaps with an already scheduled interval
                # 1. add a split event copy to schedule the time before the already scheduled interval
                to_add = ev.copy()
                to_add["end"] = intervals[current_interval_idx][0]
                if to_add["end"] >= datetime_start:
                    # only include if updated event ends inside the requested time range
                    resolved.append(to_add)
                # 2. check if there is still time to be scheduled after the current scheduled interval ends
                if ev["end"] > intervals[current_interval_idx][1]:
                    # event ends after current interval, update event start timestamp to match the interval end
                    # and process the updated event as any other event
                    ev["start"] = intervals[current_interval_idx][1]
                    if ev["start"] < datetime_end:
                        # only include event if it is still inside the requested time range
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

        resolved.sort(key=lambda e: (event_start_cmp_key(e), e["shift"]["pk"] or ""))
        return resolved

    def _merge_events(self, events: ScheduleEvents) -> ScheduleEvents:
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
                    current["users"] += [u for u in next_event["users"] if u not in current["users"]]
                    current["missing_users"] += [
                        u for u in next_event["missing_users"] if u not in current["missing_users"]
                    ]
                else:
                    merged.append(next_event)
                    current = next_event
            events = merged
        return events

    def _generate_ical_file_from_shifts(self, qs, extra_shifts=None, allow_empty_users=False):
        """Generate iCal events file from custom on-call shifts."""
        # default to empty string since it is not possible to have a no-events ical file
        ical = ""
        if qs.exists() or extra_shifts is not None:
            if extra_shifts is None:
                extra_shifts = []
            end_line = "END:VCALENDAR"
            calendar = icalendar.Calendar()
            calendar.add("prodid", "-//web schedule//oncall//")
            calendar.add("version", "2.0")
            calendar.add("method", "PUBLISH")
            ical_file = calendar.to_ical().decode()
            ical = ical_file.replace(end_line, "").strip()
            ical = f"{ical}\r\n"
            for event in itertools.chain(qs.all(), extra_shifts):
                ical += event.convert_to_ical(allow_empty_users=allow_empty_users)
            ical += f"{end_line}\r\n"
        return ical

    def preview_shift(self, custom_shift, datetime_start, datetime_end, updated_shift_pk=None):
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
            # only reuse PK for preview when updating a rotation that won't be started after the update
            custom_shift.public_primary_key = updated_shift_pk
            qs = qs.exclude(public_primary_key=updated_shift_pk)

        ical_file = self._generate_ical_file_from_shifts(qs, extra_shifts=extra_shifts, allow_empty_users=True)

        original_value = getattr(self, ical_attr)
        _invalidate_cache(self, ical_property)
        setattr(self, ical_attr, ical_file)

        # filter events using a temporal overriden calendar including the not-yet-saved shift
        events = self.filter_events(datetime_start, datetime_end, with_empty=True, with_gap=True)

        # return preview events for affected shifts
        updated_shift_pks = {s.public_primary_key for s in extra_shifts}
        shift_events = [e.copy() for e in events if e["shift"]["pk"] in updated_shift_pks]
        final_events = self._resolve_schedule(events, datetime_start, datetime_end)

        _invalidate_cache(self, ical_property)
        setattr(self, ical_attr, original_value)

        return shift_events, final_events

    # Insight logs
    @property
    def insight_logs_verbal(self):
        return self.name

    @property
    def insight_logs_serialized(self):
        result = {
            "name": self.name,
        }
        if self.team:
            result["team"] = self.team.name
            result["team_id"] = self.team.public_primary_key
        else:
            result["team"] = "General"
        if self.organization.slack_team_identity:
            if self.channel:
                from apps.slack.models import SlackChannel

                sti = self.organization.slack_team_identity
                slack_channel = SlackChannel.objects.filter(slack_team_identity=sti, slack_id=self.channel).first()
                if slack_channel:
                    result["slack_channel"] = slack_channel.name
            if self.user_group is not None:
                result["user_group"] = self.user_group.handle

            result["notification_frequency"] = self.get_notify_oncall_shift_freq_display()
            result["current_shift_notification"] = self.mention_oncall_start
            result["next_shift_notification"] = self.mention_oncall_next
            result["notify_empty_oncall"] = self.get_notify_empty_oncall_display()
        return result

    @property
    def insight_logs_metadata(self):
        result = {}
        if self.team:
            result["team"] = self.team.name
            result["team_id"] = self.team.public_primary_key
        else:
            result["team"] = "General"
        return result


class OnCallScheduleICal(OnCallSchedule):
    escalation_policies: "RelatedManager['EscalationPolicy']"
    objects: models.Manager["OnCallScheduleICal"]
    schedule_export_token: "RelatedManager['ScheduleExportAuthToken']"

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

    # Insight logs
    @property
    def insight_logs_serialized(self):
        res = super().insight_logs_serialized
        res["primary_calendar_url"] = self.ical_url_primary
        res["overrides_calendar_url"] = self.ical_url_overrides
        return res

    @property
    def insight_logs_type_verbal(self):
        return "ical_schedule"


class OnCallScheduleCalendar(OnCallSchedule):
    escalation_policies: "RelatedManager['EscalationPolicy']"
    objects: models.Manager["OnCallScheduleCalendar"]
    schedule_export_token: "RelatedManager['ScheduleExportAuthToken']"

    # For the calendar schedule only overrides ical is imported via ical url.
    ical_url_overrides = models.CharField(max_length=500, null=True, default=None)
    ical_file_error_overrides = models.CharField(max_length=200, null=True, default=None)

    # Primary ical is generated from custom_on_call_shifts.
    time_zone = models.CharField(max_length=100, default="UTC")
    custom_on_call_shifts = models.ManyToManyField("schedules.CustomOnCallShift", related_name="schedules")

    enable_web_overrides = models.BooleanField(default=False, null=True)

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
        if self.cached_ical_file_overrides is not None:
            return self.cached_ical_file_overrides

        self._refresh_overrides_ical_file()
        return self.cached_ical_file_overrides

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

        if self.enable_web_overrides:
            # web overrides
            qs = self.custom_shifts.filter(type=CustomOnCallShift.TYPE_OVERRIDE)
            self.cached_ical_file_overrides = self._generate_ical_file_from_shifts(qs)
        elif self.ical_url_overrides is not None:
            self.cached_ical_file_overrides, self.ical_file_error_overrides = fetch_ical_file_or_get_error(
                self.ical_url_overrides,
            )

        self.save(update_fields=["cached_ical_file_overrides", "prev_ical_file_overrides", "ical_file_error_overrides"])

    def _generate_ical_file_primary(self):
        """
        Generate iCal events file from custom on-call shifts (created via API)
        """
        # default to empty string since it is not possible to have a no-events ical file
        ical = ""
        if self.custom_on_call_shifts.exists():
            end_line = "END:VCALENDAR"
            calendar = icalendar.Calendar()
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

    def preview_shift(self, custom_shift, datetime_start, datetime_end, updated_shift_pk=None):
        """Return unsaved rotation and final schedule preview events."""
        if custom_shift.type != CustomOnCallShift.TYPE_OVERRIDE:
            raise ValueError("Invalid shift type")
        return super().preview_shift(custom_shift, datetime_start, datetime_end, updated_shift_pk=updated_shift_pk)

    @property
    def insight_logs_type_verbal(self):
        return "calendar_schedule"

    @property
    def insight_logs_serialized(self):
        res = super().insight_logs_serialized
        res["overrides_calendar_url"] = self.ical_url_overrides
        return res


class OnCallScheduleWeb(OnCallSchedule):
    escalation_policies: "RelatedManager['EscalationPolicy']"
    objects: models.Manager["OnCallScheduleWeb"]
    schedule_export_token: "RelatedManager['ScheduleExportAuthToken']"

    time_zone = models.CharField(max_length=100, default="UTC")

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
            try:
                self.save(update_fields=["cached_ical_file_primary"])
            except DatabaseError:
                # schedule may have been deleted from db
                return
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
            try:
                self.save(update_fields=["cached_ical_file_overrides"])
            except DatabaseError:
                # schedule may have been deleted from db
                return
        return self.cached_ical_file_overrides

    def _refresh_overrides_ical_file(self):
        self.prev_ical_file_overrides = self.cached_ical_file_overrides
        self.cached_ical_file_overrides = self._generate_ical_file_overrides()
        self.save(update_fields=["cached_ical_file_overrides", "prev_ical_file_overrides"])

    # Insight logs
    @property
    def insight_logs_type_verbal(self):
        return "web_schedule"

    @property
    def insight_logs_serialized(self):
        res = super().insight_logs_serialized
        res["time_zone"] = self.time_zone
        return res
