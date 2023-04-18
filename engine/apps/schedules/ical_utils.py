from __future__ import annotations

import datetime
import logging
import re
import typing
from collections import namedtuple
from typing import TYPE_CHECKING

import pytz
import requests
from django.apps import apps
from django.db.models import Q
from django.utils import timezone
from icalendar import Calendar

from apps.api.permissions import RBACPermission
from apps.schedules.constants import (
    ICAL_ATTENDEE,
    ICAL_DATETIME_END,
    ICAL_DATETIME_START,
    ICAL_DESCRIPTION,
    ICAL_SUMMARY,
    ICAL_UID,
    RE_EVENT_UID_V1,
    RE_EVENT_UID_V2,
    RE_PRIORITY,
)
from apps.schedules.ical_events import ical_events
from common.timezones import is_valid_timezone
from common.utils import timed_lru_cache

"""
This is a hack to allow us to load models for type checking without circular dependencies.
This module likely needs to refactored to be part of the OnCallSchedule module.
"""
if TYPE_CHECKING:
    from apps.schedules.models import OnCallSchedule
    from apps.user_management.models import Organization, User
    from apps.user_management.models.user import UserQuerySet

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def users_in_ical(
    usernames_from_ical: typing.List[str],
    organization: Organization,
    include_viewers=False,
    users_to_filter: typing.Optional[UserQuerySet] = None,
) -> UserQuerySet:
    """
    This method returns a `UserQuerySet`, filtered by users whose username, or case-insensitive e-mail,
    is present in `usernames_from_ical`. If `include_viewers` is set to `True`, users are further filtered down
    based on their granted permissions.

    Parameters
    ----------
    usernames_from_ical : typing.List[str]
        A list of usernames present in the ical feed
    organization : apps.user_management.models.organization.Organization
        The organization in question
    include_viewers : bool
        Whether or not the list should be further filtered to exclude users based on granted permissions
    users_to_filter : typing.Optional[UserQuerySet]
        Filter users without making SQL queries if users_to_filter arg is provided
        users_to_filter is passed in `apps.schedules.ical_utils.get_oncall_users_for_multiple_schedules`
    """
    from apps.user_management.models import User

    emails_from_ical = [username.lower() for username in usernames_from_ical]

    if users_to_filter is not None:
        return list(
            {
                user
                for user in users_to_filter
                if user.username in usernames_from_ical or user.email.lower() in emails_from_ical
            }
        )

    users_found_in_ical = organization.users
    if not include_viewers:
        users_found_in_ical = users_found_in_ical.filter(
            **User.build_permissions_query(RBACPermission.Permissions.SCHEDULES_WRITE, organization)
        )

    users_found_in_ical = users_found_in_ical.filter(
        (Q(username__in=usernames_from_ical) | Q(email__lower__in=emails_from_ical))
    ).distinct()

    return users_found_in_ical


@timed_lru_cache(timeout=100)
def memoized_users_in_ical(usernames_from_ical: typing.List[str], organization: Organization) -> UserQuerySet:
    # using in-memory cache instead of redis to avoid pickling python objects
    return users_in_ical(usernames_from_ical, organization)


