import datetime
import textwrap
from uuid import uuid4

import icalendar
import pytest
import pytz
from django.utils import timezone

from apps.api.permissions import LegacyAccessControlRole
from apps.schedules.ical_utils import (
    get_icalendar_tz_or_utc,
    is_icals_equal,
    list_of_oncall_shifts_from_ical,
    list_users_to_notify_from_ical,
    parse_event_uid,
    users_in_ical,
)
from apps.schedules.models import (
    CustomOnCallShift,
    OnCallSchedule,
    OnCallScheduleCalendar,
    OnCallScheduleICal,
    OnCallScheduleWeb,
)


def test_get_icalendar_tz_or_utc():
    ical_data = textwrap.dedent(
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
        END:VCALENDAR
    """
    )
    ical = icalendar.Calendar.from_ical(ical_data)
    tz = get_icalendar_tz_or_utc(ical)
    assert tz == pytz.timezone("Europe/London")


def test_get_icalendar_tz_or_utc_fallback():
    ical_data = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        PRODID:-//Google Inc//Google Calendar 70.9054//EN
        VERSION:2.0
        CALSCALE:GREGORIAN
        METHOD:PUBLISH
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
        END:VCALENDAR
    """
    )
    ical = icalendar.Calendar.from_ical(ical_data)
    tz = get_icalendar_tz_or_utc(ical)
    assert tz == pytz.timezone("UTC")


@pytest.mark.django_db
def test_users_in_ical_email_case_insensitive(make_organization_and_user, make_user_for_organization):
    organization, user = make_organization_and_user()
    user = make_user_for_organization(organization, username="foo", email="TestingUser@test.com")

    usernames = ["testinguser@test.com"]
    result = users_in_ical(usernames, organization)
    assert set(result) == {user}


@pytest.mark.django_db
def test_users_in_ical_viewers_inclusion(make_organization_and_user, make_user_for_organization):
    organization, user = make_organization_and_user()
    viewer = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)

    usernames = [user.username, viewer.username]
    result = users_in_ical(usernames, organization)
    assert set(result) == {user}


@pytest.mark.django_db
def test_list_users_to_notify_from_ical_viewers_inclusion(
    make_organization_and_user, make_user_for_organization, make_schedule, make_on_call_shift
):
    organization, user = make_organization_and_user()
    viewer = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    date = timezone.now().replace(microsecond=0)
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
    users_on_call = list_users_to_notify_from_ical(schedule, date)

    assert len(users_on_call) == 1
    assert set(users_on_call) == {user}


@pytest.mark.django_db
def test_list_users_to_notify_from_ical_ignore_cancelled(make_organization_and_user, make_schedule):
    organization, user = make_organization_and_user()
    now = timezone.now().replace(second=0, microsecond=0)
    end = now + timezone.timedelta(minutes=30)
    ical_data = textwrap.dedent(
        """
        BEGIN:VCALENDAR
        VERSION:2.0
        CALSCALE:GREGORIAN
        METHOD:PUBLISH
        BEGIN:VEVENT
        SUMMARY:{}
        DTSTART;VALUE=DATE-TIME:{}
        DTEND;VALUE=DATE-TIME:{}
        DTSTAMP;VALUE=DATE-TIME:20230807T001508Z
        UID:some-uid
        LOCATION:primary
        STATUS:CANCELLED
        END:VEVENT
        END:VCALENDAR
    """.format(
            user.username, now.strftime("%Y%m%dT%H%M%SZ"), end.strftime("%Y%m%dT%H%M%SZ")
        )
    )
    schedule = make_schedule(organization, schedule_class=OnCallScheduleICal, cached_ical_file_primary=ical_data)

    # get users on-call
    users_on_call = list_users_to_notify_from_ical(schedule, now + timezone.timedelta(minutes=5))
    assert len(users_on_call) == 0


@pytest.mark.django_db
def test_list_users_to_notify_from_ical_until_terminated_event(
    make_organization_and_user, make_user_for_organization, make_schedule, make_on_call_shift
):
    organization, user = make_organization_and_user()
    other_user = make_user_for_organization(organization)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    date = timezone.now().replace(microsecond=0)

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
    assert list(users_on_call) == []


