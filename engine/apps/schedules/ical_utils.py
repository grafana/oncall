from __future__ import annotations

import datetime
import logging
import re
import typing
from collections import namedtuple
from typing import TYPE_CHECKING

import pytz
import requests
from django.db.models import Q
from django.utils import timezone
from icalendar import Calendar
from icalendar import Event as IcalEvent

from apps.api.permissions import RBACPermission
from apps.schedules.constants import (
    CALENDAR_TYPE_FINAL,
    ICAL_ATTENDEE,
    ICAL_DATETIME_END,
    ICAL_DATETIME_START,
    ICAL_DESCRIPTION,
    ICAL_LOCATION,
    ICAL_PRIORITY,
    ICAL_RECURRENCE_ID,
    ICAL_SEQUENCE,
    ICAL_STATUS,
    ICAL_STATUS_CANCELLED,
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
    from apps.schedules.models.on_call_schedule import OnCallScheduleQuerySet
    from apps.user_management.models import Organization, User
    from apps.user_management.models.user import UserQuerySet

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


EmptyShift = namedtuple(
    "EmptyShift",
    ["start", "end", "summary", "description", "attendee", "all_day", "calendar_type", "calendar_tz", "shift_pk"],
)
EmptyShifts = typing.List[EmptyShift]

DatetimeInterval = namedtuple("DatetimeInterval", ["start", "end"])
DatetimeIntervals = typing.List[DatetimeInterval]

IcalEvents = typing.List[IcalEvent]


def users_in_ical(
    usernames_from_ical: typing.List[str],
    organization: "Organization",
) -> "UserQuerySet":
    """
    This method returns a sequence of `User` objects, filtered by users whose username, or case-insensitive e-mail,
    is present in `usernames_from_ical`. If `include_viewers` is set to `True`, users are further filtered down
    based on their granted permissions.

    Parameters
    ----------
    usernames_from_ical : typing.List[str]
        A list of usernames present in the ical feed
    organization : apps.user_management.models.organization.Organization
        The organization in question
    """
    from apps.user_management.models import User

    emails_from_ical = [username.lower() for username in usernames_from_ical]

    # users_found_in_ical = organization.users
    users_found_in_ical = organization.users.filter(
        **User.build_permissions_query(RBACPermission.Permissions.SCHEDULES_WRITE, organization)
    )

    users_found_in_ical = users_found_in_ical.filter(
        (Q(username__in=usernames_from_ical) | Q(email__lower__in=emails_from_ical))
    ).distinct()

    return users_found_in_ical


@timed_lru_cache(timeout=100)
def memoized_users_in_ical(usernames_from_ical: typing.List[str], organization: "Organization") -> UserQuerySet:
    # using in-memory cache instead of redis to avoid pickling python objects
    return users_in_ical(usernames_from_ical, organization)


# used for display schedule events on web
def list_of_oncall_shifts_from_ical(
    schedule: "OnCallSchedule",
    datetime_start: datetime.datetime,
    datetime_end: datetime.datetime,
    with_empty_shifts: bool = False,
    with_gaps: bool = False,
    filter_by: str | None = None,
    from_cached_final: bool = False,
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
    from apps.schedules.models import OnCallSchedule

    # get list of iCalendars from current iCal files. If there is more than one calendar, primary calendar will always
    # be the first
    calendars: typing.Tuple[typing.Optional[Calendar], ...]

    if from_cached_final:
        calendars = (Calendar.from_ical(schedule.cached_ical_final_schedule),)
    else:
        calendars = schedule.get_icalendars()

    result_datetime = []
    result_date = []

    for idx, calendar in enumerate(calendars):
        if calendar is not None:
            calendar_type: str | int

            if from_cached_final:
                calendar_type = CALENDAR_TYPE_FINAL
            elif idx == 0:
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

    def event_start_cmp_key(e):
        pytz_tz = pytz.timezone("UTC")
        return (
            datetime.datetime.combine(e["start"], datetime.datetime.min.time(), tzinfo=pytz_tz)
            if type(e["start"]) == datetime.date
            else e["start"]
        )

    result = sorted(result_datetime + result_date, key=event_start_cmp_key)
    # if there is no events, return None
    return result or None


def get_shifts_dict(
    calendar: Calendar,
    calendar_type: str | int,
    schedule: "OnCallSchedule",
    datetime_start: datetime.datetime,
    datetime_end: datetime.datetime,
    with_empty_shifts: bool = False,
):
    events = ical_events.get_events_from_ical_between(calendar, datetime_start, datetime_end)
    result_datetime = []
    result_date = []
    for event in events:
        status = event.get(ICAL_STATUS)
        if status == ICAL_STATUS_CANCELLED:
            # ignore cancelled events
            continue
        sequence = event.get(ICAL_SEQUENCE)
        recurrence_id = event.get(ICAL_RECURRENCE_ID)
        if recurrence_id:
            recurrence_id = recurrence_id.dt.isoformat()
        priority = parse_priority_from_string(event.get(ICAL_SUMMARY, "[L0]"))
        pk, source = parse_event_uid(event.get(ICAL_UID), sequence=sequence, recurrence_id=recurrence_id)
        users = get_users_from_ical_event(event, schedule.organization)
        missing_users = get_missing_users_from_ical_event(event, schedule.organization)
        event_calendar_type = calendar_type
        if calendar_type == CALENDAR_TYPE_FINAL:
            event_calendar_type = (
                schedule.OVERRIDES
                if (
                    event.get(ICAL_PRIORITY, "") == schedule.OVERRIDES
                    or
                    # keep for backwards compatibility (to be removed later once schedules are refreshed)
                    event.get(ICAL_LOCATION, "") == schedule.CALENDAR_TYPE_VERBAL[schedule.OVERRIDES]
                )
                else schedule.PRIMARY
            )
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
                        "calendar_type": event_calendar_type,
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
                            "calendar_type": event_calendar_type,
                            "shift_pk": pk,
                        }
                    )
    return result_datetime, result_date