# used for display schedule events on web
def list_of_oncall_shifts_from_ical(
    schedule,
    date,
    user_timezone="UTC",
    with_empty_shifts=False,
    with_gaps=False,
    days=1,
    filter_by=None,
):
    """
    Parse the ical file and return list of events with users
    This function is used in serializer for api schedules/events/ endpoint
    Example output:
    [
        {
            "start": datetime.datetime(2021, 7, 8, 5, 30, tzinfo=<UTC>,
            "end": datetime.datetime(2021, 7, 8, 13, 15, tzinfo=<UTC>),
            "users": <QuerySet [<User: User object (1)>]>,
            "priority": 0,
            "source": None,
            "calendar_type": 0
        }
    ]
    """
    OnCallSchedule = apps.get_model("schedules", "OnCallSchedule")

    # get list of iCalendars from current iCal files. If there is more than one calendar, primary calendar will always
    # be the first
    calendars = schedule.get_icalendars()

    # TODO: Review offset usage
    user_timezone_offset = timezone.datetime.now().astimezone(pytz.timezone(user_timezone)).utcoffset()
    datetime_min = timezone.datetime.combine(date, datetime.time.min) + timezone.timedelta(milliseconds=1)
    datetime_start = (datetime_min - user_timezone_offset).astimezone(pytz.UTC)
    datetime_end = datetime_start + timezone.timedelta(days=days - 1, hours=23, minutes=59, seconds=59)

    result_datetime = []
    result_date = []

    for idx, calendar in enumerate(calendars):
        if calendar is not None:
            if idx == 0:
                calendar_type = OnCallSchedule.PRIMARY
            else:
                calendar_type = OnCallSchedule.OVERRIDES

            if filter_by is not None and filter_by != calendar_type:
                continue

            tmp_result_datetime, tmp_result_date = get_shifts_dict(
                calendar, calendar_type, schedule, datetime_start, datetime_end, with_empty_shifts
            )
            result_datetime.extend(tmp_result_datetime)
            result_date.extend(tmp_result_date)

    if with_gaps and len(result_date) == 0:
        as_intervals = [DatetimeInterval(shift["start"], shift["end"]) for shift in result_datetime]
        gaps = detect_gaps(as_intervals, datetime_start, datetime_end)
        for g in gaps:
            result_datetime.append(
                {
                    "start": g.start if g.start else datetime_start,
                    "end": g.end if g.end else datetime_end,
                    "users": [],
                    "missing_users": [],
                    "priority": None,
                    "source": None,
                    "calendar_type": None,
                    "is_gap": True,
                    "shift_pk": None,
                }
            )
    result = sorted(result_datetime, key=lambda dt: dt["start"]) + result_date
    # if there is no events, return None
    return result or None


def get_shifts_dict(calendar, calendar_type, schedule, datetime_start, datetime_end, with_empty_shifts=False):
    events = ical_events.get_events_from_ical_between(calendar, datetime_start, datetime_end)
    result_datetime = []
    result_date = []
    for event in events:
        priority = parse_priority_from_string(event.get(ICAL_SUMMARY, "[L0]"))
        pk, source = parse_event_uid(event.get(ICAL_UID))
        users = get_users_from_ical_event(event, schedule.organization)
        missing_users = get_missing_users_from_ical_event(event, schedule.organization)
        # Define on-call shift out of ical event that has the actual user
        if len(users) > 0 or with_empty_shifts:
            if type(event[ICAL_DATETIME_START].dt) == datetime.date:
                start = event[ICAL_DATETIME_START].dt
                end = event[ICAL_DATETIME_END].dt
                result_date.append(
                    {
                        "start": start,
                        "end": end,
                        "users": users,
                        "missing_users": missing_users,
                        "priority": priority,
                        "source": source,
                        "calendar_type": calendar_type,
                        "shift_pk": pk,
                    }
                )
            else:
                start, end = ical_events.get_start_and_end_with_respect_to_event_type(event)
                if start < end:
                    result_datetime.append(
                        {
                            "start": start.astimezone(pytz.UTC),
                            "end": end.astimezone(pytz.UTC),
                            "users": users,
                            "missing_users": missing_users,
                            "priority": priority,
                            "source": source,
                            "calendar_type": calendar_type,
                            "shift_pk": pk,
                        }
                    )
    return result_datetime, result_date


EmptyShift = namedtuple(
    "EmptyShift",
    ["start", "end", "summary", "description", "attendee", "all_day", "calendar_type", "calendar_tz", "shift_pk"],
)