@pytest.mark.django_db
def test_list_users_to_notify_from_ical_overlapping_events(
    make_organization_and_user, make_user_for_organization, make_schedule, make_on_call_shift
):
    organization, user = make_organization_and_user()
    another_user = make_user_for_organization(organization)

    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    start = timezone.now() - timezone.timedelta(hours=1)
    data = {
        "start": start,
        "rotation_start": start,
        "duration": timezone.timedelta(hours=3),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[user]])

    data = {
        "start": start + timezone.timedelta(minutes=30),
        "rotation_start": start + timezone.timedelta(minutes=30),
        "duration": timezone.timedelta(hours=2),
        "priority_level": 2,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[another_user]])

    # get users on-call now
    users_on_call = list_users_to_notify_from_ical(schedule)

    assert len(users_on_call) == 1
    assert set(users_on_call) == {another_user}


@pytest.mark.django_db
def test_shifts_dict_all_day_middle_event(make_organization, make_schedule, get_ical):
    calendar = get_ical("calendar_with_all_day_event.ics")
    organization = make_organization()
    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar)
    schedule.cached_ical_file_primary = calendar.to_ical()

    day_to_check_iso = "2021-01-27T15:27:14.448059+00:00"
    parsed_iso_day_to_check = datetime.datetime.fromisoformat(day_to_check_iso).replace(tzinfo=pytz.UTC)
    requested_datetime = parsed_iso_day_to_check - timezone.timedelta(days=1)
    datetime_end = requested_datetime + timezone.timedelta(days=2)
    shifts = list_of_oncall_shifts_from_ical(schedule, requested_datetime, datetime_end, with_empty_shifts=True)
    assert len(shifts) == 5
    for s in shifts:
        start = (
            s["start"]
            if isinstance(s["start"], datetime.datetime)
            else datetime.datetime.combine(s["start"], datetime.time.min, tzinfo=pytz.UTC)
        )
        end = (
            s["end"]
            if isinstance(s["end"], datetime.datetime)
            else datetime.datetime.combine(s["start"], datetime.time.max, tzinfo=pytz.UTC)
        )
        # event started in the given period, or ended in that period, or is happening during the period
        assert (
            requested_datetime <= start <= requested_datetime + timezone.timedelta(days=2)
            or requested_datetime <= end <= requested_datetime + timezone.timedelta(days=2)
            or start <= requested_datetime <= end
        )


@pytest.mark.django_db
def test_shifts_dict_from_cached_final(
    make_organization,
    make_user_for_organization,
    make_schedule,
    make_on_call_shift,
):
    organization = make_organization()
    u1 = make_user_for_organization(organization)

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timezone.timedelta(days=1)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)
    data = {
        "start": yesterday + timezone.timedelta(hours=10),
        "rotation_start": yesterday + timezone.timedelta(hours=10),
        "duration": timezone.timedelta(hours=2),
        "priority_level": 1,
        "frequency": CustomOnCallShift.FREQUENCY_DAILY,
        "schedule": schedule,
    }
    on_call_shift = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT, **data
    )
    on_call_shift.add_rolling_users([[u1]])

    override_data = {
        "start": yesterday + timezone.timedelta(hours=12),
        "rotation_start": yesterday + timezone.timedelta(hours=12),
        "duration": timezone.timedelta(hours=1),
        "schedule": schedule,
    }
    override = make_on_call_shift(
        organization=organization, shift_type=CustomOnCallShift.TYPE_OVERRIDE, **override_data
    )
    override.add_rolling_users([[u1]])
    schedule.refresh_ical_file()
    schedule.refresh_ical_final_schedule()

    shifts = [
        (s["calendar_type"], s["start"], list(s["users"]))
        for s in list_of_oncall_shifts_from_ical(schedule, yesterday, today, from_cached_final=True)
    ]
    expected_events = [
        (OnCallSchedule.PRIMARY, on_call_shift.start, [u1]),
        (OnCallSchedule.OVERRIDES, override.start, [u1]),
    ]
    assert shifts == expected_events


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


def test_parse_recurrent_event_uid_fallback_modified():
    # use ical existing UID for imported events
    event_uid = "someid@google.com"
    pk, source = parse_event_uid(event_uid, sequence="2")
    assert pk == f"{event_uid}_2"
    assert source is None
    pk, source = parse_event_uid(event_uid, recurrence_id="other-id")
    assert pk == f"{event_uid}_other-id"
    assert source is None
    pk, source = parse_event_uid(event_uid, sequence="3", recurrence_id="other-id")
    assert pk == f"{event_uid}_3_other-id"
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
