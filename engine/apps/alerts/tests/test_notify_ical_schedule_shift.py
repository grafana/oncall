import json
import textwrap
from datetime import datetime
from unittest.mock import Mock, patch

import icalendar
import pytest
import pytz
from django.utils import timezone

from apps.alerts.tasks.notify_ical_schedule_shift import get_current_shifts_from_ical, notify_ical_schedule_shift
from apps.schedules.ical_utils import memoized_users_in_ical
from apps.schedules.models import CustomOnCallShift, OnCallScheduleCalendar, OnCallScheduleICal

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
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

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


@pytest.mark.django_db
def test_overrides_changes_no_current_no_triggering_notification(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_schedule,
    make_on_call_shift,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    user1 = make_user(organization=organization, username="user1")
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    ical_before = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        PRODID:-//Google Inc//Google Calendar 70.9054//EN
        VERSION:2.0
        CALSCALE:GREGORIAN
        METHOD:PUBLISH
        BEGIN:VEVENT
        DTSTART:20230101T020000
        DTEND:20230101T170000
        DTSTAMP:20230101T000000
        UID:id1@google.com
        CREATED:20230101T000000
        DESCRIPTION:
        LAST-MODIFIED:20230101T000000
        LOCATION:
        SEQUENCE:1
        STATUS:CONFIRMED
        SUMMARY:user1
        TRANSP:TRANSPARENT
        END:VEVENT
        END:VCALENDAR"""
    )

    # event outside current time is changed
    ical_after = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        PRODID:-//Google Inc//Google Calendar 70.9054//EN
        VERSION:2.0
        CALSCALE:GREGORIAN
        METHOD:PUBLISH
        BEGIN:VEVENT
        DTSTART:20230101T020000
        DTEND:20230101T210000
        DTSTAMP:20230101T000000
        UID:id1@google.com
        CREATED:20230101T000000
        DESCRIPTION:
        LAST-MODIFIED:20230101T000000
        LOCATION:
        SEQUENCE:2
        STATUS:CONFIRMED
        SUMMARY:user1
        TRANSP:TRANSPARENT
        END:VEVENT
        END:VCALENDAR"""
    )

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleCalendar,
        name="test_schedule",
        channel="channel",
        prev_ical_file_overrides=ical_before,
        cached_ical_file_overrides=ical_after,
    )

    now = timezone.now().replace(microsecond=0)
    start_date = now - timezone.timedelta(days=7)

    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user1]])
    on_call_shift.schedules.add(schedule)

    # setup current shifts before checking/triggering for notifications
    calendar = icalendar.Calendar.from_ical(schedule._ical_file_primary)
    current_shifts, _ = get_current_shifts_from_ical(calendar, schedule, 0)
    schedule.current_shifts = json.dumps(current_shifts, default=str)
    schedule.empty_oncall = False
    schedule.save()

    with patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call") as mock_slack_api_call:
        notify_ical_schedule_shift(schedule.oncallschedule_ptr_id)

    assert not mock_slack_api_call.called


@pytest.mark.django_db
def test_no_changes_no_triggering_notification(
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
        schedule_class=OnCallScheduleCalendar,
        name="test_schedule",
        channel="channel",
        prev_ical_file_overrides=None,
        cached_ical_file_overrides=None,
    )

    now = timezone.now().replace(microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user1]])
    on_call_shift.schedules.add(schedule)

    # setup current shifts before checking/triggering for notifications
    calendar = icalendar.Calendar.from_ical(schedule._ical_file_primary)
    current_shifts, _ = get_current_shifts_from_ical(calendar, schedule, 0)
    schedule.current_shifts = json.dumps(current_shifts, default=str)
    schedule.empty_oncall = False
    schedule.save()

    with patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call") as mock_slack_api_call:
        notify_ical_schedule_shift(schedule.oncallschedule_ptr_id)

    assert not mock_slack_api_call.called


@pytest.mark.django_db
def test_current_shift_changes_trigger_notification(
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
        schedule_class=OnCallScheduleCalendar,
        name="test_schedule",
        channel="channel",
        prev_ical_file_overrides=None,
        cached_ical_file_overrides=None,
    )

    now = timezone.now().replace(microsecond=0)
    start_date = now - timezone.timedelta(days=7)
    data = {
        "start": start_date,
        "rotation_start": start_date,
        "duration": timezone.timedelta(seconds=3600 * 24),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user1]])
    on_call_shift.schedules.add(schedule)
    schedule.refresh_ical_file()

    # setup empty current shifts before checking/triggering for notifications
    schedule.current_shifts = json.dumps({}, default=str)
    schedule.empty_oncall = False
    schedule.save()

    with patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call") as mock_slack_api_call:
        notify_ical_schedule_shift(schedule.oncallschedule_ptr_id)

    assert mock_slack_api_call.called