def list_of_empty_shifts_in_schedule(
    schedule: "OnCallSchedule", start_date: datetime.date, end_date: datetime.date
) -> EmptyShifts:
    # Calculate lookup window in schedule's tz
    # If we can't get tz from ical use UTC
    from apps.schedules.models import OnCallSchedule

    calendars = schedule.get_icalendars()
    empty_shifts: EmptyShifts = []
    for idx, calendar in enumerate(calendars):
        if calendar is not None:
            if idx == 0:
                calendar_type = OnCallSchedule.PRIMARY
            else:
                calendar_type = OnCallSchedule.OVERRIDES

            calendar_tz = get_icalendar_tz_or_utc(calendar)

            # utcoffset can technically return None, but we're confident it is a timedelta here
            schedule_timezone_offset: datetime.timedelta = datetime.datetime.now().astimezone(calendar_tz).utcoffset()  # type: ignore[assignment]

            start_datetime = datetime.datetime.combine(start_date, datetime.time.min) + datetime.timedelta(
                milliseconds=1
            )
            start_datetime_with_offset = (start_datetime - schedule_timezone_offset).astimezone(pytz.UTC)
            end_datetime = datetime.datetime.combine(end_date, datetime.time.max)
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
    schedule: "OnCallSchedule",
    events_datetime: typing.Optional[datetime.datetime] = None,
) -> typing.Sequence["User"]:
    """
    Retrieve on-call users for the current time
    """
    events_datetime = events_datetime if events_datetime else datetime.datetime.now(timezone.utc)
    return list_users_to_notify_from_ical_for_period(
        schedule,
        events_datetime,
        events_datetime,
    )


def list_users_to_notify_from_ical_for_period(
    schedule: "OnCallSchedule",
    start_datetime: datetime.datetime,
    end_datetime: datetime.datetime,
) -> UserQuerySet:
    users_found_in_ical: typing.Sequence["User"] = []
    events = schedule.final_events(start_datetime, end_datetime)
    usernames = []
    for event in events:
        usernames += [u["email"] for u in event.get("users", [])]

    users_found_in_ical = users_in_ical(usernames, schedule.organization)
    return users_found_in_ical


