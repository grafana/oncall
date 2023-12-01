import pytest
from django.urls import reverse
from icalendar import Calendar
from rest_framework import status
from rest_framework.test import APIClient

from apps.auth_token.models import ScheduleExportAuthToken, UserScheduleExportAuthToken
from apps.schedules.constants import ICAL_COMPONENT_VEVENT, ICAL_SUMMARY
from apps.schedules.models import OnCallScheduleICal

ICAL_DATA = """
BEGIN:VCALENDAR
PRODID://Grafana Labs//Grafana On-Call//
CALSCALE:GREGORIAN
X-WR-CALNAME:test_ical_schedule
X-WR-TIMEZONE:UTC
BEGIN:VEVENT
SUMMARY:justin.hunthrop@grafana.com
DTSTART;TZID=America/Chicago:20211015T000000
DTEND;TZID=America/Chicago:20211015T120000
DTSTAMP:20230223T144743Z
UID:03vjiku070po61a9t8t7ln9q4o@google.com
SEQUENCE:1
RRULE:FREQ=DAILY
CREATED:20211015T013834Z
DESCRIPTION:
LAST-MODIFIED:20211015T142118Z
LOCATION:
STATUS:CONFIRMED
TRANSP:TRANSPARENT
END:VEVENT
BEGIN:VEVENT
SUMMARY:amixr
DTSTART;TZID=America/Chicago:20211015T120000
DTEND;TZID=America/Chicago:20211016T000000
DTSTAMP:20230223T144743Z
UID:0g1cuqi56qtaqvgb38crsh0mpa@google.com
SEQUENCE:1
RRULE:FREQ=DAILY
CREATED:20211015T020105Z
DESCRIPTION:
LAST-MODIFIED:20211015T140758Z
LOCATION:
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT
END:VCALENDAR
"""


@pytest.mark.django_db
def test_export_calendar(make_organization_and_user_with_token, make_user_for_organization, make_schedule):
    organization, user, _ = make_organization_and_user_with_token()
    usernames = {"amixr", "justin.hunthrop@grafana.com"}
    # setup users for shifts
    for u in usernames:
        make_user_for_organization(organization, username=u)

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        cached_ical_file_primary=ICAL_DATA,
    )
    _, schedule_token = ScheduleExportAuthToken.create_auth_token(
        user=user, organization=organization, schedule=schedule
    )

    client = APIClient()

    url = reverse("api-public:schedules-export", kwargs={"pk": schedule.public_primary_key})
    url = url + "?token={0}".format(schedule_token)

    response = client.get(url, format="text/calendar")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "text/calendar; charset=utf-8"

    cal = Calendar.from_ical(response.data)

    assert type(cal) == Calendar
    # check there are events
    assert len(cal.subcomponents) > 0
    for component in cal.walk():
        if component.name == ICAL_COMPONENT_VEVENT:
            assert component[ICAL_SUMMARY] in usernames


@pytest.mark.django_db
def test_export_user_calendar(make_organization_and_user_with_token, make_schedule):
    organization, user, _ = make_organization_and_user_with_token()

    # make a schedule so that one is available
    make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        cached_ical_file_primary=ICAL_DATA,
    )

    _, schedule_token = UserScheduleExportAuthToken.create_auth_token(user=user, organization=organization)

    url = reverse("api-public:users-schedule-export", kwargs={"pk": user.public_primary_key})
    url = url + "?token={0}".format(schedule_token)

    client = APIClient()

    response = client.get(url, format="text/calendar")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "text/calendar; charset=utf-8"

    cal = Calendar.from_ical(response.data)

    assert type(cal) == Calendar
    assert cal.get("x-wr-calname") == "On-Call Schedule for {0}".format(user.username)
    assert cal.get("x-wr-timezone") == "UTC"
    assert cal.get("calscale") == "GREGORIAN"
    assert cal.get("prodid") == "//Grafana Labs//Grafana On-Call//"