def list_of_empty_shifts_in_schedule(schedule, start_date, end_date):
    """
    Parse the ical file and return list of EmptyShift.
    """
    # Calculate lookup window in schedule's tz
    # If we can't get tz from ical use UTC
    OnCallSchedule = apps.get_model("schedules", "OnCallSchedule")

    calendars = schedule.get_icalendars()
    empty_shifts = []
    for idx, calendar in enumerate(calendars):
        if calendar is not None:
            if idx == 0:
                calendar_type = OnCallSchedule.PRIMARY
            else:
                calendar_type = OnCallSchedule.OVERRIDES

            calendar_tz = get_icalendar_tz_or_utc(calendar)

            schedule_timezone_offset = timezone.datetime.now().astimezone(calendar_tz).utcoffset()
            start_datetime = timezone.datetime.combine(start_date, datetime.time.min) + timezone.timedelta(
                milliseconds=1
            )
            start_datetime_with_offset = (start_datetime - schedule_timezone_offset).astimezone(pytz.UTC)
            end_datetime = timezone.datetime.combine(end_date, datetime.time.max)
            end_datetime_with_offset = (end_datetime - schedule_timezone_offset).astimezone(pytz.UTC)

            events = ical_events.get_events_from_ical_between(
                calendar, start_datetime_with_offset, end_datetime_with_offset
            )

            # Keep hashes of checked events to include only first recurrent event into result
            checked_events = set()
            empty_shifts_per_calendar = []
            for event in events:
                users = get_users_from_ical_event(event, schedule.organization)
                if len(users) == 0:
                    summary = event.get(ICAL_SUMMARY, "")
                    description = event.get(ICAL_DESCRIPTION, "")
                    attendee = event.get(ICAL_ATTENDEE, "")
                    pk, _ = parse_event_uid(event.get(ICAL_UID))

                    event_hash = hash(f"{event[ICAL_UID]}{summary}{description}{attendee}")
                    if event_hash in checked_events:
                        continue

                    checked_events.add(event_hash)

                    start, end, all_day = event_start_end_all_day_with_respect_to_type(event, calendar_tz)
                    if not all_day:
                        start = start.astimezone(pytz.UTC)
                        end = end.astimezone(pytz.UTC)

                    empty_shifts_per_calendar.append(
                        EmptyShift(
                            start=start,
                            end=end,
                            summary=summary,
                            description=description,
                            attendee=attendee,
                            all_day=all_day,
                            calendar_type=calendar_type,
                            calendar_tz=calendar_tz,
                            shift_pk=pk,
                        )
                    )
            empty_shifts.extend(empty_shifts_per_calendar)

    return sorted(empty_shifts, key=lambda dt: dt.start)


def list_users_to_notify_from_ical(
    schedule, events_datetime=None, include_viewers=False, users_to_filter=None
) -> UserQuerySet:
    """
    Retrieve on-call users for the current time
    """
    events_datetime = events_datetime if events_datetime else timezone.datetime.now(timezone.utc)
    return list_users_to_notify_from_ical_for_period(
        schedule,
        events_datetime,
        events_datetime,
        include_viewers=include_viewers,
        users_to_filter=users_to_filter,
    )


def list_users_to_notify_from_ical_for_period(
    schedule,
    start_datetime,
    end_datetime,
    include_viewers=False,
    users_to_filter=None,
) -> UserQuerySet:
    # get list of iCalendars from current iCal files. If there is more than one calendar, primary calendar will always
    # be the first
    calendars = schedule.get_icalendars()
    # reverse calendars to make overrides calendar the first, if schedule is iCal
    calendars = calendars[::-1]
    users_found_in_ical = []
    # at first check overrides calendar and return users from it if it exists and on-call users are found
    for calendar in calendars:
        if calendar is None:
            continue
        events = ical_events.get_events_from_ical_between(calendar, start_datetime, end_datetime)
        parsed_ical_events = {}  # event info where key is event priority and value list of found usernames {0:["alex"]}
        for event in events:
            current_usernames, current_priority = get_usernames_from_ical_event(event)
            parsed_ical_events.setdefault(current_priority, []).extend(current_usernames)
        # find users by usernames. if users are not found for shift, get users from lower priority
        for _, usernames in sorted(parsed_ical_events.items(), reverse=True):
            users_found_in_ical = users_in_ical(
                usernames, schedule.organization, include_viewers=include_viewers, users_to_filter=users_to_filter
            )
            if users_found_in_ical:
                break
        if users_found_in_ical:
            # if users are found in the overrides calendar, there is no need to check primary calendar
            break
    return users_found_in_ical


def get_oncall_users_for_multiple_schedules(
    schedules, events_datetime=None
) -> typing.Dict[OnCallSchedule, typing.List[User]]:
    from apps.user_management.models import User

    if events_datetime is None:
        events_datetime = timezone.datetime.now(timezone.utc)

    # Exit early if there are no schedules
    if not schedules.exists():
        return {}

    # Assume all schedules from the queryset belong to the same organization
    organization = schedules[0].organization

    # Gather usernames from all events from all schedules
    usernames = set()
    for schedule in schedules.all():
        calendars = schedule.get_icalendars()
        for calendar in calendars:
            if calendar is None:
                continue
            events = ical_events.get_events_from_ical_between(calendar, events_datetime, events_datetime)
            for event in events:
                current_usernames, _ = get_usernames_from_ical_event(event)
                usernames.update(current_usernames)

    # Fetch relevant users from the db
    emails = [username.lower() for username in usernames]
    users = organization.users.filter(
        Q(**User.build_permissions_query(RBACPermission.Permissions.SCHEDULES_WRITE, organization))
        & (Q(username__in=usernames) | Q(email__lower__in=emails))
    )

    # Get on-call users
    oncall_users = {}
    for schedule in schedules.all():
        # pass user list to list_users_to_notify_from_ical
        schedule_oncall_users = list_users_to_notify_from_ical(
            schedule, events_datetime=events_datetime, users_to_filter=users
        )
        oncall_users.update({schedule.pk: schedule_oncall_users})

    return oncall_users


