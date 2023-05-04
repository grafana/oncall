import datetime
import textwrap
from uuid import uuid4

import pytest
import pytz
from django.utils import timezone

from apps.api.permissions import LegacyAccessControlRole
from apps.schedules.ical_utils import (
    is_icals_equal,
    list_of_oncall_shifts_from_ical,
    list_users_to_notify_from_ical,
    parse_event_uid,
    users_in_ical,
)
from apps.schedules.models import CustomOnCallShift, OnCallScheduleCalendar, OnCallScheduleWeb


@pytest.mark.django_db
def test_users_in_ical_email_case_insensitive(make_organization_and_user, make_user_for_organization):
    organization, user = make_organization_and_user()
    user = make_user_for_organization(organization, username="foo", email="TestingUser@test.com")

    usernames = ["testinguser@test.com"]
    result = users_in_ical(usernames, organization)
    assert set(result) == {user}


@pytest.mark.django_db
@pytest.mark.parametrize("include_viewers", [True, False])
def test_users_in_ical_viewers_inclusion(make_organization_and_user, make_user_for_organization, include_viewers):
    organization, user = make_organization_and_user()
    viewer = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)

    usernames = [user.username, viewer.username]
    result = users_in_ical(usernames, organization, include_viewers=include_viewers)
    if include_viewers:
        assert set(result) == {user, viewer}
    else:
        assert set(result) == {user}


@pytest.mark.django_db
@pytest.mark.parametrize("include_viewers", [True, False])
def test_list_users_to_notify_from_ical_viewers_inclusion(
    make_organization_and_user, make_user_for_organization, make_schedule, make_on_call_shift, include_viewers
):
    organization, user = make_organization_and_user()
    viewer = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    date = timezone.now().replace(tzinfo=None, microsecond=0)
    data = {
        "priority_level": 1,
        "start": date,
        "rotation_start": date,
        "duration": timezone.timedelta(seconds=10800),
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_SINGLE_EVENT, **data
    )
    on_call_shift.users.add(user)
    on_call_shift.users.add(viewer)
    schedule.custom_on_call_shifts.add(on_call_shift)

    # get users on-call
    date = date + timezone.timedelta(minutes=5)
    users_on_call = list_users_to_notify_from_ical(schedule, date, include_viewers=include_viewers)

    if include_viewers:
        assert len(users_on_call) == 2
        assert set(users_on_call) == {user, viewer}
    else:
        assert len(users_on_call) == 1
        assert set(users_on_call) == {user}


@pytest.mark.django_db
def test_list_users_to_notify_from_ical_until_terminated_event(
    make_organization_and_user, make_user_for_organization, make_schedule, make_on_call_shift
):
    organization, user = make_organization_and_user()
    other_user = make_user_for_organization(organization)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    date = timezone.now().replace(tzinfo=None, microsecond=0)

    data = {
        "start": date,
        "duration": timezone.timedelta(hours=4),
        "rotation_start": date + timezone.timedelta(days=3),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "by_day": ["SU"],
        "interval": 1,
        "until": date + timezone.timedelta(hours=8),
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user], [other_user]])

    # get users on-call
    date = date + timezone.timedelta(minutes=5)
    # this should not raise despite the shift configuration (until < rotation start)
    users_on_call = list_users_to_notify_from_ical(schedule, date)
    assert users_on_call == []


@pytest.mark.django_db
def test_shifts_dict_all_day_middle_event(make_organization, make_schedule, get_ical):
    calendar = get_ical("calendar_with_all_day_event.ics")
    organization = make_organization()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    schedule.cached_ical_file_primary = calendar.to_ical()

    day_to_check_iso = "2021-01-27T15:27:14.448059+00:00"
    parsed_iso_day_to_check = datetime.datetime.fromisoformat(day_to_check_iso).replace(tzinfo=pytz.UTC)
    requested_date = (parsed_iso_day_to_check - timezone.timedelta(days=1)).date()
    shifts = list_of_oncall_shifts_from_ical(schedule, requested_date, days=3, with_empty_shifts=True)
    assert len(shifts) == 5
    for s in shifts:
        start = s["start"].date() if isinstance(s["start"], datetime.datetime) else s["start"]
        end = s["end"].date() if isinstance(s["end"], datetime.datetime) else s["end"]
        # event started in the given period, or ended in that period, or is happening during the period
        assert (
            requested_date <= start <= requested_date + timezone.timedelta(days=3)
            or requested_date <= end <= requested_date + timezone.timedelta(days=3)
            or start <= requested_date <= end
        )


def test_parse_event_uid_v1():
    uuid = uuid4()
    event_uid = f"amixr-{uuid}-U1-E2-S1"
    pk, source = parse_event_uid(event_uid)
    assert pk is None
    assert source == "api"


def test_parse_event_uid_v2():
    uuid = uuid4()
    pk_value = "OABCDEF12345"
    event_uid = f"oncall-{uuid}-PK{pk_value}-U3-E1-S2"
    pk, source = parse_event_uid(event_uid)
    assert pk == pk_value
    assert source == "slack"


