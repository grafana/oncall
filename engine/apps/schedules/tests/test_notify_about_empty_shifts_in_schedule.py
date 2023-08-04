import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.api.permissions import LegacyAccessControlRole
from apps.schedules.ical_utils import memoized_users_in_ical
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb
from apps.schedules.tasks import notify_about_empty_shifts_in_schedule


@pytest.mark.django_db
def test_no_empty_shifts_no_triggering_notification(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    user1 = make_user(organization=organization, username="user1")
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_schedule",
        channel="channel",
        prev_ical_file_overrides=None,
        cached_ical_file_overrides=None,
    )

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

    empty_shifts_report_sent_at = schedule.empty_shifts_report_sent_at

    with patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call") as mock_slack_api_call:
        notify_about_empty_shifts_in_schedule(schedule.pk)

    assert not mock_slack_api_call.called

    schedule.refresh_from_db()
    assert empty_shifts_report_sent_at != schedule.empty_shifts_report_sent_at


@pytest.mark.django_db
def test_empty_shifts_trigger_notification(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    user1 = make_user(organization=organization, username="user1", role=LegacyAccessControlRole.VIEWER)
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_schedule",
        channel="channel",
        prev_ical_file_overrides=None,
        cached_ical_file_overrides=None,
    )

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

    empty_shifts_report_sent_at = schedule.empty_shifts_report_sent_at

    with patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call") as mock_slack_api_call:
        notify_about_empty_shifts_in_schedule(schedule.pk)

    assert mock_slack_api_call.called

    schedule.refresh_from_db()
    assert empty_shifts_report_sent_at != schedule.empty_shifts_report_sent_at
    assert schedule.has_empty_shifts


@pytest.mark.django_db
def test_empty_non_empty_shifts_trigger_notification(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    user1 = make_user(organization=organization, username="user1")
    user2 = make_user(organization=organization, username="user2", role=LegacyAccessControlRole.VIEWER)
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_schedule",
        channel="channel",
        prev_ical_file_overrides=None,
        cached_ical_file_overrides=None,
    )
    # non-empty shift has higher priority
    now = timezone.now().replace(microsecond=0)
    start_date = now - datetime.timedelta(days=7, minutes=1)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": datetime.timedelta(seconds=3600 * 24),
        "priority_level": 2,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift_1 = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift_1.add_rolling_users([[user1]])

    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": datetime.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift_2 = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift_2.add_rolling_users([[user2]])
    schedule.refresh_ical_file()

    empty_shifts_report_sent_at = schedule.empty_shifts_report_sent_at

    with patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call") as mock_slack_api_call:
        notify_about_empty_shifts_in_schedule(schedule.pk)

    assert mock_slack_api_call.called

    schedule.refresh_from_db()
    assert empty_shifts_report_sent_at != schedule.empty_shifts_report_sent_at
    assert schedule.has_empty_shifts