def get_oncall_users_for_multiple_schedules(
    schedules: "OnCallScheduleQuerySet", events_datetime=None
) -> typing.Dict["OnCallSchedule", UserQuerySet]:
    if events_datetime is None:
        events_datetime = datetime.datetime.now(timezone.utc)

    # Exit early if there are no schedules
    if not schedules.exists():
        return {}

    # Get on-call users
    oncall_users = {}
    for schedule in schedules.all():
        # pass user list to list_users_to_notify_from_ical
        schedule_oncall_users = list_users_to_notify_from_ical(schedule, events_datetime=events_datetime)
        oncall_users.update({schedule.pk: schedule_oncall_users})

    return oncall_users


def parse_username_from_string(string: str) -> str:
    """
    Parse on-call shift user from the given string
    Example input:
    [L1] bob@company.com
    Example output:
    bob@company.com
    """
    return re.sub(RE_PRIORITY, "", string.strip(), 1).strip()


def parse_priority_from_string(string: str) -> int:
    """
    Parse on-call shift priority from the given string
    Example input:
    [L1] @alex @bob
    Example output:
    1
    """
    priority = 0
    priority_matches = re.findall(RE_PRIORITY, string.strip())
    if len(priority_matches) > 0:
        priority = int(priority_matches[0])
        if priority < 1:
            priority = 0
    return priority


def parse_event_uid(string: str, sequence: str = None, recurrence_id: str = None):
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
            # in ical imported calendars, sequence and/or recurrence_id
            # distinguish main recurring event vs instance modification
            # (see https://icalendar.org/iCalendar-RFC-5545/3-8-4-4-recurrence-id.html)
            if sequence:
                pk = f"{pk}_{sequence}"
            if recurrence_id:
                pk = f"{pk}_{recurrence_id}"

    if source is not None:
        source = int(source)
        from apps.schedules.models import CustomOnCallShift

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


def get_missing_users_from_ical_event(event, organization: "Organization"):
    all_usernames, _ = get_usernames_from_ical_event(event)
    users = list(get_users_from_ical_event(event, organization))
    found_usernames = [u.username for u in users]
    found_emails = [u.email.lower() for u in users]
    return [u for u in all_usernames if u != "" and u not in found_usernames and u.lower() not in found_emails]


def get_users_from_ical_event(event, organization: "Organization") -> typing.Sequence["User"]:
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
        # only consider VEVENT components
        first_cal_events = {
            cmp.get("UID", None): cmp.get("SEQUENCE", None) for cmp in first_subcomponents if cmp.name == "VEVENT"
        }
        second_cal_events = {
            cmp.get("UID", None): cmp.get("SEQUENCE", None) for cmp in second_subcomponents if cmp.name == "VEVENT"
        }
        # check events and their respective sequences are equal
        return first_cal_events == second_cal_events


def ical_date_to_datetime(date, tz, start):
    datetime_to_combine = datetime.time.min
    all_day = False
    if type(date) == datetime.date:
        all_day = True
        calendar_timezone_offset = datetime.datetime.now().astimezone(tz).utcoffset()
        date = datetime.datetime.combine(date, datetime_to_combine).astimezone(tz) - calendar_timezone_offset
        if not start:
            date -= datetime.timedelta(seconds=1)
    return date, all_day


def calculate_shift_diff(shifts: list, prev_shifts: list) -> typing.Tuple[bool, list]:
    """
    Get shifts diff comparing with the previous shifts
    """
    fields_to_compare = ["users", "end", "start", "all_day", "priority_level", "shift"]

    shifts_fields = [{k: v for k, v in shift.items() if k in fields_to_compare} for shift in shifts]
    prev_shifts_fields = [{k: v for k, v in shift.items() if k in fields_to_compare} for shift in prev_shifts]

    shift_changed = len(shifts) != len(prev_shifts)

    diff = []

    for idx, shift in enumerate(shifts_fields):
        if shift not in prev_shifts_fields:
            shift_changed = True
            diff.append(shifts[idx])

    return shift_changed, diff


def get_icalendar_tz_or_utc(icalendar):
    calendar_timezone = icalendar.get("X-WR-TIMEZONE", "UTC")

    if pytz_timezone := is_valid_timezone(calendar_timezone):
        return pytz_timezone

    # try to convert the timezone from windows to iana
    if (converted_timezone := convert_windows_timezone_to_iana(calendar_timezone)) is None:
        return "UTC"

    return pytz.timezone(converted_timezone)