def parse_username_from_string(string):
    """
    Parse on-call shift user from the given string
    Example input:
    [L1] bob@company.com
    Example output:
    bob@company.com
    """
    return re.sub(RE_PRIORITY, "", string.strip(), 1).strip()


def parse_priority_from_string(string):
    """
    Parse on-call shift priority from the given string
    Example input:
    [L1] @alex @bob
    Example output:
    1
    """
    priority = re.findall(RE_PRIORITY, string.strip())
    if len(priority) > 0:
        priority = int(priority[0])
        if priority < 1:
            priority = 0
    else:
        priority = 0
    return priority


def parse_event_uid(string):
    pk = None
    source = None
    source_verbal = None

    match = RE_EVENT_UID_V2.match(string)
    if match:
        _, pk, _, _, source = match.groups()
    else:
        # eventually this path would be automatically deprecated
        # once all ical representations are refreshed
        match = RE_EVENT_UID_V1.match(string)
        if match:
            _, _, _, source = match.groups()
        else:
            # fallback to use the UID string as the rotation ID
            pk = string

    if source is not None:
        source = int(source)
        CustomOnCallShift = apps.get_model("schedules", "CustomOnCallShift")
        source_verbal = CustomOnCallShift.SOURCE_CHOICES[source][1]

    return pk, source_verbal


def get_usernames_from_ical_event(event):
    usernames_found = []
    priority = parse_priority_from_string(event.get(ICAL_SUMMARY, "[L0]"))
    if ICAL_SUMMARY in event:
        usernames_found.append(parse_username_from_string(event[ICAL_SUMMARY]))
    if ICAL_DESCRIPTION in event:
        usernames_found.append(parse_username_from_string(event[ICAL_DESCRIPTION]))
    if ICAL_ATTENDEE in event:
        if isinstance(event[ICAL_ATTENDEE], str):
            # PagerDuty adds only one attendee and in this case event[ICAL_ATTENDEE] is string.
            # If several attendees were added to the event than event[ICAL_ATTENDEE] will be list
            # (E.g. several invited in Google cal).
            usernames_found.append(parse_username_from_string(event[ICAL_ATTENDEE]))
    return usernames_found, priority


def get_missing_users_from_ical_event(event, organization):
    all_usernames, _ = get_usernames_from_ical_event(event)
    users = list(get_users_from_ical_event(event, organization))
    found_usernames = [u.username for u in users]
    found_emails = [u.email.lower() for u in users]
    return [u for u in all_usernames if u != "" and u not in found_usernames and u.lower() not in found_emails]


def get_users_from_ical_event(event, organization):
    usernames_from_ical, _ = get_usernames_from_ical_event(event)
    users = []
    if len(usernames_from_ical) != 0:
        users = memoized_users_in_ical(tuple(usernames_from_ical), organization)
    return users


def is_icals_equal_line_by_line(first, second):
    first = first.split("\n")
    second = second.split("\n")
    if len(first) != len(second):
        return False
    else:
        for idx, first_item in enumerate(first):
            if first_item.startswith("DTSTAMP"):
                continue
            else:
                second_item = second[idx]
                if first_item != second_item:
                    return False

    return True


def is_icals_equal(first, second):
    first_cal = Calendar.from_ical(first)
    if first_cal.get("PRODID", None) in ("-//My calendar product//amixr//", "-//web schedule//oncall//"):
        # Compare schedules generated by oncall line by line, since they not support SEQUENCE field yet.
        # But we are sure that same calendars will have same lines, since we are generating it.
        return is_icals_equal_line_by_line(first, second)
    else:
        # Compare external calendars by events, since sometimes they contain different lines even for equal calendars.
        second_cal = Calendar.from_ical(second)
        first_subcomponents = first_cal.subcomponents
        second_subcomponents = second_cal.subcomponents
        if len(first_subcomponents) != len(second_subcomponents):
            return False
        first_cal_events = {}
        second_cal_events = {}
        for cmp in first_cal.subcomponents:
            first_cal_events[cmp.get("UID", None)] = cmp.get("SEQUENCE", None)
        for cmp in second_cal.subcomponents:
            second_cal_events[cmp.get("UID", None)] = cmp.get("SEQUENCE", None)
        for first_uid, first_seq in first_cal_events.items():
            if first_uid not in second_cal_events:
                return False
            second_seq = second_cal_events.get(first_uid, None)
            if first_seq != second_seq:
                return False
        return True


