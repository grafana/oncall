import pytest
from django.utils import timezone

from apps.schedules.ical_utils import list_users_to_notify_from_ical
from apps.schedules.models import CustomOnCallShift, OnCallSchedule, OnCallScheduleCalendar, OnCallScheduleWeb


@pytest.mark.django_db
def test_get_on_call_users_from_single_event(make_organization_and_user, make_on_call_shift, make_schedule):
    organization, user = make_organization_and_user()

    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    date = timezone.now().replace(tzinfo=None, microsecond=0)

    data = {
        "priority_level": 1,
        "start": date,
        "duration": timezone.timedelta(seconds=10800),
    }

    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT, **data
    )
    on_call_shift.users.add(user)

    schedule.custom_on_call_shifts.add(on_call_shift)

    # user is on-call
    date = date + timezone.timedelta(minutes=5)
    users_on_call = list_users_to_notify_from_ical(schedule, date)
    assert len(users_on_call) == 1
    assert user in users_on_call


@pytest.mark.django_db
def test_get_on_call_users_from_web_schedule_override(make_organization_and_user, make_on_call_shift, make_schedule):
    organization, user = make_organization_and_user()

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    date = timezone.now().replace(tzinfo=None, microsecond=0)

    data = {
        "start": date,
        "duration": timezone.timedelta(seconds=10800),
        "schedule": schedule,
    }

    on_call_shift = make_on_call_shift(organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **data)
    on_call_shift.users.add(user)

    # user is on-call
    date = date + timezone.timedelta(minutes=5)
    users_on_call = list_users_to_notify_from_ical(schedule, date)
    assert len(users_on_call) == 1
    assert user in users_on_call


@pytest.mark.django_db
def test_get_on_call_users_from_recurrent_event(make_organization_and_user, make_on_call_shift, make_schedule):
    organization, user = make_organization_and_user()

    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    date = timezone.now().replace(tzinfo=None, microsecond=0)

    data = {
        "priority_level": 1,
        "start": date,
        "duration": timezone.timedelta(seconds=10800),
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 2,
    }

    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_RECURRENT_EVENT, **data
    )
    on_call_shift.users.add(user)

    schedule.custom_on_call_shifts.add(on_call_shift)

    # user is on-call
    date = date + timezone.timedelta(minutes=5)
    users_on_call = list_users_to_notify_from_ical(schedule, date)
    assert len(users_on_call) == 1
    assert user in users_on_call

    # user is not on-call according to event recurrence rules (interval = 2)
    date = date + timezone.timedelta(days=1)
    users_on_call = list_users_to_notify_from_ical(schedule, date)
    assert len(users_on_call) == 0

    # user is on-call again
    date = date + timezone.timedelta(days=1)
    users_on_call = list_users_to_notify_from_ical(schedule, date)
    assert len(users_on_call) == 1
    assert user in users_on_call


@pytest.mark.django_db
def test_get_on_call_users_from_web_schedule_recurrent_event(
    make_organization_and_user, make_on_call_shift, make_schedule
):
    organization, user = make_organization_and_user()

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    date = timezone.now().replace(tzinfo=None, microsecond=0)

    data = {
        "priority_level": 1,
        "start": date,
        "duration": timezone.timedelta(seconds=10800),
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 2,
        "schedule": schedule,
    }

    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_RECURRENT_EVENT, **data
    )
    on_call_shift.users.add(user)

    # user is on-call
    date = date + timezone.timedelta(minutes=5)
    users_on_call = list_users_to_notify_from_ical(schedule, date)
    assert len(users_on_call) == 1
    assert user in users_on_call

    # user is not on-call according to event recurrence rules (interval = 2)
    date = date + timezone.timedelta(days=1)
    users_on_call = list_users_to_notify_from_ical(schedule, date)
    assert len(users_on_call) == 0

    # user is on-call again
    date = date + timezone.timedelta(days=1)
    users_on_call = list_users_to_notify_from_ical(schedule, date)
    assert len(users_on_call) == 1
    assert user in users_on_call


