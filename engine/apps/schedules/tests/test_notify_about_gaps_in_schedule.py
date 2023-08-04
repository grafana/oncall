import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.schedules.ical_utils import memoized_users_in_ical
from apps.schedules.models import CustomOnCallShift, OnCallScheduleWeb
from apps.schedules.tasks import notify_about_gaps_in_schedule


@pytest.mark.django_db
def test_no_gaps_no_triggering_notification(
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

    gaps_report_sent_at = schedule.gaps_report_sent_at

    with patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call") as mock_slack_api_call:
        notify_about_gaps_in_schedule(schedule.pk)

    assert not mock_slack_api_call.called

    schedule.refresh_from_db()
    assert gaps_report_sent_at != schedule.gaps_report_sent_at
    assert schedule.check_gaps_for_next_week() is False


@pytest.mark.django_db
def test_gaps_in_the_past_no_triggering_notification(
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
    start_date_1 = now - datetime.timedelta(days=1, minutes=1)
    data = {
        "start": start_date_1,
        "rotation_start": start_date_1,
        "duration": datetime.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift_1 = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift_1.add_rolling_users([[user1]])

    start_date_2 = now - datetime.timedelta(days=5, minutes=1)
    until_date = start_date_2 + datetime.timedelta(days=3)
    data = {
        "start": start_date_2,
        "rotation_start": start_date_2,
        "duration": datetime.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
        "until": until_date,
    }
    on_call_shift_2 = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift_2.add_rolling_users([[user1]])
    schedule.refresh_ical_file()

    gaps_report_sent_at = schedule.gaps_report_sent_at

    with patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call") as mock_slack_api_call:
        notify_about_gaps_in_schedule(schedule.pk)

    assert not mock_slack_api_call.called

    schedule.refresh_from_db()
    assert gaps_report_sent_at != schedule.gaps_report_sent_at
    assert schedule.check_gaps_for_next_week() is False


@pytest.mark.django_db
def test_gaps_now_trigger_notification(
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

    gaps_report_sent_at = schedule.gaps_report_sent_at

    assert schedule.has_gaps is False

    with patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call") as mock_slack_api_call:
        notify_about_gaps_in_schedule(schedule.pk)

    assert mock_slack_api_call.called

    schedule.refresh_from_db()
    assert gaps_report_sent_at != schedule.gaps_report_sent_at
    assert schedule.has_gaps is True
    assert schedule.check_gaps_for_next_week() is True


@pytest.mark.django_db
def test_gaps_near_future_trigger_notification(
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
    until_date = now + datetime.timedelta(days=3)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": datetime.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
        "until": until_date,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user1]])
    schedule.refresh_ical_file()

    gaps_report_sent_at = schedule.gaps_report_sent_at

    assert schedule.has_gaps is False

    with patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call") as mock_slack_api_call:
        notify_about_gaps_in_schedule(schedule.pk)

    assert mock_slack_api_call.called

    schedule.refresh_from_db()
    assert gaps_report_sent_at != schedule.gaps_report_sent_at
    assert schedule.has_gaps is True
    assert schedule.check_gaps_for_next_week() is True


@pytest.mark.django_db
def test_gaps_later_than_7_days_no_triggering_notification(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    user1 = make_user(organization=organization, username="user1")
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    now = timezone.now().replace(microsecond=0)

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_schedule",
        channel="channel",
        prev_ical_file_overrides=None,
        cached_ical_file_overrides=None,
    )
    start_date = now - datetime.timedelta(days=7, minutes=1)
    until_date = now + datetime.timedelta(days=8)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": datetime.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
        "until": until_date,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user1]])
    schedule.refresh_ical_file()

    gaps_report_sent_at = schedule.gaps_report_sent_at

    with patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call") as mock_slack_api_call:
        notify_about_gaps_in_schedule(schedule.pk)

    assert not mock_slack_api_call.called

    schedule.refresh_from_db()
    assert gaps_report_sent_at != schedule.gaps_report_sent_at
    assert schedule.check_gaps_for_next_week() is False
