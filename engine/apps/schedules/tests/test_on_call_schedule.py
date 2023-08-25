import datetime
import textwrap
from unittest.mock import patch

import icalendar
import pytest
import pytz
from django.utils import timezone

from apps.api.permissions import LegacyAccessControlRole
from apps.schedules.constants import (
    ICAL_COMPONENT_VEVENT,
    ICAL_DATETIME_END,
    ICAL_DATETIME_START,
    ICAL_LAST_MODIFIED,
    ICAL_PRIORITY,
    ICAL_STATUS,
    ICAL_STATUS_CANCELLED,
    ICAL_SUMMARY,
)
from apps.schedules.ical_utils import memoized_users_in_ical
from apps.schedules.models import (
    CustomOnCallShift,
    OnCallSchedule,
    OnCallScheduleCalendar,
    OnCallScheduleICal,
    OnCallScheduleWeb,
)


@pytest.mark.django_db
def test_filter_events(make_organization, make_user_for_organization, make_schedule, make_on_call_shift):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )
    user = make_user_for_organization(organization)
    viewer = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    data = {
        "start": start_date + timezone.timedelta(days=1, hours=10),
        "rotation_start": start_date + timezone.timedelta(days=1, hours=10),
        "duration": timezone.timedelta(hours=4),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    # add empty shift
    data = {
        "start": start_date + timezone.timedelta(days=1, hours=20),
        "rotation_start": start_date + timezone.timedelta(days=1, hours=20),
        "duration": timezone.timedelta(hours=2),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_WEEKLY,
        "schedule": schedule,
    }
    empty_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    empty_shift.add_rolling_users([[viewer]])

    # override: 22-23
    override_data = {
        "start": start_date + timezone.timedelta(hours=22),
        "rotation_start": start_date + timezone.timedelta(hours=22),
        "duration": timezone.timedelta(hours=1),
        "schedule": schedule,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[user]])

    # filter primary non-empty shifts only
    end_date = start_date + timezone.timedelta(days=3)
    events = schedule.filter_events(start_date, end_date, filter_by=OnCallSchedule.TYPE_ICAL_PRIMARY)
    expected = [
        {
            "calendar_type": OnCallSchedule.TYPE_ICAL_PRIMARY,
            "start": on_call_shift.start + timezone.timedelta(days=i),
            "end": on_call_shift.start + timezone.timedelta(days=i) + on_call_shift.duration,
            "all_day": False,
            "is_override": False,
            "is_empty": False,
            "is_gap": False,
            "priority_level": on_call_shift.priority_level,
            "missing_users": [],
            "users": [
                {
                    "display_name": user.username,
                    "pk": user.public_primary_key,
                    "email": user.email,
                    "avatar_full": user.avatar_full_url,
                },
            ],
            "shift": {"pk": on_call_shift.public_primary_key},
            "source": "api",
        }
        for i in range(2)
    ]
    assert events == expected

    # filter overrides only
    end_date = start_date + timezone.timedelta(days=3)
    events = schedule.filter_events(start_date, end_date, filter_by=OnCallSchedule.TYPE_ICAL_OVERRIDES)
    expected_override = [
        {
            "calendar_type": OnCallSchedule.TYPE_ICAL_OVERRIDES,
            "start": override.start,
            "end": override.start + override.duration,
            "all_day": False,
            "is_override": True,
            "is_empty": False,
            "is_gap": False,
            "priority_level": None,
            "missing_users": [],
            "users": [
                {
                    "display_name": user.username,
                    "pk": user.public_primary_key,
                    "email": user.email,
                    "avatar_full": user.avatar_full_url,
                },
            ],
            "shift": {"pk": override.public_primary_key},
            "source": "api",
        }
    ]
    assert events == expected_override

    # no type filter
    end_date = start_date + timezone.timedelta(days=3)
    events = schedule.filter_events(start_date, end_date)
    assert events == expected_override + expected