def ical_date_to_datetime(date, tz, start):
    datetime_to_combine = datetime.time.min
    all_day = False
    if type(date) == datetime.date:
        all_day = True
        calendar_timezone_offset = timezone.datetime.now().astimezone(tz).utcoffset()
        date = timezone.datetime.combine(date, datetime_to_combine).astimezone(tz) - calendar_timezone_offset
        if not start:
            date -= timezone.timedelta(seconds=1)
    return date, all_day


def calculate_shift_diff(first_shift, second_shift):
    fields_to_compare = ["users", "end", "start", "all_day", "priority"]

    shift_changed = set(first_shift.keys()) != set(second_shift.keys())
    if not shift_changed:
        diff = set()
        for k, v in first_shift.items():
            for f in fields_to_compare:
                if v.get(f) != second_shift[k].get(f):
                    shift_changed = True
                    diff.add(k)
                    break
    else:
        diff = set(first_shift.keys()) - set(second_shift.keys())

    return shift_changed, diff


def get_icalendar_tz_or_utc(icalendar):
    try:
        calendar_timezone = icalendar.walk("VTIMEZONE")[0]["TZID"]
    except (IndexError, KeyError):
        calendar_timezone = "UTC"

    if pytz_timezone := is_valid_timezone(calendar_timezone):
        return pytz_timezone

    # try to convert the timezone from windows to iana
    if (converted_timezone := convert_windows_timezone_to_iana(calendar_timezone)) is None:
        return "UTC"

    return pytz.timezone(converted_timezone)


def fetch_ical_file_or_get_error(ical_url):
    cached_ical_file = None
    ical_file_error = None
    try:
        new_ical_file = fetch_ical_file(ical_url)
        Calendar.from_ical(new_ical_file)
        cached_ical_file = new_ical_file
    except requests.exceptions.RequestException:
        ical_file_error = "iCal download failed"
    except ValueError:
        ical_file_error = "wrong iCal"
    # TODO: catch icalendar exceptions
    return cached_ical_file, ical_file_error


def fetch_ical_file(ical_url):
    # without user-agent header google calendar sometimes returns text/html instead of text/calendar
    headers = {"User-Agent": "Grafana OnCall"}
    r = requests.get(ical_url, headers=headers, timeout=10)
    logger.info(f"fetch_ical_file: content-type={r.headers.get('Content-Type')}")
    ical_file = r.text
    return ical_file


def create_base_icalendar(name: str) -> Calendar:
    cal = Calendar()
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", name)
    cal.add("x-wr-timezone", "UTC")
    cal.add("version", "2.0")
    cal.add("prodid", "//Grafana Labs//Grafana On-Call//")

    return cal


def get_events_from_calendars(ical_obj: Calendar, calendars: tuple) -> None:
    for calendar in calendars:
        if calendar:
            for component in calendar.walk():
                if component.name == "VEVENT":
                    ical_obj.add_component(component)


def get_user_events_from_calendars(ical_obj: Calendar, calendars: tuple, user: User, name: str = None) -> None:
    for calendar in calendars:
        if calendar:
            for component in calendar.walk():
                if component.name == "VEVENT":
                    event_user = get_usernames_from_ical_event(component)
                    event_user_value = event_user[0][0]
                    if event_user_value == user.username or event_user_value.lower() == user.email.lower():
                        if name:
                            component["SUMMARY"] = "{}: {}".format(name, component["SUMMARY"])
                        ical_obj.add_component(component)


def _is_final_export_enabled(schedule: OnCallSchedule) -> bool:
    DynamicSetting = apps.get_model("base", "DynamicSetting")
    enabled_final_export = DynamicSetting.objects.get_or_create(
        name="enabled_final_schedule_export",
        defaults={
            "json_value": {
                "schedule_ids": [],
            }
        },
    )[0]
    return schedule.public_primary_key in enabled_final_export.json_value["schedule_ids"]


