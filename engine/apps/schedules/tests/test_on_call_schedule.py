import datetime
from unittest.mock import patch

import pytest
import pytz
from django.utils import timezone

from apps.api.permissions import LegacyAccessControlRole
from apps.schedules.ical_utils import memoized_users_in_ical
from apps.schedules.models import CustomOnCallShift, OnCallSchedule, OnCallScheduleCalendar, OnCallScheduleWeb


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
    events = schedule.filter_events("UTC", start_date, days=3, filter_by=OnCallSchedule.TYPE_ICAL_PRIMARY)
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
            "users": [{"display_name": user.username, "pk": user.public_primary_key}],
            "shift": {"pk": on_call_shift.public_primary_key},
            "source": "api",
        }
        for i in range(2)
    ]
    assert events == expected

    # filter overrides only
    events = schedule.filter_events("UTC", start_date, days=3, filter_by=OnCallSchedule.TYPE_ICAL_OVERRIDES)
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
            "users": [{"display_name": user.username, "pk": user.public_primary_key}],
            "shift": {"pk": override.public_primary_key},
            "source": "api",
        }
    ]
    assert events == expected_override

    # no type filter
    events = schedule.filter_events("UTC", start_date, days=3)
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

    events = schedule.filter_events(
        "UTC", start_date, days=1, filter_by=OnCallSchedule.TYPE_ICAL_PRIMARY, with_gap=True
    )
    expected = [
        {
            "calendar_type": None,
            "start": start_date + timezone.timedelta(milliseconds=1),
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
            "users": [{"display_name": user.username, "pk": user.public_primary_key}],
            "shift": {"pk": on_call_shift.public_primary_key},
            "source": "api",
        },
        {
            "calendar_type": None,
            "start": on_call_shift.start + on_call_shift.duration,
            "end": on_call_shift.start + timezone.timedelta(hours=13, minutes=59, seconds=59, milliseconds=1),
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

    events = schedule.filter_events(
        "UTC", start_date, days=1, filter_by=OnCallSchedule.TYPE_ICAL_PRIMARY, with_empty=True
    )
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
    start_date = (parsed_iso_day_to_check - timezone.timedelta(days=1)).date()

    events = schedule.final_events("UTC", start_date, days=2)
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
            datetime.datetime(2021, 1, 27, 23, 59, 59, 999999, tzinfo=pytz.UTC),
        ),
        (
            True,
            ["@Alice"],
            datetime.datetime(2021, 1, 27, 0, 0, tzinfo=pytz.UTC),
            datetime.datetime(2021, 1, 28, 23, 59, 59, 999999, tzinfo=pytz.UTC),
        ),
        (
            False,
            ["@Bob"],
            datetime.datetime(2021, 1, 27, 8, 0, tzinfo=pytz.UTC),
            datetime.datetime(2021, 1, 27, 17, 0, tzinfo=pytz.UTC),
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

    returned_events = schedule.final_events("UTC", start_date, days=1)

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
            "start": start_date + timezone.timedelta(hours=start, milliseconds=1 if start == 0 else 0),
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

    returned_events = schedule.final_events("UTC", start_date, days=1)

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

    returned_events = schedule.final_events("UTC", start_date, days=1)

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

    returned_events = schedule.final_events("UTC", start_date, days=1)

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

    rotation_events, final_events = schedule.preview_shift(new_shift, "UTC", start_date, days=1)

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
            "users": [{"display_name": other_user.username, "pk": other_user.public_primary_key}],
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

    rotation_events, final_events = schedule.preview_shift(new_shift, "UTC", start_date, days=1)

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

    rotation_events, final_events = schedule.preview_shift(new_shift, "UTC", start_date, days=1)

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
            "users": [{"display_name": other_user.username, "pk": other_user.public_primary_key}],
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

    users = schedule.related_users()
    assert users == set()


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
            organization=organization, shift_type=CustomOnCallShift.TYPE_RECURRENT_EVENT, **data
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

    schedule.refresh_from_db()
    users = schedule.related_users()
    assert users == set(u.public_primary_key for u in [user_a, user_d, user_e])


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

    events = schedule.filter_events("UTC", start_date, days=5, filter_by=OnCallSchedule.TYPE_ICAL_PRIMARY)
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
def test_api_schedule_use_overrides_from_db(make_organization, make_schedule, make_on_call_shift):
    organization = make_organization()
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
        schedule.preview_shift(non_override_shift, "UTC", now, 1)