@pytest.mark.django_db
def test_get_on_call_users_from_rolling_users_event(
    make_organization_and_user, make_user_for_organization, make_on_call_shift, make_schedule
):
    organization, user_1 = make_organization_and_user()
    user_2 = make_user_for_organization(organization)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    now = timezone.now().replace(tzinfo=None, microsecond=0)

    data = {
        "priority_level": 1,
        "start": now,
        "duration": timezone.timedelta(seconds=10800),
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "interval": 2,
    }
    rolling_users = [[user_1], [user_2]]
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users(rolling_users)
    schedule.custom_on_call_shifts.add(on_call_shift)

    date = now + timezone.timedelta(minutes=5)

    user_1_on_call_dates = [date, date + timezone.timedelta(days=4)]
    user_2_on_call_dates = [date + timezone.timedelta(days=2), date + timezone.timedelta(days=6)]
    nobody_on_call_dates = [
        date + timezone.timedelta(days=1),
        date + timezone.timedelta(days=3),
        date + timezone.timedelta(days=5),
    ]

    for date in user_1_on_call_dates:
        users_on_call = list_users_to_notify_from_ical(schedule, date)
        assert len(users_on_call) == 1
        assert user_1 in users_on_call

    for date in user_2_on_call_dates:
        users_on_call = list_users_to_notify_from_ical(schedule, date)
        assert len(users_on_call) == 1
        assert user_2 in users_on_call

    for date in nobody_on_call_dates:
        users_on_call = list_users_to_notify_from_ical(schedule, date)
        assert len(users_on_call) == 0


@pytest.mark.django_db
def test_get_oncall_users_for_empty_schedule(
    make_organization,
    make_schedule,
):
    organization = make_organization()

    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    schedules = OnCallSchedule.objects.filter(pk=schedule.pk)

    assert schedules.get_oncall_users() == []


@pytest.mark.django_db
def test_get_oncall_users_for_multiple_schedules(
    make_organization,
    make_user_for_organization,
    make_on_call_shift,
    make_schedule,
):
    organization = make_organization()

    user_1 = make_user_for_organization(organization)
    user_2 = make_user_for_organization(organization)
    user_3 = make_user_for_organization(organization)

    schedule_1 = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    schedule_2 = make_schedule(organization, schedule_class=OnCallScheduleCalendar)

    now = timezone.now().replace(tzinfo=None, microsecond=0)

    on_call_shift_1 = make_on_call_shift(
        organization=organization,
        shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT,
        priority_level=1,
        start=now,
        duration=timezone.timedelta(minutes=30),
    )

    on_call_shift_2 = make_on_call_shift(
        organization=organization,
        shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT,
        priority_level=1,
        start=now,
        duration=timezone.timedelta(minutes=10),
    )

    on_call_shift_3 = make_on_call_shift(
        organization=organization,
        shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT,
        priority_level=1,
        start=now + timezone.timedelta(minutes=10),
        duration=timezone.timedelta(minutes=30),
    )

    on_call_shift_1.users.add(user_1)
    on_call_shift_1.users.add(user_2)

    on_call_shift_2.users.add(user_2)

    on_call_shift_3.users.add(user_3)

    schedule_1.custom_on_call_shifts.add(on_call_shift_1)

    schedule_2.custom_on_call_shifts.add(on_call_shift_2)
    schedule_2.custom_on_call_shifts.add(on_call_shift_3)

    schedules = OnCallSchedule.objects.filter(pk__in=[schedule_1.pk, schedule_2.pk])

    expected = set(schedules.get_oncall_users(events_datetime=now + timezone.timedelta(seconds=1)))
    assert expected == {user_1, user_2}

    expected = set(schedules.get_oncall_users(events_datetime=now + timezone.timedelta(minutes=10, seconds=1)))
    assert expected == {user_1, user_2, user_3}

    assert schedules.get_oncall_users(events_datetime=now + timezone.timedelta(minutes=30, seconds=1)) == [user_3]

    assert schedules.get_oncall_users(events_datetime=now + timezone.timedelta(minutes=40, seconds=1)) == []


@pytest.mark.django_db
def test_shift_convert_to_ical(make_organization_and_user, make_on_call_shift):
    organization, user = make_organization_and_user()

    date = timezone.now().replace(tzinfo=None, microsecond=0)
    until = date + timezone.timedelta(days=30)

    data = {
        "priority_level": 1,
        "start": date,
        "duration": timezone.timedelta(seconds=10800),
        "frequency": CustomOnCallShift.FREQUENCY_HOURLY,
        "interval": 1,
        "until": until,
    }

    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_RECURRENT_EVENT, **data
    )
    on_call_shift.users.add(user)

    ical_data = on_call_shift.convert_to_ical()
    ical_rrule_until = on_call_shift.until.strftime("%Y%m%dT%H%M%S")
    expected_rrule = f"RRULE:FREQ=HOURLY;UNTIL={ical_rrule_until}Z;INTERVAL=1;WKST=SU"
    assert expected_rrule in ical_data
