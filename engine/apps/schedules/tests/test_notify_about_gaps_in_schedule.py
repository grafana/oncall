import datetime
from unittest.mock import patch

import pytest
from django.utils import timezone

from apps.schedules.constants import SCHEDULE_CHECK_NEXT_DAYS
from apps.schedules.models import CustomOnCallShift, OnCallScheduleCalendar, OnCallScheduleICal, OnCallScheduleWeb
from apps.schedules.tasks import notify_about_gaps_in_schedule_task, start_notify_about_gaps_in_schedule


@pytest.mark.django_db
def test_no_gaps_no_triggering_notification(
    make_slack_team_identity,
    make_slack_channel,
    make_organization,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    slack_team_identity = make_slack_team_identity()
    slack_channel = make_slack_channel(slack_team_identity)
    organization = make_organization(slack_team_identity=slack_team_identity)
    user1 = make_user(organization=organization, username="user1")

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_schedule",
        slack_channel=slack_channel,
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

    with patch("apps.slack.client.SlackClient.chat_postMessage") as mock_slack_api_call:
        notify_about_gaps_in_schedule_task(schedule.pk)

    assert not mock_slack_api_call.called

    schedule.refresh_from_db()
    assert gaps_report_sent_at != schedule.gaps_report_sent_at
    assert schedule.has_gaps is False


@pytest.mark.django_db
def test_gaps_in_the_past_no_triggering_notification(
    make_slack_team_identity,
    make_slack_channel,
    make_organization,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    slack_team_identity = make_slack_team_identity()
    slack_channel = make_slack_channel(slack_team_identity)
    organization = make_organization(slack_team_identity=slack_team_identity)
    user1 = make_user(organization=organization, username="user1")

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_schedule",
        slack_channel=slack_channel,
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

    with patch("apps.slack.client.SlackClient.chat_postMessage") as mock_slack_api_call:
        notify_about_gaps_in_schedule_task(schedule.pk)

    assert not mock_slack_api_call.called

    schedule.refresh_from_db()
    assert gaps_report_sent_at != schedule.gaps_report_sent_at
    assert schedule.has_gaps is False


@pytest.mark.django_db
def test_gaps_now_trigger_notification(
    make_slack_team_identity,
    make_slack_channel,
    make_organization,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    slack_team_identity = make_slack_team_identity()
    slack_channel = make_slack_channel(slack_team_identity)
    organization = make_organization(slack_team_identity=slack_team_identity)
    user1 = make_user(organization=organization, username="user1")

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_schedule",
        slack_channel=slack_channel,
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

    with patch("apps.slack.client.SlackClient.chat_postMessage") as mock_slack_api_call:
        notify_about_gaps_in_schedule_task(schedule.pk)

    assert mock_slack_api_call.called

    schedule.refresh_from_db()
    assert gaps_report_sent_at != schedule.gaps_report_sent_at
    assert schedule.has_gaps is True


@pytest.mark.django_db
def test_gaps_near_future_trigger_notification(
    make_slack_team_identity,
    make_slack_channel,
    make_organization,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    slack_team_identity = make_slack_team_identity()
    slack_channel = make_slack_channel(slack_team_identity)
    organization = make_organization(slack_team_identity=slack_team_identity)
    user1 = make_user(organization=organization, username="user1")

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_schedule",
        slack_channel=slack_channel,
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

    with patch("apps.slack.client.SlackClient.chat_postMessage") as mock_slack_api_call:
        notify_about_gaps_in_schedule_task(schedule.pk)

    assert mock_slack_api_call.called

    schedule.refresh_from_db()
    assert gaps_report_sent_at != schedule.gaps_report_sent_at
    assert schedule.has_gaps is True


@pytest.mark.django_db
def test_gaps_later_than_days_no_triggering_notification(
    make_slack_team_identity,
    make_slack_channel,
    make_organization,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    slack_team_identity = make_slack_team_identity()
    slack_channel = make_slack_channel(slack_team_identity)
    organization = make_organization(slack_team_identity=slack_team_identity)
    user1 = make_user(organization=organization, username="user1")

    now = timezone.now().replace(microsecond=0)

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_schedule",
        slack_channel=slack_channel,
        prev_ical_file_overrides=None,
        cached_ical_file_overrides=None,
    )
    start_date = now - datetime.timedelta(days=SCHEDULE_CHECK_NEXT_DAYS, minutes=1)
    until_date = now + datetime.timedelta(days=SCHEDULE_CHECK_NEXT_DAYS + 1)
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

    with patch("apps.slack.client.SlackClient.chat_postMessage") as mock_slack_api_call:
        notify_about_gaps_in_schedule_task(schedule.pk)

    assert not mock_slack_api_call.called

    schedule.refresh_from_db()
    assert gaps_report_sent_at != schedule.gaps_report_sent_at
    assert schedule.has_gaps is False


@pytest.mark.parametrize(
    "schedule_class",
    [OnCallScheduleWeb, OnCallScheduleICal, OnCallScheduleCalendar],
)
@pytest.mark.parametrize(
    "report_sent_days_ago,expected_call",
    [(8, True), (6, False), (None, True)],
)
@pytest.mark.django_db
def test_start_notify_about_gaps(
    make_slack_team_identity,
    make_slack_channel,
    make_organization,
    make_schedule,
    schedule_class,
    report_sent_days_ago,
    expected_call,
):
    slack_team_identity = make_slack_team_identity()
    slack_channel = make_slack_channel(slack_team_identity)
    organization = make_organization(slack_team_identity=slack_team_identity)

    sent = timezone.now() - datetime.timedelta(days=report_sent_days_ago) if report_sent_days_ago else None
    schedule = make_schedule(
        organization,
        schedule_class=schedule_class,
        name="test_schedule",
        slack_channel=slack_channel,
        gaps_report_sent_at=sent,
    )

    with patch(
        "apps.schedules.tasks.notify_about_gaps_in_schedule.notify_about_gaps_in_schedule_task.apply_async"
    ) as mock_notify:
        start_notify_about_gaps_in_schedule()

    if expected_call:
        mock_notify.assert_called_once_with((schedule.pk,))
    else:
        mock_notify.assert_not_called()