@pytest.mark.django_db
def test_filter_events_include_gaps(make_organization, make_user_for_organization, make_schedule, make_on_call_shift):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )
    user = make_user_for_organization(organization)
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    data = {
        "start": start_date + timezone.timedelta(hours=10),
        "rotation_start": start_date + timezone.timedelta(hours=10),
        "duration": timezone.timedelta(hours=8),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    end_date = start_date + timezone.timedelta(days=1)
    events = schedule.filter_events(start_date, end_date, filter_by=OnCallSchedule.TYPE_ICAL_PRIMARY, with_gap=True)
    expected = [
        {
            "calendar_type": None,
            "start": start_date,
            "end": on_call_shift.start,
            "all_day": False,
            "is_override": False,
            "is_empty": False,
            "is_gap": True,
            "priority_level": None,
            "missing_users": [],
            "users": [],
            "shift": {"pk": None},
            "source": None,
        },
        {
            "calendar_type": OnCallSchedule.TYPE_ICAL_PRIMARY,
            "start": on_call_shift.start,
            "end": on_call_shift.start + on_call_shift.duration,
            "all_day": False,
            "is_override": False,
            "is_empty": False,
            "is_gap": False,
            "priority_level": on_call_shift.priority_level,
            "missing_users": [],
            "users": [
                {
                    "display_name": user.username,
                    "pk": user.public_primary_key,
                    "email": user.email,
                    "avatar_full": user.avatar_full_url,
                },
            ],
            "shift": {"pk": on_call_shift.public_primary_key},
            "source": "api",
        },
        {
            "calendar_type": None,
            "start": on_call_shift.start + on_call_shift.duration,
            "end": on_call_shift.start + timezone.timedelta(hours=14),
            "all_day": False,
            "is_override": False,
            "is_empty": False,
            "is_gap": True,
            "priority_level": None,
            "missing_users": [],
            "users": [],
            "shift": {"pk": None},
            "source": None,
        },
    ]
    assert events == expected


@pytest.mark.django_db
def test_filter_events_include_empty(make_organization, make_user_for_organization, make_schedule, make_on_call_shift):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )
    user = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    data = {
        "start": start_date + timezone.timedelta(hours=10),
        "rotation_start": start_date + timezone.timedelta(hours=10),
        "duration": timezone.timedelta(hours=8),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    end_date = start_date + timezone.timedelta(days=1)
    events = schedule.filter_events(start_date, end_date, filter_by=OnCallSchedule.TYPE_ICAL_PRIMARY, with_empty=True)
    expected = [
        {
            "calendar_type": OnCallSchedule.TYPE_ICAL_PRIMARY,
            "start": on_call_shift.start,
            "end": on_call_shift.start + on_call_shift.duration,
            "all_day": False,
            "is_override": False,
            "is_empty": True,
            "is_gap": False,
            "priority_level": on_call_shift.priority_level,
            "missing_users": [user.username],
            "users": [],
            "shift": {"pk": on_call_shift.public_primary_key},
            "source": "api",
        }
    ]
    assert events == expected


@pytest.mark.django_db
def test_filter_events_ical_all_day(make_organization, make_user_for_organization, make_schedule, get_ical):
    calendar = get_ical("calendar_with_all_day_event.ics")
    organization = make_organization()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    schedule.cached_ical_file_primary = calendar.to_ical()
    for u in ("@Bernard Desruisseaux", "@Bob", "@Alex", "@Alice"):
        make_user_for_organization(organization, username=u)
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    day_to_check_iso = "2021-01-27T15:27:14.448059+00:00"
    parsed_iso_day_to_check = datetime.datetime.fromisoformat(day_to_check_iso).replace(tzinfo=pytz.UTC)
    datetime_start = parsed_iso_day_to_check - timezone.timedelta(days=1)
    datetime_end = datetime_start + datetime.timedelta(days=1, hours=23, minutes=59, seconds=59)

    events = schedule.final_events(datetime_start, datetime_end)
    expected_events = [
        # all_day, users, start, end
        (
            False,
            ["@Bernard Desruisseaux"],
            datetime.datetime(2021, 1, 26, 8, 0, tzinfo=pytz.UTC),
            datetime.datetime(2021, 1, 26, 17, 0, tzinfo=pytz.UTC),
        ),
        (
            True,
            ["@Alex"],
            datetime.datetime(2021, 1, 27, 0, 0, tzinfo=pytz.UTC),
            datetime.datetime(2021, 1, 27, 23, 59, 59, tzinfo=pytz.UTC),
        ),
        (
            True,
            ["@Alice"],
            datetime.datetime(2021, 1, 27, 0, 0, tzinfo=pytz.UTC),
            datetime.datetime(2021, 1, 28, 23, 59, 59, tzinfo=pytz.UTC),
        ),
        (
            False,
            ["@Bob"],
            datetime.datetime(2021, 1, 27, 8, 0, tzinfo=pytz.UTC),
            datetime.datetime(2021, 1, 27, 17, 0, tzinfo=pytz.UTC),
        ),
        (
            False,
            ["@Bernard Desruisseaux"],
            datetime.datetime(2021, 1, 28, 8, 0, tzinfo=pytz.UTC),
            datetime.datetime(2021, 1, 28, 17, 0, tzinfo=pytz.UTC),
        ),
    ]
    expected = [
        {"all_day": all_day, "users": users, "start": start, "end": end}
        for all_day, users, start, end in expected_events
    ]
    returned = [
        {
            "all_day": e["all_day"],
            "users": [u["display_name"] for u in e["users"]],
            "start": e["start"],
            "end": e["end"],
        }
        for e in events
    ]
    assert returned == expected


@pytest.mark.django_db
def test_final_schedule_events(make_organization, make_user_for_organization, make_on_call_shift, make_schedule):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    user_a, user_b, user_c, user_d, user_e = (make_user_for_organization(organization, username=i) for i in "ABCDE")
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    shifts = (
        # user, priority, start time (h), duration (hs)
        (user_a, 1, 10, 5),  # r1-1: 10-15 / A
        (user_b, 1, 11, 2),  # r1-2: 11-13 / B
        (user_a, 1, 16, 3),  # r1-3: 16-19 / A
        (user_a, 1, 21, 1),  # r1-4: 21-22 / A
        (user_b, 1, 22, 2),  # r1-5: 22-00 / B
        (user_c, 2, 12, 2),  # r2-1: 12-14 / C
        (user_d, 2, 14, 1),  # r2-2: 14-15 / D
        (user_d, 2, 17, 1),  # r2-3: 17-18 / D
        (user_d, 2, 20, 3),  # r2-4: 20-23 / D
    )
    for user, priority, start_h, duration in shifts:
        data = {
            "start": start_date + timezone.timedelta(hours=start_h),
            "rotation_start": start_date + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(hours=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

    overrides = (
        # user, priority, start time (h), duration (hs)
        (user_e, 0, 22, 1),  # 22-23 / E
        (user_a, 1, 22, 0.5),  # 22-22:30 / A
    )
    for user, priority, start_h, duration in overrides:
        data = {
            "start": start_date + timezone.timedelta(hours=start_h),
            "rotation_start": start_date + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(hours=duration),
            "priority_level": priority,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **data
        )
        on_call_shift.add_rolling_users([[user]])

    datetime_end = start_date + timezone.timedelta(days=1)
    returned_events = schedule.final_events(start_date, datetime_end)

    expected = (
        # start (h), duration (H), user, priority, is_gap, is_override
        (0, 10, None, None, True, False),  # 0-10 gap
        (10, 2, "A", 1, False, False),  # 10-12 A
        (11, 1, "B", 1, False, False),  # 11-12 B
        (12, 2, "C", 2, False, False),  # 12-14 C
        (14, 1, "D", 2, False, False),  # 14-15 D
        (15, 1, None, None, True, False),  # 15-16 gap
        (16, 1, "A", 1, False, False),  # 16-17 A
        (17, 1, "D", 2, False, False),  # 17-18 D
        (18, 1, "A", 1, False, False),  # 18-19 A
        (19, 1, None, None, True, False),  # 19-20 gap
        (20, 2, "D", 2, False, False),  # 20-22 D
        (22, 0.5, "A", 1, False, True),  # 22-22:30 A (override the override)
        (22.5, 0.5, "E", None, False, True),  # 22:30-23 E (override)
        (23, 1, "B", 1, False, False),  # 23-00 B
    )
    expected_events = [
        {
            "calendar_type": 1 if is_override else None if is_gap else 0,
            "end": start_date + timezone.timedelta(hours=start + duration),
            "is_gap": is_gap,
            "is_override": is_override,
            "priority_level": priority,
            "start": start_date + timezone.timedelta(hours=start),
            "user": user,
        }
        for start, duration, user, priority, is_gap, is_override in expected
    ]
    returned_events = [
        {
            "calendar_type": e["calendar_type"],
            "end": e["end"],
            "is_gap": e["is_gap"],
            "is_override": e["is_override"],
            "priority_level": e["priority_level"],
            "start": e["start"],
            "user": e["users"][0]["display_name"] if e["users"] else None,
        }
        for e in returned_events
    ]
    assert returned_events == expected_events


@pytest.mark.django_db
def test_final_schedule_override_no_priority_shift(
    make_organization, make_user_for_organization, make_on_call_shift, make_schedule
):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    user_a, user_b = (make_user_for_organization(organization, username=i) for i in "AB")
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    shifts = (
        # user, priority, start time (h), duration (hs)
        (user_a, 0, 10, 5),  # 10-15 / A
    )
    for user, priority, start_h, duration in shifts:
        data = {
            "start": start_date + timezone.timedelta(hours=start_h),
            "rotation_start": start_date + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(hours=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

    # override: 10-15 / B
    override_data = {
        "start": start_date + timezone.timedelta(hours=10),
        "rotation_start": start_date + timezone.timedelta(hours=5),
        "duration": timezone.timedelta(hours=5),
        "schedule": schedule,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[user_b]])

    datetime_end = start_date + timezone.timedelta(days=1)
    returned_events = schedule.final_events(start_date, datetime_end)

    expected = (
        # start (h), duration (H), user, priority, is_override
        (10, 5, "B", None, True),  # 10-15 B
    )
    expected_events = [
        {
            "calendar_type": 1 if is_override else 0,
            "end": start_date + timezone.timedelta(hours=start + duration),
            "is_override": is_override,
            "priority_level": priority,
            "start": start_date + timezone.timedelta(hours=start, milliseconds=1 if start == 0 else 0),
            "user": user,
        }
        for start, duration, user, priority, is_override in expected
    ]
    returned_events = [
        {
            "calendar_type": e["calendar_type"],
            "end": e["end"],
            "is_override": e["is_override"],
            "priority_level": e["priority_level"],
            "start": e["start"],
            "user": e["users"][0]["display_name"] if e["users"] else None,
        }
        for e in returned_events
        if not e["is_gap"]
    ]
    assert returned_events == expected_events


@pytest.mark.django_db
def test_final_schedule_override_split(
    make_organization, make_user_for_organization, make_on_call_shift, make_schedule
):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    user_a, user_b = (make_user_for_organization(organization, username=i) for i in "AB")
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    shifts = (
        # user, priority, start time (h), duration (hs)
        (user_a, 0, 10, 5),  # 10-15 / A
    )
    for user, priority, start_h, duration in shifts:
        data = {
            "start": start_date + timezone.timedelta(hours=start_h),
            "rotation_start": start_date + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(hours=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

    # override: 10-14 / B
    override_start = start_date + timezone.timedelta(hours=10)
    override_data = {
        "start": override_start,
        "rotation_start": override_start,
        "duration": timezone.timedelta(hours=4),
        "schedule": schedule,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[user_b]])

    override_started = override_start + timezone.timedelta(seconds=1)
    returned_events = schedule.final_events(override_started, override_started)

    expected = (
        # start (h), duration (H), user, priority, is_override
        (10, 4, "B", None, True),  # 10-14 B
    )
    expected_events = [
        {
            "calendar_type": 1 if is_override else 0,
            "end": start_date + timezone.timedelta(hours=start + duration),
            "is_override": is_override,
            "priority_level": priority,
            "start": start_date + timezone.timedelta(hours=start, milliseconds=1 if start == 0 else 0),
            "user": user,
        }
        for start, duration, user, priority, is_override in expected
    ]
    returned_events = [
        {
            "calendar_type": e["calendar_type"],
            "end": e["end"],
            "is_override": e["is_override"],
            "priority_level": e["priority_level"],
            "start": e["start"],
            "user": e["users"][0]["display_name"] if e["users"] else None,
        }
        for e in returned_events
        if not e["is_gap"]
    ]
    assert returned_events == expected_events


@pytest.mark.django_db
def test_final_schedule_splitting_events(
    make_organization, make_user_for_organization, make_on_call_shift, make_schedule
):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    user_a, user_b, user_c = (make_user_for_organization(organization, username=i) for i in "ABC")
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    shifts = (
        # user, priority, start time (h), duration (hs)
        (user_a, 1, 10, 10),  # r1-1: 10-20 / A
        (user_b, 1, 12, 4),  # r1-2: 12-16 / B
        (user_c, 2, 15, 3),  # r2-1: 15-18 / C
    )
    for user, priority, start_h, duration in shifts:
        data = {
            "start": start_date + timezone.timedelta(hours=start_h),
            "rotation_start": start_date + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(hours=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

    datetime_end = start_date + timezone.timedelta(days=1)
    returned_events = schedule.final_events(start_date, datetime_end)

    expected = (
        # start (h), duration (H), user, priority
        (10, 5, "A", 1),  # 10-15 A
        (12, 3, "B", 1),  # 12-15 B
        (15, 3, "C", 2),  # 15-18 C
        (18, 2, "A", 1),  # 18-20 A
    )
    expected_events = [
        {
            "end": start_date + timezone.timedelta(hours=start + duration),
            "priority_level": priority,
            "start": start_date + timezone.timedelta(hours=start),
            "user": user,
        }
        for start, duration, user, priority in expected
    ]
    returned_events = [
        {
            "end": e["end"],
            "priority_level": e["priority_level"],
            "start": e["start"],
            "user": e["users"][0]["display_name"] if e["users"] else None,
        }
        for e in returned_events
        if not e["is_gap"]
    ]
    assert returned_events == expected_events


@pytest.mark.django_db
def test_final_schedule_splitting_same_time_events(
    make_organization, make_user_for_organization, make_on_call_shift, make_schedule
):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    user_a, user_b, user_c = (make_user_for_organization(organization, username=i) for i in "ABC")
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    shifts = (
        # user, priority, start time (h), duration (hs)
        (user_a, 1, 10, 10),  # r1-1: 10-20 / A
        (user_b, 1, 10, 10),  # r1-2: 10-20 / B
        (user_c, 2, 10, 3),  # r2-1: 10-13 / C
    )
    for user, priority, start_h, duration in shifts:
        data = {
            "start": start_date + timezone.timedelta(hours=start_h),
            "rotation_start": start_date + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(hours=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

    datetime_end = start_date + timezone.timedelta(days=1)
    returned_events = schedule.final_events(start_date, datetime_end)

    expected = (
        # start (h), duration (H), user, priority
        (10, 3, "C", 2),  # 10-13 C
        (13, 7, "A", 1),  # 13-20 A
        (13, 7, "B", 1),  # 13-20 B
    )
    expected_events = [
        {
            "end": start_date + timezone.timedelta(hours=start + duration),
            "priority_level": priority,
            "start": start_date + timezone.timedelta(hours=start),
            "user": user,
        }
        for start, duration, user, priority in expected
    ]
    returned_events = [
        {
            "end": e["end"],
            "priority_level": e["priority_level"],
            "start": e["start"],
            "user": e["users"][0]["display_name"] if e["users"] else None,
        }
        for e in sorted(
            returned_events, key=lambda e: (e["start"], e["users"][0]["display_name"] if e["users"] else None)
        )
        if not e["is_gap"]
    ]
    assert returned_events == expected_events


@pytest.mark.django_db
def test_preview_shift(make_organization, make_user_for_organization, make_schedule, make_on_call_shift):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    data = {
        "start": start_date + timezone.timedelta(hours=9),
        "rotation_start": start_date + timezone.timedelta(hours=9),
        "duration": timezone.timedelta(hours=9),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    schedule_primary_ical = schedule._ical_file_primary

    # proposed shift
    new_shift = CustomOnCallShift(
        type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        organization=organization,
        schedule=schedule,
        name="testing",
        start=start_date + timezone.timedelta(hours=12),
        rotation_start=start_date + timezone.timedelta(hours=12),
        duration=timezone.timedelta(seconds=3600),
        frequency=CustomOnCallShift.FREQUENCY_DAILY,
        priority_level=2,
        rolling_users=[{other_user.pk: other_user.public_primary_key}],
    )

    datetime_end = start_date + timezone.timedelta(days=1)
    rotation_events, final_events = schedule.preview_shift(new_shift, start_date, datetime_end)

    # check rotation events
    expected_rotation_events = [
        {
            "calendar_type": OnCallSchedule.TYPE_ICAL_PRIMARY,
            "start": new_shift.start,
            "end": new_shift.start + new_shift.duration,
            "all_day": False,
            "is_override": False,
            "is_empty": False,
            "is_gap": False,
            "priority_level": new_shift.priority_level,
            "missing_users": [],
            "users": [
                {
                    "display_name": other_user.username,
                    "pk": other_user.public_primary_key,
                    "email": other_user.email,
                    "avatar_full": other_user.avatar_full_url,
                },
            ],
            "shift": {"pk": new_shift.public_primary_key},
            "source": "api",
        }
    ]
    assert rotation_events == expected_rotation_events

    # check final schedule events
    expected = (
        # start (h), duration (H), user, priority
        (9, 3, user.username, 1),  # 9-12 user
        (12, 1, other_user.username, 2),  # 12-13 other_user
        (13, 5, user.username, 1),  # 13-18 C
    )
    expected_events = [
        {
            "end": start_date + timezone.timedelta(hours=start + duration),
            "priority_level": priority,
            "start": start_date + timezone.timedelta(hours=start, milliseconds=1 if start == 0 else 0),
            "user": user,
        }
        for start, duration, user, priority in expected
    ]
    returned_events = [
        {
            "end": e["end"],
            "priority_level": e["priority_level"],
            "start": e["start"],
            "user": e["users"][0]["display_name"] if e["users"] else None,
        }
        for e in final_events
        if not e["is_override"] and not e["is_gap"]
    ]
    assert returned_events == expected_events

    # final ical schedule didn't change
    assert schedule._ical_file_primary == schedule_primary_ical


@pytest.mark.django_db
def test_preview_shift_do_not_change_rotation_events(
    make_organization, make_user_for_organization, make_schedule, make_on_call_shift
):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    data = {
        "start": start_date + timezone.timedelta(hours=9),
        "rotation_start": start_date + timezone.timedelta(hours=9),
        "duration": timezone.timedelta(hours=9),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    data = {
        "start": start_date + timezone.timedelta(hours=12),
        "rotation_start": start_date + timezone.timedelta(hours=12),
        "duration": timezone.timedelta(seconds=3600),
        "priority_level": 2,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    other_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    other_shift.add_rolling_users([[other_user]])

    datetime_end = start_date + timezone.timedelta(days=1)
    rotation_events, final_events = schedule.preview_shift(on_call_shift, start_date, datetime_end)

    # check rotation events
    expected_rotation_events = [
        {
            "calendar_type": OnCallSchedule.TYPE_ICAL_PRIMARY,
            "start": on_call_shift.start,
            "end": on_call_shift.start + on_call_shift.duration,
            "all_day": False,
            "is_override": False,
            "is_empty": False,
            "is_gap": False,
            "priority_level": on_call_shift.priority_level,
            "missing_users": [],
            "users": [
                {
                    "display_name": user.username,
                    "pk": user.public_primary_key,
                    "email": user.email,
                    "avatar_full": user.avatar_full_url,
                },
            ],
            "shift": {"pk": on_call_shift.public_primary_key},
            "source": "api",
        }
    ]
    assert rotation_events == expected_rotation_events


@pytest.mark.django_db
def test_preview_shift_no_user(make_organization, make_user_for_organization, make_schedule, make_on_call_shift):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    schedule_primary_ical = schedule._ical_file_primary

    # proposed shift
    new_shift = CustomOnCallShift(
        type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        organization=organization,
        schedule=schedule,
        name="testing",
        start=start_date + timezone.timedelta(hours=12),
        rotation_start=start_date + timezone.timedelta(hours=12),
        duration=timezone.timedelta(seconds=3600),
        frequency=CustomOnCallShift.FREQUENCY_DAILY,
        priority_level=2,
        rolling_users=[],
    )

    datetime_end = start_date + timezone.timedelta(days=1)
    rotation_events, final_events = schedule.preview_shift(new_shift, start_date, datetime_end)

    # check rotation events
    expected_rotation_events = [
        {
            "calendar_type": OnCallSchedule.TYPE_ICAL_PRIMARY,
            "start": new_shift.start,
            "end": new_shift.start + new_shift.duration,
            "all_day": False,
            "is_override": False,
            "is_empty": True,
            "is_gap": False,
            "priority_level": None,
            "missing_users": [],
            "users": [],
            "shift": {"pk": new_shift.public_primary_key},
            "source": "api",
        }
    ]
    assert rotation_events == expected_rotation_events

    expected_events = []
    returned_events = [
        {
            "end": e["end"],
            "start": e["start"],
            "user": e["users"][0]["display_name"] if e["users"] else None,
            "is_empty": e["is_empty"],
        }
        for e in final_events
        if not e["is_override"] and not e["is_gap"]
    ]
    assert returned_events == expected_events

    # final ical schedule didn't change
    assert schedule._ical_file_primary == schedule_primary_ical


@pytest.mark.django_db
def test_preview_override_shift(make_organization, make_user_for_organization, make_schedule, make_on_call_shift):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    data = {
        "start": start_date + timezone.timedelta(hours=9),
        "rotation_start": start_date + timezone.timedelta(hours=9),
        "duration": timezone.timedelta(hours=9),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    schedule_overrides_ical = schedule._ical_file_overrides

    # proposed override
    new_shift = CustomOnCallShift(
        type=CustomOnCallShift.TYPE_OVERRIDE,
        organization=organization,
        schedule=schedule,
        name="testing",
        start=start_date + timezone.timedelta(hours=12),
        rotation_start=start_date + timezone.timedelta(hours=12),
        duration=timezone.timedelta(seconds=3600),
        rolling_users=[{other_user.pk: other_user.public_primary_key}],
    )

    datetime_end = start_date + timezone.timedelta(days=1)
    rotation_events, final_events = schedule.preview_shift(new_shift, start_date, datetime_end)

    # check rotation events
    expected_rotation_events = [
        {
            "calendar_type": OnCallSchedule.TYPE_ICAL_OVERRIDES,
            "start": new_shift.start,
            "end": new_shift.start + new_shift.duration,
            "all_day": False,
            "is_override": True,
            "is_empty": False,
            "is_gap": False,
            "priority_level": None,
            "missing_users": [],
            "users": [
                {
                    "display_name": other_user.username,
                    "pk": other_user.public_primary_key,
                    "email": other_user.email,
                    "avatar_full": other_user.avatar_full_url,
                },
            ],
            "shift": {"pk": new_shift.public_primary_key},
            "source": "api",
        }
    ]
    assert rotation_events == expected_rotation_events

    # check final schedule events
    expected = (
        # start (h), duration (H), user, priority, is_override
        (9, 3, user.username, 1, False),  # 9-12 user
        (12, 1, other_user.username, None, True),  # 12-13 other_user
        (13, 5, user.username, 1, False),  # 13-18 C
    )
    expected_events = [
        {
            "end": start_date + timezone.timedelta(hours=start + duration),
            "priority_level": priority,
            "start": start_date + timezone.timedelta(hours=start, milliseconds=1 if start == 0 else 0),
            "user": user,
            "is_override": is_override,
        }
        for start, duration, user, priority, is_override in expected
    ]
    returned_events = [
        {
            "end": e["end"],
            "priority_level": e["priority_level"],
            "start": e["start"],
            "user": e["users"][0]["display_name"] if e["users"] else None,
            "is_override": e["is_override"],
        }
        for e in final_events
        if not e["is_gap"]
    ]
    assert returned_events == expected_events

    # final ical schedule didn't change
    assert schedule._ical_file_overrides == schedule_overrides_ical


@pytest.mark.django_db
def test_schedule_related_users_empty_schedule(make_organization, make_schedule):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )
    schedule.refresh_ical_file()

    users = schedule.related_users()
    assert set(users) == set()


@pytest.mark.django_db
def test_schedule_related_users(make_organization, make_user_for_organization, make_on_call_shift, make_schedule):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    user_a, _, _, user_d, user_e = (make_user_for_organization(organization, username=i) for i in "ABCDE")
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    shifts = (
        # user, priority, start time (h), duration (hs)
        (user_a, 1, 10, 5),  # r1-1: 10-15 / A
        (user_d, 2, 20, 3),  # r2-4: 20-23 / D
    )
    for user, priority, start_h, duration in shifts:
        data = {
            "start": start_date + timezone.timedelta(hours=start_h),
            "rotation_start": start_date + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(hours=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

    # override: 22-23 / E
    override_data = {
        "start": start_date - timezone.timedelta(hours=22),
        "rotation_start": start_date - timezone.timedelta(hours=22),
        "duration": timezone.timedelta(hours=1),
        "schedule": schedule,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[user_e]])

    schedule.refresh_ical_file()
    schedule.refresh_from_db()

    users = schedule.related_users()
    assert set(users) == set([user_a, user_d, user_e])


@pytest.mark.django_db
def test_schedule_related_users_usernames(
    make_organization, make_user_for_organization, make_on_call_shift, make_schedule
):
    """
    Check different usernames, including those with special characters and uppercase letters
    """
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )

    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    # Check different usernames, including those with special characters and uppercase letters
    usernames = ["test", "test.test", "test.test@test.test", "TEST.TEST@TEST.TEST"]
    users = [make_user_for_organization(organization, username=u) for u in usernames]
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    for user in users:
        data = {
            "start": start_date,
            "rotation_start": start_date,
            "duration": timezone.timedelta(hours=1),
            "priority_level": 1,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

    schedule.refresh_ical_file()
    schedule.refresh_from_db()

    assert set(schedule.related_users()) == set(users)


@pytest.mark.django_db(transaction=True)
def test_filter_events_none_cache_unchanged(
    make_organization, make_user_for_organization, make_schedule, make_on_call_shift
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )
    start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # add shift
    data = {
        "start": start_date + timezone.timedelta(hours=36),
        "rotation_start": start_date + timezone.timedelta(hours=36),
        "duration": timezone.timedelta(hours=2),
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    # schedule is removed from db
    schedule.delete()

    end_date = start_date + timezone.timedelta(days=5)
    events = schedule.filter_events(start_date, end_date, filter_by=OnCallSchedule.TYPE_ICAL_PRIMARY)
    expected = []
    assert events == expected


@pytest.mark.django_db
def test_schedules_ical_shift_cache(make_organization, make_schedule):
    organization = make_organization()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

    # initial values are None
    assert schedule.cached_ical_file_primary is None
    assert schedule.cached_ical_file_overrides is None

    # accessing the properties will trigger a refresh of the ical files (both empty)
    assert schedule._ical_file_primary == ""
    assert schedule._ical_file_overrides == ""

    # after the refresh, cached values are updated
    # (not None means no need to refresh cached value)
    assert schedule.cached_ical_file_primary == ""
    assert schedule.cached_ical_file_overrides == ""

    # same for Terraform/API schedules
    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)

    # initial values is None
    assert schedule.cached_ical_file_primary is None

    # accessing the property will trigger a refresh of the ical file (empty)
    assert schedule._ical_file_primary == ""

    # after the refresh, cached value is updated
    # (not None means no need to refresh cached value)
    assert schedule.cached_ical_file_primary == ""


@pytest.mark.django_db
def test_api_schedule_use_overrides_from_url(make_organization, make_schedule, get_ical):
    ical_file = get_ical("calendar_with_recurring_event.ics")
    ical_data = ical_file.to_ical().decode("utf-8")
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
        ical_url_overrides="http://some-url",
    )
    assert schedule.enable_web_overrides is False

    with patch("apps.schedules.models.on_call_schedule.fetch_ical_file_or_get_error") as mock_fetch_ical:
        mock_fetch_ical.return_value = (ical_data, None)
        schedule.refresh_ical_file()

    schedule.refresh_from_db()
    assert schedule.cached_ical_file_overrides == ical_data


@pytest.mark.django_db
def test_api_schedule_use_overrides_from_db(
    make_organization, make_user_for_organization, make_schedule, make_on_call_shift
):
    organization = make_organization()
    user_1 = make_user_for_organization(organization)
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
        ical_url_overrides=None,
        enable_web_overrides=True,
    )
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    override = make_on_call_shift(
        organization=organization,
        shift_type=CustomOnCallShift.TYPE_OVERRIDE,
        priority_level=1,
        start=now,
        rotation_start=now,
        duration=timezone.timedelta(minutes=30),
        source=CustomOnCallShift.SOURCE_WEB,
        schedule=schedule,
    )
    override.add_rolling_users([[user_1]])

    schedule.refresh_ical_file()

    ical_event = override.convert_to_ical()
    assert ical_event in schedule.cached_ical_file_overrides


@pytest.mark.django_db
def test_api_schedule_overrides_from_db_use_own_tz(
    make_organization, make_user_for_organization, make_schedule, make_on_call_shift
):
    organization = make_organization()
    user_1 = make_user_for_organization(organization)
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
        ical_url_overrides=None,
        enable_web_overrides=True,
        time_zone="Etc/GMT-2",
    )
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    override = make_on_call_shift(
        organization=organization,
        shift_type=CustomOnCallShift.TYPE_OVERRIDE,
        priority_level=1,
        start=now,
        rotation_start=now,
        duration=timezone.timedelta(hours=12),
        source=CustomOnCallShift.SOURCE_WEB,
        schedule=schedule,
    )
    override.add_rolling_users([[user_1]])

    schedule.refresh_ical_file()

    ical_event = override.convert_to_ical()
    assert ical_event in schedule.cached_ical_file_overrides


@pytest.mark.django_db
def test_api_schedule_ignores_overrides_from_url(
    make_organization, make_user_for_organization, make_schedule, make_on_call_shift, get_ical
):
    ical_file = get_ical("calendar_with_recurring_event.ics")
    ical_data = ical_file.to_ical().decode("utf-8")
    organization = make_organization()
    user_1 = make_user_for_organization(organization)
    user_2 = make_user_for_organization(organization)
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
        ical_url_overrides="http://some-url",
        enable_web_overrides=True,
    )
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    override = make_on_call_shift(
        organization=organization,
        shift_type=CustomOnCallShift.TYPE_OVERRIDE,
        priority_level=1,
        start=now,
        rotation_start=now,
        duration=timezone.timedelta(minutes=30),
        source=CustomOnCallShift.SOURCE_WEB,
        schedule=schedule,
    )
    override.add_rolling_users([[user_1, user_2]])

    with patch("apps.schedules.models.on_call_schedule.fetch_ical_file_or_get_error") as mock_fetch_ical:
        mock_fetch_ical.return_value = (ical_data, None)
        schedule.refresh_ical_file()

    schedule.refresh_from_db()

    # events coming from ical file are not in the final ical file
    for component in ical_file.walk():
        if component.name == "VEVENT":
            assert component.to_ical().decode("utf-8") not in schedule.cached_ical_file_overrides
    # only the event coming from the override shift
    ical_event = override.convert_to_ical()
    assert ical_event in schedule.cached_ical_file_overrides


@pytest.mark.django_db
def test_api_schedule_preview_requires_override(make_organization, make_schedule, make_on_call_shift):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
    )
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    non_override_shift = make_on_call_shift(
        organization=organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        priority_level=1,
        start=now,
        rotation_start=now,
        duration=timezone.timedelta(minutes=30),
        source=CustomOnCallShift.SOURCE_WEB,
        schedule=schedule,
    )

    with pytest.raises(ValueError):
        datetime_end = now + timezone.timedelta(days=1)
        schedule.preview_shift(non_override_shift, now, datetime_end)


@pytest.mark.django_db
def test_polymorphic_delete_related(
    make_organization_with_slack_team_identity, make_team, make_schedule, make_slack_user_group
):
    """
    Check that deleting related objects works as expected given that OnCallSchedule is a polymorphic model, and
    django-polymorphic has a bug with on_delete not working correctly for FKs:
    https://github.com/django-polymorphic/django-polymorphic/issues/229#issuecomment-398434412.
    """
    organization, slack_team_identity = make_organization_with_slack_team_identity()

    team = make_team(organization)
    slack_user_group = make_slack_user_group(slack_team_identity)

    schedule_1 = make_schedule(organization, schedule_class=OnCallScheduleWeb, team=team, user_group=slack_user_group)
    schedule_2 = make_schedule(organization, schedule_class=OnCallScheduleICal, team=team, user_group=slack_user_group)

    # Check that deleting the team works as expected
    team.delete()
    schedule_1.refresh_from_db()
    schedule_2.refresh_from_db()
    assert schedule_1.team is None
    assert schedule_2.team is None

    # Check that deleting the user group works as expected
    slack_user_group.delete()
    schedule_1.refresh_from_db()
    schedule_2.refresh_from_db()
    assert schedule_1.user_group is None
    assert schedule_2.user_group is None

    # Check that deleting the organization works as expected
    organization.hard_delete()
    assert not OnCallSchedule.objects.exists()


@pytest.mark.django_db
def test_user_related_schedules(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    schedule1 = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    shifts = (
        # user, priority, start time (h), duration (seconds)
        (admin, 1, 0, (24 * 60 * 60) - 1),  # r1-1: 0-23:59:59
    )
    for user, priority, start_h, duration in shifts:
        data = {
            "start": today + timezone.timedelta(hours=start_h),
            "rotation_start": today + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(seconds=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule1,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])
    schedule1.refresh_ical_file()

    schedule2 = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    override_data = {
        "start": today + timezone.timedelta(hours=22),
        "rotation_start": today + timezone.timedelta(hours=22),
        "duration": timezone.timedelta(hours=1),
        "schedule": schedule2,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[admin]])
    schedule2.refresh_ical_file()

    # schedule3
    make_schedule(organization, schedule_class=OnCallScheduleWeb)

    schedules = OnCallSchedule.objects.related_to_user(admin)
    assert set(schedules) == {schedule1, schedule2}


@pytest.mark.django_db
def test_user_related_schedules_only_username(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
):
    organization = make_organization()
    # oncall is used as keyword in the ical calendar definition,
    # shouldn't be associated to the user
    user = make_user_for_organization(organization, username="oncall")
    other_user = make_user_for_organization(organization, username="other")

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    schedule1 = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    shifts = (
        # user, priority, start time (h), duration (seconds)
        (user, 1, 0, (24 * 60 * 60) - 1),  # r1-1: 0-23:59:59
    )
    for user, priority, start_h, duration in shifts:
        data = {
            "start": today + timezone.timedelta(hours=start_h),
            "rotation_start": today + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(seconds=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule1,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])
    schedule1.refresh_ical_file()

    schedule2 = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    override_data = {
        "start": today + timezone.timedelta(hours=22),
        "rotation_start": today + timezone.timedelta(hours=22),
        "duration": timezone.timedelta(hours=1),
        "schedule": schedule2,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[user]])
    schedule2.refresh_ical_file()

    # schedule3
    schedule3 = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    override_data = {
        "start": today + timezone.timedelta(hours=22),
        "rotation_start": today + timezone.timedelta(hours=22),
        "duration": timezone.timedelta(hours=1),
        "schedule": schedule3,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[other_user]])
    schedule3.refresh_ical_file()

    schedules = OnCallSchedule.objects.related_to_user(user)
    assert set(schedules) == {schedule1, schedule2}


@pytest.mark.django_db
def test_upcoming_shift_for_user(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
):
    organization = make_organization()
    admin = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    shifts = (
        # user, priority, start time (h), duration (seconds)
        (admin, 1, 0, (24 * 60 * 60) - 1),  # r1-1: 0-23:59:59
    )
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for user, priority, start_h, duration in shifts:
        data = {
            "start": today + timezone.timedelta(hours=start_h),
            "rotation_start": today + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(seconds=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])
    schedule.refresh_ical_file()
    schedule.refresh_ical_final_schedule()

    current_shift, upcoming_shift = schedule.upcoming_shift_for_user(admin)
    assert current_shift is not None and current_shift["start"] == on_call_shift.start
    next_shift_start = on_call_shift.start + timezone.timedelta(days=1)
    assert upcoming_shift is not None and upcoming_shift["start"] == next_shift_start

    current_shift, upcoming_shift = schedule.upcoming_shift_for_user(other_user)
    assert current_shift is None
    assert upcoming_shift is None


@pytest.mark.django_db
def test_refresh_ical_final_schedule_ok(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
):
    organization = make_organization()
    u1 = make_user_for_organization(organization)
    u2 = make_user_for_organization(organization)

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    shifts = (
        # user, priority, start time (h), duration (seconds)
        (u1, 1, 0, (12 * 60 * 60) - 1),  # r1-1: 0-11:59:59
        (u2, 1, 12, (12 * 60 * 60) - 1),  # r1-1: 12-23:59:59
    )
    for user, priority, start_h, duration in shifts:
        data = {
            "start": today + timezone.timedelta(hours=start_h),
            "rotation_start": today + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(seconds=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

    override_data = {
        "start": today + timezone.timedelta(hours=22),
        "rotation_start": today + timezone.timedelta(hours=22),
        "duration": timezone.timedelta(hours=1),
        "schedule": schedule,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[u1]])
    schedule.refresh_ical_file()

    expected_events = {
        # user, start, end, type
        (
            u1.username,
            today,
            today + timezone.timedelta(seconds=(12 * 60 * 60) - 1),
            OnCallSchedule.PRIMARY,
        ),
        (
            u2.username,
            today + timezone.timedelta(hours=12),
            today + timezone.timedelta(hours=22),
            OnCallSchedule.PRIMARY,
        ),
        (
            u1.username,
            today + timezone.timedelta(hours=22),
            today + timezone.timedelta(hours=23),
            OnCallSchedule.OVERRIDES,
        ),
        (
            u2.username,
            today + timezone.timedelta(hours=23),
            today + timezone.timedelta(seconds=(24 * 60 * 60) - 1),
            OnCallSchedule.PRIMARY,
        ),
    }

    for i in range(2):
        # running multiple times keeps the same events in place
        with patch("apps.schedules.models.on_call_schedule.EXPORT_WINDOW_DAYS_AFTER", 1):
            with patch("apps.schedules.models.on_call_schedule.EXPORT_WINDOW_DAYS_BEFORE", 0):
                schedule.refresh_ical_final_schedule()

        assert schedule.cached_ical_final_schedule
        calendar = icalendar.Calendar.from_ical(schedule.cached_ical_final_schedule)
        for component in calendar.walk():
            if component.name == ICAL_COMPONENT_VEVENT:
                event = (
                    component[ICAL_SUMMARY],
                    component[ICAL_DATETIME_START].dt,
                    component[ICAL_DATETIME_END].dt,
                    component[ICAL_PRIORITY],
                )
                assert event in expected_events


@pytest.mark.django_db
def test_refresh_ical_final_schedule_cancel_deleted_events(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
):
    organization = make_organization()
    u1 = make_user_for_organization(organization)
    u2 = make_user_for_organization(organization)

    tomorrow = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timezone.timedelta(days=1)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    shifts = (
        # user, priority, start time (h), duration (seconds)
        (u1, 1, 0, (24 * 60 * 60) - 1),  # r1-1: 0-23:59:59
    )
    for user, priority, start_h, duration in shifts:
        data = {
            "start": tomorrow + timezone.timedelta(hours=start_h),
            "rotation_start": tomorrow + timezone.timedelta(hours=start_h),
            "duration": timezone.timedelta(seconds=duration),
            "priority_level": priority,
            "frequency": CustomOnCallShift.FREQUENCY_DAILY,
            "schedule": schedule,
        }
        on_call_shift = make_on_call_shift(
            organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
        )
        on_call_shift.add_rolling_users([[user]])

    override_data = {
        "start": tomorrow + timezone.timedelta(hours=22),
        "rotation_start": tomorrow + timezone.timedelta(hours=22),
        "duration": timezone.timedelta(hours=1),
        "schedule": schedule,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[u2]])

    # refresh ical files
    schedule.refresh_ical_file()
    with patch("apps.schedules.models.on_call_schedule.EXPORT_WINDOW_DAYS_AFTER", 1):
        with patch("apps.schedules.models.on_call_schedule.EXPORT_WINDOW_DAYS_BEFORE", 0):
            schedule.refresh_ical_final_schedule()

    # delete override, re-check the final refresh
    override.delete()

    # reload instance to avoid cached properties issue
    schedule = OnCallScheduleWeb.objects.get(id=schedule.id)
    schedule.refresh_ical_file()

    with patch("apps.schedules.models.on_call_schedule.EXPORT_WINDOW_DAYS_AFTER", 1):
        with patch("apps.schedules.models.on_call_schedule.EXPORT_WINDOW_DAYS_BEFORE", 0):
            schedule.refresh_ical_final_schedule()

    # check for deleted override
    calendar = icalendar.Calendar.from_ical(schedule.cached_ical_final_schedule)
    for component in calendar.walk():
        if component.name == ICAL_COMPONENT_VEVENT and component[ICAL_SUMMARY] == u2.username:
            # check event is cancelled
            assert component[ICAL_DATETIME_START].dt == component[ICAL_DATETIME_END].dt
            assert component[ICAL_LAST_MODIFIED]
            assert component[ICAL_STATUS] == ICAL_STATUS_CANCELLED


@pytest.mark.django_db
def test_refresh_ical_final_schedule_cancelled_not_updated(
    make_organization,
    make_user_for_organization,
    make_schedule,
):
    organization = make_organization()
    u1 = make_user_for_organization(organization)
    u2 = make_user_for_organization(organization)
    last_week = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) - timezone.timedelta(days=7)
    last_week_timestamp = last_week.strftime("%Y%m%dT%H%M%S")
    cached_ical_final_schedule = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        VERSION:2.0
        PRODID://Grafana Labs//Grafana On-Call//
        CALSCALE:GREGORIAN
        X-WR-CALNAME:Cup cut.
        X-WR-TIMEZONE:UTC
        BEGIN:VEVENT
        SUMMARY:{}
        DTSTART;VALUE=DATE-TIME:20220414T000000Z
        DTEND;VALUE=DATE-TIME:20220414T000000Z
        DTSTAMP;VALUE=DATE-TIME:20220414T190951Z
        UID:O231U3VXVIYRX-202304140000-U5FWIHEASEWS2
        LAST-MODIFIED;VALUE=DATE-TIME:20220414T190951Z
        STATUS:CANCELLED
        END:VEVENT
        BEGIN:VEVENT
        SUMMARY:{}
        DTSTART;VALUE=DATE-TIME:{}Z
        DTEND;VALUE=DATE-TIME:{}Z
        DTSTAMP;VALUE=DATE-TIME:20230414T190951Z
        UID:OBPQ1TI99E4DG-202304141200-U2G6RZQM3S3I9
        LAST-MODIFIED;VALUE=DATE-TIME:{}Z
        STATUS:CANCELLED
        END:VEVENT
        END:VCALENDAR
    """.format(
            u1.username, u2.username, last_week_timestamp, last_week_timestamp, last_week_timestamp
        )
    )

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        cached_ical_final_schedule=cached_ical_final_schedule,
    )

    schedule.refresh_ical_final_schedule()

    # check old event is dropped, recent one is kept unchanged
    event_count = 0
    calendar = icalendar.Calendar.from_ical(schedule.cached_ical_final_schedule)
    for component in calendar.walk():
        if component.name == ICAL_COMPONENT_VEVENT:
            event_count += 1
            if component[ICAL_SUMMARY] == u2.username:
                # check event is unchanged
                assert component[ICAL_DATETIME_START].dt == last_week
                assert component[ICAL_DATETIME_END].dt == last_week
                assert component[ICAL_LAST_MODIFIED].dt == last_week
                assert component[ICAL_STATUS] == ICAL_STATUS_CANCELLED
    assert event_count == 1


@pytest.mark.django_db
def test_refresh_ical_final_schedule_event_in_the_past(
    make_organization,
    make_user_for_organization,
    make_schedule,
):
    organization = make_organization()
    u1 = make_user_for_organization(organization)
    cached_ical_final_schedule = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        VERSION:2.0
        PRODID://Grafana Labs//Grafana On-Call//
        CALSCALE:GREGORIAN
        X-WR-CALNAME:Cup cut.
        X-WR-TIMEZONE:UTC
        BEGIN:VEVENT
        SUMMARY:{}
        DTSTART;VALUE=DATE-TIME:20220414T000000Z
        DTEND;VALUE=DATE-TIME:20220414T000000Z
        DTSTAMP;VALUE=DATE-TIME:20220414T190951Z
        UID:O231U3VXVIYRX-202304140000-U5FWIHEASEWS2
        LAST-MODIFIED;VALUE=DATE-TIME:20220414T190951Z
        END:VEVENT
        END:VCALENDAR
    """.format(
            u1.username
        )
    )

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        cached_ical_final_schedule=cached_ical_final_schedule,
    )

    schedule.refresh_ical_final_schedule()

    # check old event is dropped
    calendar = icalendar.Calendar.from_ical(schedule.cached_ical_final_schedule)
    events = [component for component in calendar.walk() if component.name == ICAL_COMPONENT_VEVENT]
    assert len(events) == 0


@pytest.mark.django_db
def test_refresh_ical_final_schedule_all_day_date_event(
    make_organization,
    make_user_for_organization,
    make_schedule,
):
    organization = make_organization()
    u1 = make_user_for_organization(organization)
    cached_ical_final_schedule = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        VERSION:2.0
        PRODID://Grafana Labs//Grafana On-Call//
        CALSCALE:GREGORIAN
        X-WR-CALNAME:Cup cut.
        X-WR-TIMEZONE:UTC
        BEGIN:VEVENT
        SUMMARY:{}
        DTSTART;VALUE=DATE:20221203
        DTEND;VALUE=DATE:20221205
        DTSTAMP;VALUE=DATE-TIME:20220414T190951Z
        UID:O231U3VXVIYRX-202304140000-U5FWIHEASEWS2
        LAST-MODIFIED;VALUE=DATE-TIME:20220414T190951Z
        END:VEVENT
        END:VCALENDAR
    """.format(
            u1.username
        )
    )

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        cached_ical_final_schedule=cached_ical_final_schedule,
    )

    schedule.refresh_ical_final_schedule()

    # check old event is dropped
    calendar = icalendar.Calendar.from_ical(schedule.cached_ical_final_schedule)
    events = [component for component in calendar.walk() if component.name == ICAL_COMPONENT_VEVENT]
    assert len(events) == 0


@pytest.mark.django_db
def test_event_until_non_utc(make_organization, make_schedule):
    organization = make_organization()
    cached_ical_primary_schedule = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        VERSION:2.0
        PRODID:testing
        CALSCALE:GREGORIAN
        BEGIN:VEVENT
        CREATED:20220316T121102Z
        LAST-MODIFIED:20230127T151619Z
        DTSTAMP:20230127T151619Z
        UID:something
        SUMMARY:testing
        RRULE:FREQ=WEEKLY;UNTIL=20221231T010101
        DTSTART;TZID=Europe/Madrid:20220309T130000
        DTEND;TZID=Europe/Madrid:20220309T133000
        SEQUENCE:4
        END:VEVENT
        END:VCALENDAR
    """
    )

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        cached_ical_file_primary=cached_ical_primary_schedule,
    )

    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    # check this works without raising exception
    datetime_end = now + timezone.timedelta(days=7)
    schedule.final_events(now, datetime_end)


@pytest.mark.django_db
@pytest.mark.parametrize("swap_taken", [False, True])
def test_swap_request_split_start(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
    make_shift_swap_request,
    swap_taken,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today + timezone.timedelta(hours=12)
    duration = timezone.timedelta(hours=3)
    data = {
        "start": start,
        "rotation_start": start,
        "duration": duration,
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    tomorrow = today + timezone.timedelta(days=1)
    # setup swap request
    swap_request = make_shift_swap_request(
        schedule,
        user,
        swap_start=tomorrow + timezone.timedelta(hours=13),
        swap_end=tomorrow + timezone.timedelta(hours=18),
    )
    if swap_taken:
        swap_request.take(other_user)

    events = schedule.filter_events(today, today + timezone.timedelta(days=2))

    expected = [
        # start, end, swap requested
        (start, start + duration, False),  # today shift unchanged
        (start + timezone.timedelta(days=1), start + timezone.timedelta(days=1, hours=1), False),  # first split
        (
            start + timezone.timedelta(days=1, hours=1),
            start + timezone.timedelta(days=1, hours=3),
            True,
        ),  # second split
    ]
    returned = [(e["start"], e["end"], bool(e["users"][0].get("swap_request", False))) for e in events]
    assert returned == expected
    # check swap request details
    assert events[2]["users"][0]["swap_request"]["pk"] == swap_request.public_primary_key
    if swap_taken:
        assert events[2]["users"][0]["pk"] == other_user.public_primary_key
        assert events[2]["users"][0]["swap_request"]["user"]["pk"] == user.public_primary_key
    else:
        assert events[2]["users"][0]["pk"] == user.public_primary_key


@pytest.mark.django_db
@pytest.mark.parametrize("swap_taken", [False, True])
def test_swap_request_split_end(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
    make_shift_swap_request,
    swap_taken,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today + timezone.timedelta(hours=12)
    duration = timezone.timedelta(hours=3)
    data = {
        "start": start,
        "rotation_start": start,
        "duration": duration,
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    tomorrow = today + timezone.timedelta(days=1)
    # setup swap request
    swap_request = make_shift_swap_request(
        schedule,
        user,
        swap_start=tomorrow + timezone.timedelta(hours=10),
        swap_end=tomorrow + timezone.timedelta(hours=13),
    )
    if swap_taken:
        swap_request.take(other_user)

    events = schedule.filter_events(today, today + timezone.timedelta(days=2))

    expected = [
        # start, end, swap requested
        (start, start + duration, False),  # today shift unchanged
        (start + timezone.timedelta(days=1), start + timezone.timedelta(days=1, hours=1), True),  # first split
        (
            start + timezone.timedelta(days=1, hours=1),
            start + timezone.timedelta(days=1, hours=3),
            False,
        ),  # second split
    ]
    returned = [(e["start"], e["end"], bool(e["users"][0].get("swap_request", False))) for e in events]
    assert returned == expected
    # check swap request details
    assert events[1]["users"][0]["swap_request"]["pk"] == swap_request.public_primary_key
    if swap_taken:
        assert events[1]["users"][0]["pk"] == other_user.public_primary_key
        assert events[1]["users"][0]["swap_request"]["user"]["pk"] == user.public_primary_key
    else:
        assert events[1]["users"][0]["pk"] == user.public_primary_key


@pytest.mark.django_db
def test_swap_request_split_final_events_range(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
    make_shift_swap_request,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today + timezone.timedelta(hours=10)
    duration = timezone.timedelta(hours=8)
    data = {
        "start": start,
        "rotation_start": start,
        "duration": duration,
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    tomorrow = today + timezone.timedelta(days=1)
    # setup swap request
    swap_request = make_shift_swap_request(
        schedule,
        user,
        swap_start=tomorrow + timezone.timedelta(hours=16),
        swap_end=tomorrow + timezone.timedelta(hours=18),
    )
    swap_request.take(other_user)

    # check final events for tomorrow while swap in progress
    now = tomorrow + timezone.timedelta(hours=16, minutes=10)
    events = schedule.final_events(now, now)

    assert len(events) == 1
    expected = [
        # start, end, on-call user
        (
            tomorrow + timezone.timedelta(hours=16),
            tomorrow + timezone.timedelta(hours=18),
            other_user.public_primary_key,
        ),
    ]
    returned = [(e["start"], e["end"], e["users"][0]["pk"]) for e in events]
    assert returned == expected


@pytest.mark.django_db
@pytest.mark.parametrize("swap_taken", [False, True])
def test_swap_request_split_both(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
    make_shift_swap_request,
    swap_taken,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today + timezone.timedelta(hours=12)
    duration = timezone.timedelta(hours=3)
    data = {
        "start": start,
        "rotation_start": start,
        "duration": duration,
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    tomorrow = today + timezone.timedelta(days=1)
    # setup swap request
    swap_request = make_shift_swap_request(
        schedule,
        user,
        swap_start=tomorrow + timezone.timedelta(hours=13),
        swap_end=tomorrow + timezone.timedelta(hours=14),
    )
    if swap_taken:
        swap_request.take(other_user)

    events = schedule.filter_events(today, today + timezone.timedelta(days=2))

    expected = [
        # start, end, swap requested
        (start, start + duration, False),  # today shift unchanged
        (start + timezone.timedelta(days=1), start + timezone.timedelta(days=1, hours=1), False),  # first split
        (
            start + timezone.timedelta(days=1, hours=1),
            start + timezone.timedelta(days=1, hours=2),
            True,
        ),  # second split
        (
            start + timezone.timedelta(days=1, hours=2),
            start + timezone.timedelta(days=1, hours=3),
            False,
        ),  # third split
    ]
    returned = [(e["start"], e["end"], bool(e["users"][0].get("swap_request", False))) for e in events]
    assert returned == expected
    # check swap request details
    assert events[2]["users"][0]["swap_request"]["pk"] == swap_request.public_primary_key
    if swap_taken:
        assert events[2]["users"][0]["pk"] == other_user.public_primary_key
        assert events[2]["users"][0]["swap_request"]["user"]["pk"] == user.public_primary_key
    else:
        assert events[2]["users"][0]["pk"] == user.public_primary_key

    # check cached final schedule reflects swap
    # force final schedule export to consider 2 days only
    with patch("apps.schedules.models.on_call_schedule.EXPORT_WINDOW_DAYS_AFTER", 2):
        with patch("apps.schedules.models.on_call_schedule.EXPORT_WINDOW_DAYS_BEFORE", 0):
            schedule.refresh_ical_final_schedule()
    assert schedule.cached_ical_final_schedule
    if swap_taken:
        expected_events = [
            # start, end, user
            (start, start + duration, user.username),  # today shift unchanged
            (
                start + timezone.timedelta(days=1),
                start + timezone.timedelta(days=1, hours=1),
                user.username,
            ),  # first split
            (
                start + timezone.timedelta(days=1, hours=1),
                start + timezone.timedelta(days=1, hours=2),
                other_user.username if swap_taken else user.username,
            ),  # second split
            (
                start + timezone.timedelta(days=1, hours=2),
                start + timezone.timedelta(days=1, hours=3),
                user.username,
            ),  # third split
        ]
    else:
        expected_events = [
            # start, end, user
            (start, start + duration, user.username),  # today shift unchanged
            (
                start + timezone.timedelta(days=1),
                start + timezone.timedelta(days=1) + duration,
                user.username,
            ),  # no split
        ]
    calendar = icalendar.Calendar.from_ical(schedule.cached_ical_final_schedule)
    for component in calendar.walk():
        if component.name == ICAL_COMPONENT_VEVENT:
            event = (
                component[ICAL_DATETIME_START].dt,
                component[ICAL_DATETIME_END].dt,
                component[ICAL_SUMMARY],
            )
            assert event in expected_events


@pytest.mark.django_db
@pytest.mark.parametrize("swap_taken", [False, True])
def test_swap_request_ignore_untaken(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
    make_shift_swap_request,
    swap_taken,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today + timezone.timedelta(hours=12)
    duration = timezone.timedelta(hours=3)
    data = {
        "start": start,
        "rotation_start": start,
        "duration": duration,
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    tomorrow = today + timezone.timedelta(days=1)
    # setup swap request
    swap_request = make_shift_swap_request(
        schedule,
        user,
        swap_start=tomorrow + timezone.timedelta(hours=13),
        swap_end=tomorrow + timezone.timedelta(hours=14),
    )
    if swap_taken:
        swap_request.take(other_user)

    # set flag to ignore untaken swaps
    events = schedule.filter_events(today, today + timezone.timedelta(days=2), ignore_untaken_swaps=True)

    if swap_taken:
        expected = [
            # start, end, swap requested
            (start, start + duration, False),  # today shift unchanged
            (start + timezone.timedelta(days=1), start + timezone.timedelta(days=1, hours=1), False),  # first split
            (
                start + timezone.timedelta(days=1, hours=1),
                start + timezone.timedelta(days=1, hours=2),
                True,
            ),  # second split
            (
                start + timezone.timedelta(days=1, hours=2),
                start + timezone.timedelta(days=1, hours=3),
                False,
            ),  # third split
        ]
    else:
        expected = [
            # start, end, swap requested
            (start, start + duration, False),  # today shift unchanged
            (start + timezone.timedelta(days=1), start + timezone.timedelta(days=1) + duration, False),  # no split
        ]

    returned = [(e["start"], e["end"], bool(e["users"][0].get("swap_request", False))) for e in events]
    assert returned == expected
    # check swap request details
    if swap_taken:
        assert events[2]["users"][0]["swap_request"]["pk"] == swap_request.public_primary_key
        assert events[2]["users"][0]["pk"] == other_user.public_primary_key
        assert events[2]["users"][0]["swap_request"]["user"]["pk"] == user.public_primary_key


@pytest.mark.django_db
@pytest.mark.parametrize("swap_taken", [False, True])
def test_swap_request_whole_shift(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
    make_shift_swap_request,
    swap_taken,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today + timezone.timedelta(hours=12)
    duration = timezone.timedelta(hours=3)
    data = {
        "start": start,
        "rotation_start": start,
        "duration": duration,
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    tomorrow = today + timezone.timedelta(days=1)
    # setup swap request
    swap_request = make_shift_swap_request(
        schedule,
        user,
        # swap request starting right after shift ends
        swap_start=tomorrow + timezone.timedelta(hours=15),
        # swap request ending right before shift starts
        swap_end=tomorrow + timezone.timedelta(days=2, hours=12),
    )
    if swap_taken:
        swap_request.take(other_user)

    events = schedule.filter_events(tomorrow, tomorrow + timezone.timedelta(days=2))

    tomorrow_start = start + timezone.timedelta(days=1)
    expected = [
        # start, end, swap requested
        (tomorrow_start, tomorrow_start + duration, False),  # today shift unchanged
        (
            tomorrow_start + timezone.timedelta(days=1),
            tomorrow_start + timezone.timedelta(days=1, hours=3),
            True,
        ),  # no splits
    ]
    returned = [(e["start"], e["end"], bool(e["users"][0].get("swap_request", False))) for e in events]
    assert returned == expected
    # check swap request details
    assert events[1]["users"][0]["swap_request"]["pk"] == swap_request.public_primary_key
    if swap_taken:
        assert events[1]["users"][0]["pk"] == other_user.public_primary_key
        assert events[1]["users"][0]["swap_request"]["user"]["pk"] == user.public_primary_key
    else:
        assert events[1]["users"][0]["pk"] == user.public_primary_key


@pytest.mark.django_db
@pytest.mark.parametrize("swap_taken", [False, True])
def test_swap_request_partial_replace(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
    make_shift_swap_request,
    swap_taken,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    another_user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today + timezone.timedelta(hours=12)
    duration = timezone.timedelta(hours=3)
    data = {
        "start": start,
        "rotation_start": start,
        "duration": duration,
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user, another_user]])

    tomorrow = today + timezone.timedelta(days=1)
    # setup swap request
    swap_request = make_shift_swap_request(
        schedule,
        user,
        swap_start=tomorrow + timezone.timedelta(hours=10),
        swap_end=tomorrow + timezone.timedelta(hours=13),
    )
    if swap_taken:
        swap_request.take(other_user)

    events = schedule.filter_events(today, today + timezone.timedelta(days=2))

    expected = [
        # start, end, swap requested
        (start, start + duration, False),  # today shift unchanged
        (start + timezone.timedelta(days=1), start + timezone.timedelta(days=1, hours=1), True),  # first split
        (
            start + timezone.timedelta(days=1, hours=1),
            start + timezone.timedelta(days=1, hours=3),
            False,
        ),  # second split
    ]
    expected_user = user
    if swap_taken:
        expected_user = other_user
    returned = [
        (
            e["start"],
            e["end"],
            bool([u for u in e["users"] if u["pk"] == expected_user.public_primary_key and u.get("swap_request")]),
        )
        for e in events
    ]
    assert returned == expected
    # check swap request details
    user_pks = [u["pk"] for u in events[1]["users"]]
    assert expected_user.public_primary_key in user_pks
    if swap_taken:
        for u in events[1]["users"]:
            if u["pk"] == expected_user:
                assert u["swap_request"]["pk"] == swap_request.public_primary_key
                assert u["swap_request"]["user"]["pk"] == user.public_primary_key


@pytest.mark.django_db
def test_swap_request_no_changes(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
    make_shift_swap_request,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    other_user = make_user_for_organization(organization)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start = today + timezone.timedelta(hours=12)
    duration = timezone.timedelta(hours=3)
    data = {
        "start": start,
        "rotation_start": start,
        "duration": duration,
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    events_before = schedule.filter_events(today, today + timezone.timedelta(days=2))

    # setup swap requests
    tomorrow = today + timezone.timedelta(days=1)
    # user not in schedule
    make_shift_swap_request(schedule, other_user, swap_start=today, swap_end=tomorrow)
    # deleted request
    make_shift_swap_request(schedule, user, swap_start=today, swap_end=tomorrow, deleted_at=today)
    # swap request in the past
    make_shift_swap_request(
        schedule, user, swap_start=today - timezone.timedelta(days=7), swap_end=tomorrow - timezone.timedelta(days=7)
    )
    # untaken swap in progress (past due)
    make_shift_swap_request(schedule, user, swap_start=today - timezone.timedelta(days=1), swap_end=tomorrow)

    events_after = schedule.filter_events(today, today + timezone.timedelta(days=2))
    assert events_before == events_after


@pytest.mark.django_db
def test_filter_events_ical_duplicated_uid(make_organization, make_user_for_organization, make_schedule, get_ical):
    calendar = get_ical("modified_recurring_event.ics")
    organization = make_organization()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    schedule.cached_ical_file_primary = calendar.to_ical()
    make_user_for_organization(organization, username="user")
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    datetime_start = datetime.datetime(2023, 7, 17, 0, 0, tzinfo=pytz.UTC)
    datetime_end = datetime_start + datetime.timedelta(days=7)
    events = schedule.final_events(datetime_start, datetime_end)

    assert len(events) == 2
    assert events[0]["shift"]["pk"] == "eventuid@google.com_1"
    assert events[1]["shift"]["pk"] == "eventuid@google.com_2_1970-01-01T01:00:00+01:00"