@pytest.mark.django_db
def test_vtimezone_changes_no_triggering_notification(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_schedule,
):
    organization, _, _, _ = make_organization_and_user_with_slack_identities()
    make_user(organization=organization, username="user1")
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    ical_before = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        PRODID:-//Google Inc//Google Calendar 70.9054//EN
        VERSION:2.0
        CALSCALE:GREGORIAN
        X-WR-TIMEZONE:Europe/London
        METHOD:PUBLISH
        BEGIN:VTIMEZONE
        TZID:Europe/Rome
        BEGIN:STANDARD
        TZOFFSETFROM:0200
        TZOFFSETTO:0100
        TZNAME:CET
        DTSTART:19701025T030000
        END:STANDARD
        END:VTIMEZONE
        BEGIN:VTIMEZONE
        TZID:America/Argentina/Buenos_Aires
        X-LIC-LOCATION:America/Argentina/Buenos_Aires
        BEGIN:STANDARD
        TZOFFSETFROM:-0300
        TZOFFSETTO:-0300
        TZNAME:-03
        DTSTART:19700101T000000
        END:STANDARD
        END:VTIMEZONE
        BEGIN:VEVENT
        DTSTART;VALUE=DATE:20230101
        DTEND;VALUE=DATE:20230102
        RRULE:FREQ=DAILY
        DTSTAMP:20230101T000000
        UID:id1@google.com
        CREATED:20230101T000000
        DESCRIPTION:
        LAST-MODIFIED:20230101T000000
        LOCATION:
        SEQUENCE:1
        STATUS:CONFIRMED
        SUMMARY:user1
        TRANSP:TRANSPARENT
        END:VEVENT
        END:VCALENDAR"""
    )

    # same data, timezones in different order (eg. google usually randomly reorders them)
    ical_after = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        PRODID:-//Google Inc//Google Calendar 70.9054//EN
        VERSION:2.0
        CALSCALE:GREGORIAN
        METHOD:PUBLISH
        X-WR-TIMEZONE:Europe/London
        BEGIN:VTIMEZONE
        TZID:America/Argentina/Buenos_Aires
        X-LIC-LOCATION:America/Argentina/Buenos_Aires
        BEGIN:STANDARD
        TZOFFSETFROM:-0300
        TZOFFSETTO:-0300
        TZNAME:-03
        DTSTART:19700101T000000
        END:STANDARD
        END:VTIMEZONE
        BEGIN:VTIMEZONE
        TZID:Europe/Rome
        BEGIN:STANDARD
        TZOFFSETFROM:0200
        TZOFFSETTO:0100
        TZNAME:CET
        DTSTART:19701025T030000
        END:STANDARD
        END:VTIMEZONE
        BEGIN:VEVENT
        DTSTART;VALUE=DATE:20230101
        DTEND;VALUE=DATE:20230102
        RRULE:FREQ=DAILY
        DTSTAMP:20230101T000000
        UID:id1@google.com
        CREATED:20230101T000000
        DESCRIPTION:
        LAST-MODIFIED:20230101T000000
        LOCATION:
        SEQUENCE:1
        STATUS:CONFIRMED
        SUMMARY:user1
        TRANSP:TRANSPARENT
        END:VEVENT
        END:VCALENDAR"""
    )

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        channel="channel",
        ical_url_primary="url",
        prev_ical_file_primary=ical_before,
        cached_ical_file_primary=ical_after,
        prev_ical_file_overrides=None,
        cached_ical_file_overrides=None,
    )

    # setup current shifts before checking/triggering for notifications
    calendar = icalendar.Calendar.from_ical(ical_before)
    current_shifts, _ = get_current_shifts_from_ical(calendar, schedule, 0)
    schedule.current_shifts = json.dumps(current_shifts, default=str)
    schedule.empty_oncall = False
    schedule.save()

    with patch("apps.slack.slack_client.SlackClientWithErrorHandling.api_call") as mock_slack_api_call:
        notify_ical_schedule_shift(schedule.oncallschedule_ptr_id)

    assert not mock_slack_api_call.called
