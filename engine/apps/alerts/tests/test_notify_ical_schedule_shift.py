import pytest

from apps.alerts.tasks.notify_ical_schedule_shift import notify_ical_schedule_shift
from apps.schedules.models import OnCallScheduleICal

ICAL_DATA = """
BEGIN:VCALENDAR
PRODID:-//Google Inc//Google Calendar 70.9054//EN
VERSION:2.0
CALSCALE:GREGORIAN
METHOD:PUBLISH
X-WR-CALNAME:t
X-WR-TIMEZONE:Asia/Yekaterinburg
BEGIN:VTIMEZONE
TZID:Asia/Yekaterinburg
X-LIC-LOCATION:Asia/Yekaterinburg
BEGIN:STANDARD
TZOFFSETFROM:+0500
TZOFFSETTO:+0500
TZNAME:+05
DTSTART:19700101T000000
END:STANDARD
END:VTIMEZONE
BEGIN:VEVENT
DTSTART;TZID=Asia/Yekaterinburg:20210124T130000
DTEND;TZID=Asia/Yekaterinburg:20210124T220000
RRULE:FREQ=DAILY
DTSTAMP:20210127T143634Z
UID:0i0af8p6p8vfampe3r1vkog0jg@google.com
CREATED:20210127T143553Z
DESCRIPTION:
LAST-MODIFIED:20210127T143553Z
LOCATION:
SEQUENCE:0
STATUS:CONFIRMED
SUMMARY:@Bernard Desruisseaux
TRANSP:OPAQUE
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