def test_parse_event_uid_fallback():
    # use ical existing UID for imported events
    event_uid = "someid@google.com"
    pk, source = parse_event_uid(event_uid)
    assert pk == event_uid
    assert source is None


def test_is_icals_equal_compare_events():
    with_vtimezone = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        PRODID:-//Google Inc//Google Calendar 70.9054//EN
        VERSION:2.0
        CALSCALE:GREGORIAN
        METHOD:PUBLISH
        X-WR-TIMEZONE:Europe/Amsterdam
        BEGIN:VTIMEZONE
        TZID:Europe/Amsterdam
        X-LIC-LOCATION:Europe/Amsterdam
        BEGIN:DAYLIGHT
        TZOFFSETFROM:+0100
        TZOFFSETTO:+0200
        TZNAME:CEST
        DTSTART:19700329T020000
        RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
        END:DAYLIGHT
        BEGIN:STANDARD
        TZOFFSETFROM:+0200
        TZOFFSETTO:+0100
        TZNAME:CET
        DTSTART:19701025T030000
        RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
        END:STANDARD
        END:VTIMEZONE
        BEGIN:VEVENT
        DTSTART;VALUE=DATE:20230515
        DTEND;VALUE=DATE:20230522
        DTSTAMP:20230503T152557Z
        UID:something@google.com
        RECURRENCE-ID;VALUE=DATE:20230501
        CREATED:20230403T073117Z
        LAST-MODIFIED:20230424T123617Z
        SEQUENCE:2
        STATUS:CONFIRMED
        SUMMARY:some@user.com
        END:VEVENT
        END:VCALENDAR
    """
    )
    without_vtimezone = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        PRODID:-//Google Inc//Google Calendar 70.9054//EN
        VERSION:2.0
        CALSCALE:GREGORIAN
        METHOD:PUBLISH
        X-WR-TIMEZONE:Europe/Amsterdam
        BEGIN:VEVENT
        DTSTART;VALUE=DATE:20230515
        DTEND;VALUE=DATE:20230522
        DTSTAMP:20230503T162103Z
        UID:something@google.com
        RECURRENCE-ID;VALUE=DATE:20230501
        CREATED:20230403T073117Z
        LAST-MODIFIED:20230424T123617Z
        SEQUENCE:2
        STATUS:CONFIRMED
        SUMMARY:some@user.com
        END:VEVENT
        END:VCALENDAR
    """
    )
    assert is_icals_equal(with_vtimezone, without_vtimezone)


def test_is_icals_equal_compare_events_not_equal():
    with_vtimezone = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        PRODID:-//Google Inc//Google Calendar 70.9054//EN
        VERSION:2.0
        CALSCALE:GREGORIAN
        METHOD:PUBLISH
        X-WR-TIMEZONE:Europe/Amsterdam
        BEGIN:VTIMEZONE
        TZID:Europe/Amsterdam
        X-LIC-LOCATION:Europe/Amsterdam
        BEGIN:DAYLIGHT
        TZOFFSETFROM:+0100
        TZOFFSETTO:+0200
        TZNAME:CEST
        DTSTART:19700329T020000
        RRULE:FREQ=YEARLY;BYMONTH=3;BYDAY=-1SU
        END:DAYLIGHT
        BEGIN:STANDARD
        TZOFFSETFROM:+0200
        TZOFFSETTO:+0100
        TZNAME:CET
        DTSTART:19701025T030000
        RRULE:FREQ=YEARLY;BYMONTH=10;BYDAY=-1SU
        END:STANDARD
        END:VTIMEZONE
        BEGIN:VEVENT
        DTSTART;VALUE=DATE:20230515
        DTEND;VALUE=DATE:20230522
        DTSTAMP:20230503T152557Z
        UID:something@google.com
        RECURRENCE-ID;VALUE=DATE:20230501
        CREATED:20230403T073117Z
        LAST-MODIFIED:20230424T123617Z
        SEQUENCE:2
        STATUS:CONFIRMED
        SUMMARY:some@user.com
        END:VEVENT
        END:VCALENDAR
    """
    )
    without_vtimezone = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        PRODID:-//Google Inc//Google Calendar 70.9054//EN
        VERSION:2.0
        CALSCALE:GREGORIAN
        METHOD:PUBLISH
        X-WR-TIMEZONE:Europe/Amsterdam
        BEGIN:VEVENT
        DTSTART;VALUE=DATE:20230515
        DTEND;VALUE=DATE:20230522
        DTSTAMP:20230503T162103Z
        UID:something@google.com
        RECURRENCE-ID;VALUE=DATE:20230501
        CREATED:20230403T073117Z
        LAST-MODIFIED:20230424T123617Z
        SEQUENCE:3
        STATUS:CONFIRMED
        SUMMARY:some@user.com
        END:VEVENT
        END:VCALENDAR
    """
    )
    assert not is_icals_equal(with_vtimezone, without_vtimezone)