def fetch_ical_file_or_get_error(ical_url: str) -> typing.Tuple[str | None, str | None]:
    cached_ical_file: str | None = None
    ical_file_error: str | None = None
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


def fetch_ical_file(ical_url: str) -> str:
    # without user-agent header google calendar sometimes returns text/html instead of text/calendar
    headers = {"User-Agent": "Grafana OnCall"}
    r = requests.get(ical_url, headers=headers, timeout=10)
    logger.info(f"fetch_ical_file: content-type={r.headers.get('Content-Type')}")
    return r.text


def create_base_icalendar(name: str) -> Calendar:
    cal = Calendar()
    cal.add("calscale", "GREGORIAN")
    cal.add("x-wr-calname", name)
    cal.add("x-wr-timezone", "UTC")
    cal.add("version", "2.0")
    cal.add("prodid", "//Grafana Labs//Grafana On-Call//")
    # suggested minimum interval for polling for changes
    cal.add("REFRESH-INTERVAL;VALUE=DURATION", "P1H")

    return cal


def get_user_events_from_calendars(
    ical_obj: Calendar, calendar: Calendar, user: User, name: typing.Optional[str] = None
) -> None:
    if calendar:
        for component in calendar.walk():
            if component.name == "VEVENT":
                event_user = get_usernames_from_ical_event(component)
                event_user_value = event_user[0][0]
                if event_user_value == user.username or event_user_value.lower() == user.email.lower():
                    if name:
                        component["SUMMARY"] = "{}: {}".format(name, component["SUMMARY"])
                    ical_obj.add_component(component)


def _get_ical_data_final_schedule(schedule: "OnCallSchedule") -> str | None:
    ical_data = schedule.cached_ical_final_schedule
    if ical_data is None:
        schedule.refresh_ical_final_schedule()
        # casting is safe here. cached_ical_final_schedule is updated inside of refresh_ical_final_schedule
        return typing.cast(str, schedule.cached_ical_final_schedule)
    return ical_data


def ical_export_from_schedule(schedule: "OnCallSchedule") -> bytes:
    ical_data = _get_ical_data_final_schedule(schedule)
    return ical_data.encode()


def user_ical_export(user: "User", schedules: "OnCallScheduleQuerySet") -> bytes:
    schedule_name = "On-Call Schedule for {0}".format(user.username)
    ical_obj = create_base_icalendar(schedule_name)

    for schedule in schedules:
        name = schedule.name
        ical_data = _get_ical_data_final_schedule(schedule)
        get_user_events_from_calendars(ical_obj, Calendar.from_ical(ical_data), user, name=name)

    return ical_obj.to_ical()


def detect_gaps(intervals: DatetimeIntervals, start: datetime.datetime, end: datetime.datetime) -> DatetimeIntervals:
    gaps: DatetimeIntervals = []
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


def merge_if_overlaps(a: DatetimeInterval, b: DatetimeInterval) -> typing.Tuple[bool, DatetimeInterval]:
    if a.end >= b.end:
        return True, DatetimeInterval(a.start, a.end)
    if b.start - a.end < datetime.timedelta(minutes=1):
        return True, DatetimeInterval(a.start, b.end)
    else:
        return False, DatetimeInterval(b.start, b.end)


def start_end_with_respect_to_all_day(event: IcalEvent, calendar_tz):
    start, _ = ical_date_to_datetime(event[ICAL_DATETIME_START].dt, calendar_tz, start=True)
    end, _ = ical_date_to_datetime(event[ICAL_DATETIME_END].dt, calendar_tz, start=False)
    return start, end


def event_start_end_all_day_with_respect_to_type(event: IcalEvent, calendar_tz):
    all_day = False
    if type(event[ICAL_DATETIME_START].dt) == datetime.date:
        start, end = start_end_with_respect_to_all_day(event, calendar_tz)
        all_day = True
    else:
        start, end = ical_events.get_start_and_end_with_respect_to_event_type(event)
    return start, end, all_day


def convert_windows_timezone_to_iana(tz_name: str) -> str | None:
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
