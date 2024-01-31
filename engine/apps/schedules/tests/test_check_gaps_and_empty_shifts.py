import datetime

import pytest
from django.utils import timezone

from apps.api.permissions import LegacyAccessControlRole
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb


@pytest.mark.django_db
def test_no_empty_shifts_no_gaps(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    user1 = make_user(organization=organization, username="user1")

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, name="test_schedule")

    now = timezone.now().replace(microsecond=0)
    start_date = now - datetime.timedelta(days=7, minutes=1)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": datetime.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user1]])
    schedule.refresh_ical_file()
    schedule.check_gaps_and_empty_shifts_for_next_week()
    schedule.refresh_from_db()

    assert schedule.has_gaps is False
    assert schedule.has_empty_shifts is False


@pytest.mark.django_db
def test_no_empty_shifts_but_gaps_now(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    user1 = make_user(organization=organization, username="user1")

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, name="test_schedule")

    now = timezone.now().replace(microsecond=0)
    start_date = now - datetime.timedelta(days=1, minutes=1)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": datetime.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
        "interval": 2,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user1]])
    schedule.refresh_ical_file()

    assert schedule.has_gaps is False
    assert schedule.has_empty_shifts is False

    schedule.check_gaps_and_empty_shifts_for_next_week()
    schedule.refresh_from_db()

    assert schedule.has_gaps is True
    assert schedule.has_empty_shifts is False


@pytest.mark.django_db
def test_empty_shifts_no_gaps(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    user1 = make_user(organization=organization, username="user1", role=LegacyAccessControlRole.VIEWER)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, name="test_schedule")

    now = timezone.now().replace(microsecond=0)
    start_date = now - datetime.timedelta(days=7, minutes=1)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": datetime.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user1]])
    schedule.refresh_ical_file()

    assert schedule.has_gaps is False
    assert schedule.has_empty_shifts is False

    schedule.check_gaps_and_empty_shifts_for_next_week()
    schedule.refresh_from_db()

    assert schedule.has_gaps is False
    assert schedule.has_empty_shifts is True


@pytest.mark.django_db
def test_empty_shifts_and_gaps(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    user1 = make_user(organization=organization, username="user1", role=LegacyAccessControlRole.VIEWER)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, name="test_schedule")

    now = timezone.now().replace(microsecond=0)
    start_date = now - datetime.timedelta(days=7, minutes=1)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": datetime.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
        "interval": 2,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user1]])
    schedule.refresh_ical_file()

    assert schedule.has_gaps is False
    assert schedule.has_empty_shifts is False

    schedule.check_gaps_and_empty_shifts_for_next_week()
    schedule.refresh_from_db()

    assert schedule.has_gaps is True
    assert schedule.has_empty_shifts is True


@pytest.mark.django_db
def test_empty_shifts_and_gaps_in_the_past(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    user1 = make_user(organization=organization, username="user1", role=LegacyAccessControlRole.VIEWER)
    user2 = make_user(organization=organization, username="user2", role=LegacyAccessControlRole.ADMIN)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, name="test_schedule")

    now = timezone.now().replace(microsecond=0)
    start_date = now - datetime.timedelta(days=7, minutes=1)
    until = start_date + datetime.timedelta(days=5, minutes=1)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": datetime.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
        "interval": 2,
        "until": until,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user1]])

    start_date2 = now - datetime.timedelta(days=4, minutes=1)
    data2 = {
        "start": start_date2,
        "rotation_start": start_date2,
        "duration": datetime.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift2 = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data2
    )
    on_call_shift2.add_rolling_users([[user2]])
    schedule.refresh_ical_file()

    assert schedule.has_gaps is False
    assert schedule.has_empty_shifts is False

    schedule.check_gaps_and_empty_shifts_for_next_week()
    schedule.refresh_from_db()

    assert schedule.has_gaps is False
    assert schedule.has_empty_shifts is False


@pytest.mark.django_db
def test_empty_shifts_and_gaps_in_the_future(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    user1 = make_user(organization=organization, username="user1", role=LegacyAccessControlRole.VIEWER)
    user2 = make_user(organization=organization, username="user2", role=LegacyAccessControlRole.ADMIN)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb, name="test_schedule")
    # empty shift with gaps starts in 7 days 1 min
    now = timezone.now().replace(microsecond=0)
    start_date = now + datetime.timedelta(days=7, minutes=1)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": datetime.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
        "interval": 2,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user1]])
    # normal shift ends in 7 days 1 min
    start_date2 = now - datetime.timedelta(days=7, minutes=1)
    until = now + datetime.timedelta(days=7, minutes=1)
    data2 = {
        "start": start_date2,
        "rotation_start": start_date2,
        "duration": datetime.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
        "until": until,
    }
    on_call_shift2 = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data2
    )
    on_call_shift2.add_rolling_users([[user2]])
    schedule.refresh_ical_file()

    assert schedule.has_gaps is False
    assert schedule.has_empty_shifts is False

    schedule.check_gaps_and_empty_shifts_for_next_week()
    schedule.refresh_from_db()
    # no gaps and empty shifts in the next 7 days
    assert schedule.has_gaps is False
    assert schedule.has_empty_shifts is False