def _get_ical_data_final_schedule(schedule: OnCallSchedule) -> str:
    ical_data = schedule.cached_ical_final_schedule
    if ical_data is None:
        schedule.refresh_ical_final_schedule()
        ical_data = schedule.cached_ical_final_schedule
    return ical_data


def ical_export_from_schedule(schedule: OnCallSchedule) -> bytes:
    if _is_final_export_enabled(schedule):
        ical_data = _get_ical_data_final_schedule(schedule)
        return ical_data.encode()
    else:
        calendars = schedule.get_icalendars()
        ical_obj = create_base_icalendar(schedule.name)
        get_events_from_calendars(ical_obj, calendars)
        return ical_obj.to_ical()


def user_ical_export(user: User, schedules: list[OnCallSchedule]) -> bytes:
    schedule_name = "On-Call Schedule for {0}".format(user.username)
    ical_obj = create_base_icalendar(schedule_name)

    for schedule in schedules:
        if _is_final_export_enabled(schedule):
            name = schedule.name
            ical_data = _get_ical_data_final_schedule(schedule)
            calendars = [Calendar.from_ical(ical_data)]
        else:
            name = None
            calendars = schedule.get_icalendars()
        get_user_events_from_calendars(ical_obj, calendars, user, name=name)

    return ical_obj.to_ical()


DatetimeInterval = namedtuple("DatetimeInterval", ["start", "end"])


def list_of_gaps_in_schedule(schedule, start_date, end_date):
    calendars = schedule.get_icalendars()
    intervals = []
    start_datetime = timezone.datetime.combine(start_date, datetime.time.min) + timezone.timedelta(milliseconds=1)
    start_datetime = start_datetime.astimezone(pytz.UTC)
    end_datetime = timezone.datetime.combine(end_date, datetime.time.max).astimezone(pytz.UTC)

    for idx, calendar in enumerate(calendars):
        if calendar is not None:
            calendar_tz = get_icalendar_tz_or_utc(calendar)
            events = ical_events.get_events_from_ical_between(
                calendar,
                start_datetime,
                end_datetime,
            )
            for event in events:
                start, end, _ = event_start_end_all_day_with_respect_to_type(event, calendar_tz)
                intervals.append(DatetimeInterval(start, end))
    return detect_gaps(intervals, start_datetime, end_datetime)


def detect_gaps(intervals, start, end):
    gaps = []
    intervals = sorted(intervals, key=lambda dt: dt.start)
    if len(intervals) > 0:
        base_interval = intervals[0]
        if base_interval.start > start:
            gaps.append(DatetimeInterval(None, base_interval.start))
        for interval in intervals[1:]:
            overlaps, new_base_interval = merge_if_overlaps(base_interval, interval)
            if not overlaps:
                gaps.append(DatetimeInterval(base_interval.end, interval.start))
            base_interval = new_base_interval
        if base_interval.end < end:
            gaps.append(DatetimeInterval(base_interval.end, None))
    return gaps


def merge_if_overlaps(a: DatetimeInterval, b: DatetimeInterval):
    if a.end >= b.end:
        return True, DatetimeInterval(a.start, a.end)
    if b.start - a.end < datetime.timedelta(minutes=1):
        return True, DatetimeInterval(a.start, b.end)
    else:
        return False, DatetimeInterval(b.start, b.end)


def start_end_with_respect_to_all_day(event, calendar_tz):
    start, _ = ical_date_to_datetime(event[ICAL_DATETIME_START].dt, calendar_tz, start=True)
    end, _ = ical_date_to_datetime(event[ICAL_DATETIME_END].dt, calendar_tz, start=False)
    return start, end


def event_start_end_all_day_with_respect_to_type(event, calendar_tz):
    all_day = False
    if type(event[ICAL_DATETIME_START].dt) == datetime.date:
        start, end = start_end_with_respect_to_all_day(event, calendar_tz)
        all_day = True
    else:
        start, end = ical_events.get_start_and_end_with_respect_to_event_type(event)
    return start, end, all_day


