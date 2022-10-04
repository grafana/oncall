from datetime import datetime
from unittest.mock import Mock, patch

import pytest
import pytz
from django.utils import timezone

from apps.alerts.tasks.notify_ical_schedule_shift import notify_ical_schedule_shift
from apps.schedules.models import OnCallScheduleICal

ICAL_DATA = """
BEGIN:VCALENDAR
PRODID:-//Google Inc//Google Calendar 70.9054//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
BEGIN:VEVENT
DTSTART;VALUE=DATE:20211005
DTEND;VALUE=DATE:20211012
RRULE:FREQ=WEEKLY;WKST=SU;INTERVAL=7;BYDAY=WE
DTSTAMP:20210930T125523Z
UID:id1@google.com
CREATED:20210928T202349Z
DESCRIPTION:
LAST-MODIFIED:20210929T204751Z
LOCATION:
SEQUENCE:1
STATUS:CONFIRMED
SUMMARY:user1
TRANSP:TRANSPARENT
END:VEVENT
BEGIN:VEVENT
DTSTART;VALUE=DATE:20210928
DTEND;VALUE=DATE:20211005
RRULE:FREQ=WEEKLY;WKST=SU;INTERVAL=7;BYDAY=WE
DTSTAMP:20210930T125523Z
UID:id2@google.com
CREATED:20210928T202331Z
DESCRIPTION:
LAST-MODIFIED:20210929T204744Z
LOCATION:
SEQUENCE:2
STATUS:CONFIRMED
SUMMARY:user2
TRANSP:TRANSPARENT
END:VEVENT
END:VCALENDAR
"""


@pytest.mark.django_db
def test_current_overrides_ical_schedule_is_none(
    make_organization_and_user_with_slack_identities,
    make_schedule,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()

    ical_schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        channel="channel",
        ical_url_primary="url",
        prev_ical_file_primary=ICAL_DATA,
        cached_ical_file_primary=ICAL_DATA,
        prev_ical_file_overrides=ICAL_DATA,
        cached_ical_file_overrides=None,
    )

    # this should not raise
    notify_ical_schedule_shift(ical_schedule.oncallschedule_ptr_id)


@pytest.mark.django_db
def test_next_shift_notification_long_shifts(
    make_organization_and_user_with_slack_identities,
    make_schedule,
    make_user,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    make_user(organization=organization, username="user1")
    make_user(organization=organization, username="user2")

    ical_schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        channel="channel",
        ical_url_primary="url",
        prev_ical_file_primary=ICAL_DATA,
        cached_ical_file_primary=ICAL_DATA,
        prev_ical_file_overrides=None,
        cached_ical_file_overrides=None,
    )

    with patch.object(timezone, "datetime", Mock(wraps=timezone.datetime)) as mock_tz_datetime:
        mock_tz_datetime.now.return_value = datetime(2021, 9, 29, 12, 0, tzinfo=pytz.UTC)
        with patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call") as mock_slack_api_call:
            notify_ical_schedule_shift(ical_schedule.oncallschedule_ptr_id)

    slack_blocks = mock_slack_api_call.call_args_list[0][1]["blocks"]
    notification = slack_blocks[0]["text"]["text"]
    assert "*New on-call shift:*\nuser2" in notification
    assert "*Next on-call shift:*\nuser1" in notification
