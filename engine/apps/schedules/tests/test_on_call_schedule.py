import pytest
from django.utils import timezone

from apps.schedules.models import CustomOnCallShift, OnCallSchedule, OnCallScheduleWeb
from common.constants.role import Role


@pytest.mark.django_db
def test_filter_events(make_organization, make_user_for_organization, make_schedule, make_on_call_shift):
    organization = make_organization()
    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_web_schedule",
    )
    user = make_user_for_organization(organization)
    viewer = make_user_for_organization(organization, role=Role.VIEWER)
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
    user = make_user_for_organization(organization, role=Role.VIEWER)
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
            organization=organization, shift_type=CustomOnCallShift.TYPE_RECURRENT_EVENT, **data
        )
        on_call_shift.users.add(user)

    # override: 22-23 / E
    override_data = {
        "start": start_date + timezone.timedelta(hours=22),
        "rotation_start": start_date + timezone.timedelta(hours=22),
        "duration": timezone.timedelta(hours=1),
        "schedule": schedule,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[user_e]])

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
        (22, 1, "E", None, False, True),  # 22-23 E (override)
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