def convert_windows_timezone_to_iana(tz_name):
    """
    Conversion info taken from https://raw.githubusercontent.com/unicode-org/cldr/main/common/supplemental/windowsZones.xml
    Also see https://gist.github.com/mrled/8d29fde758cfc7dd0b52f3bbf2b8f06e
    NOTE: This mapping could be updated, and it's technically a guess.
    Also, there could probably be issues with DST for some timezones.
    """
    windows_to_iana_map = {
        "AUS Central Standard Time": "Australia/Darwin",
        "AUS Eastern Standard Time": "Australia/Sydney",
        "Afghanistan Standard Time": "Asia/Kabul",
        "Alaskan Standard Time": "America/Anchorage",
        "Aleutian Standard Time": "America/Adak",
        "Altai Standard Time": "Asia/Barnaul",
        "Arab Standard Time": "Asia/Riyadh",
        "Arabian Standard Time": "Asia/Dubai",
        "Arabic Standard Time": "Asia/Baghdad",
        "Argentina Standard Time": "America/Buenos_Aires",
        "Astrakhan Standard Time": "Europe/Astrakhan",
        "Atlantic Standard Time": "America/Halifax",
        "Aus Central W. Standard Time": "Australia/Eucla",
        "Azerbaijan Standard Time": "Asia/Baku",
        "Azores Standard Time": "Atlantic/Azores",
        "Bahia Standard Time": "America/Bahia",
        "Bangladesh Standard Time": "Asia/Dhaka",
        "Belarus Standard Time": "Europe/Minsk",
        "Bougainville Standard Time": "Pacific/Bougainville",
        "Canada Central Standard Time": "America/Regina",
        "Cape Verde Standard Time": "Atlantic/Cape_Verde",
        "Caucasus Standard Time": "Asia/Yerevan",
        "Cen. Australia Standard Time": "Australia/Adelaide",
        "Central America Standard Time": "America/Guatemala",
        "Central Asia Standard Time": "Asia/Almaty",
        "Central Brazilian Standard Time": "America/Cuiaba",
        "Central Europe Standard Time": "Europe/Budapest",
        "Central European Standard Time": "Europe/Warsaw",
        "Central Pacific Standard Time": "Pacific/Guadalcanal",
        "Central Standard Time": "America/Chicago",
        "Central Standard Time (Mexico)": "America/Mexico_City",
        "Chatham Islands Standard Time": "Pacific/Chatham",
        "China Standard Time": "Asia/Shanghai",
        "Cuba Standard Time": "America/Havana",
        "Dateline Standard Time": "Etc/GMT+12",
        "E. Africa Standard Time": "Africa/Nairobi",
        "E. Australia Standard Time": "Australia/Brisbane",
        "E. Europe Standard Time": "Europe/Chisinau",
        "E. South America Standard Time": "America/Sao_Paulo",
        "Easter Island Standard Time": "Pacific/Easter",
        "Eastern Standard Time": "America/New_York",
        "Eastern Standard Time (Mexico)": "America/Cancun",
        "Egypt Standard Time": "Africa/Cairo",
        "Ekaterinburg Standard Time": "Asia/Yekaterinburg",
        "FLE Standard Time": "Europe/Kiev",
        "Fiji Standard Time": "Pacific/Fiji",
        "GMT Standard Time": "Europe/London",
        "GTB Standard Time": "Europe/Bucharest",
        "Georgian Standard Time": "Asia/Tbilisi",
        "Greenland Standard Time": "America/Godthab",
        "Greenwich Standard Time": "Atlantic/Reykjavik",
        "Haiti Standard Time": "America/Port-au-Prince",
        "Hawaiian Standard Time": "Pacific/Honolulu",
        "India Standard Time": "Asia/Calcutta",
        "Iran Standard Time": "Asia/Tehran",
        "Israel Standard Time": "Asia/Jerusalem",
        "Jordan Standard Time": "Asia/Amman",
        "Kaliningrad Standard Time": "Europe/Kaliningrad",
        "Korea Standard Time": "Asia/Seoul",
        "Libya Standard Time": "Africa/Tripoli",
        "Line Islands Standard Time": "Pacific/Kiritimati",
        "Lord Howe Standard Time": "Australia/Lord_Howe",
        "Magadan Standard Time": "Asia/Magadan",
        "Magallanes Standard Time": "America/Punta_Arenas",
        "Marquesas Standard Time": "Pacific/Marquesas",
        "Mauritius Standard Time": "Indian/Mauritius",
        "Middle East Standard Time": "Asia/Beirut",
        "Montevideo Standard Time": "America/Montevideo",
        "Morocco Standard Time": "Africa/Casablanca",
        "Mountain Standard Time": "America/Denver",
        "Mountain Standard Time (Mexico)": "America/Chihuahua",
        "Myanmar Standard Time": "Asia/Rangoon",
        "N. Central Asia Standard Time": "Asia/Novosibirsk",
        "Namibia Standard Time": "Africa/Windhoek",
        "Nepal Standard Time": "Asia/Katmandu",
        "New Zealand Standard Time": "Pacific/Auckland",
        "Newfoundland Standard Time": "America/St_Johns",
        "Norfolk Standard Time": "Pacific/Norfolk",
        "North Asia East Standard Time": "Asia/Irkutsk",
        "North Asia Standard Time": "Asia/Krasnoyarsk",
        "North Korea Standard Time": "Asia/Pyongyang",
        "Omsk Standard Time": "Asia/Omsk",
        "Pacific SA Standard Time": "America/Santiago",
        "Pacific Standard Time": "America/Los_Angeles",
        "Pacific Standard Time (Mexico)": "America/Tijuana",
        "Pakistan Standard Time": "Asia/Karachi",
        "Paraguay Standard Time": "America/Asuncion",
        "Qyzylorda Standard Time": "Asia/Qyzylorda",
        "Romance Standard Time": "Europe/Paris",
        "Russia Time Zone 10": "Asia/Srednekolymsk",
        "Russia Time Zone 11": "Asia/Kamchatka",
        "Russia Time Zone 3": "Europe/Samara",
        "Russian Standard Time": "Europe/Moscow",
        "SA Eastern Standard Time": "America/Cayenne",
        "SA Pacific Standard Time": "America/Bogota",
        "SA Western Standard Time": "America/La_Paz",
        "SE Asia Standard Time": "Asia/Bangkok",
        "Saint Pierre Standard Time": "America/Miquelon",
        "Sakhalin Standard Time": "Asia/Sakhalin",
        "Samoa Standard Time": "Pacific/Apia",
        "Sao Tome Standard Time": "Africa/Sao_Tome",
        "Saratov Standard Time": "Europe/Saratov",
        "Singapore Standard Time": "Asia/Singapore",
        "South Africa Standard Time": "Africa/Johannesburg",
        "South Sudan Standard Time": "Africa/Juba",
        "Sri Lanka Standard Time": "Asia/Colombo",
        "Sudan Standard Time": "Africa/Khartoum",
        "Syria Standard Time": "Asia/Damascus",
        "Taipei Standard Time": "Asia/Taipei",
        "Tasmania Standard Time": "Australia/Hobart",
        "Tocantins Standard Time": "America/Araguaina",
        "Tokyo Standard Time": "Asia/Tokyo",
        "Tomsk Standard Time": "Asia/Tomsk",
        "Tonga Standard Time": "Pacific/Tongatapu",
        "Transbaikal Standard Time": "Asia/Chita",
        "Turkey Standard Time": "Europe/Istanbul",
        "Turks And Caicos Standard Time": "America/Grand_Turk",
        "US Eastern Standard Time": "America/Indianapolis",
        "US Mountain Standard Time": "America/Phoenix",
        "UTC": "Etc/UTC",
        "UTC+12": "Etc/GMT-12",
        "UTC+13": "Etc/GMT-13",
        "UTC-02": "Etc/GMT+2",
        "UTC-08": "Etc/GMT+8",
        "UTC-09": "Etc/GMT+9",
        "UTC-11": "Etc/GMT+11",
        "Ulaanbaatar Standard Time": "Asia/Ulaanbaatar",
        "Venezuela Standard Time": "America/Caracas",
        "Vladivostok Standard Time": "Asia/Vladivostok",
        "Volgograd Standard Time": "Europe/Volgograd",
        "W. Australia Standard Time": "Australia/Perth",
        "W. Central Africa Standard Time": "Africa/Lagos",
        "W. Europe Standard Time": "Europe/Berlin",
        "W. Mongolia Standard Time": "Asia/Hovd",
        "West Asia Standard Time": "Asia/Tashkent",
        "West Bank Standard Time": "Asia/Hebron",
        "West Pacific Standard Time": "Pacific/Port_Moresby",
        "Yakutsk Standard Time": "Asia/Yakutsk",
        "Yukon Standard Time": "America/Whitehorse",
    }

    result = windows_to_iana_map.get(tz_name)
    logger.debug("Converting the timezone from Windows to IANA. '{}' -> '{}'".format(tz_name, result))

    return result
