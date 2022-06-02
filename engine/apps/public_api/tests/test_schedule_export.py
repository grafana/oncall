import pytest
from django.urls import reverse
from icalendar import Calendar
from rest_framework import status
from rest_framework.test import APIClient

from apps.auth_token.models import ScheduleExportAuthToken, UserScheduleExportAuthToken
from apps.schedules.models import OnCallScheduleICal

ICAL_URL = "https://calendar.google.com/calendar/ical/c_6i1aprpgaqu89hqeelv7mrj264%40group.calendar.google.com/private-6a995cea6e74dd2cdc5d8c75bee06a2f/basic.ics"  # noqa


@pytest.mark.django_db
def test_export_calendar(make_organization_and_user_with_token, make_schedule):

    organization, user, _ = make_organization_and_user_with_token()

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        ical_url_primary=ICAL_URL,
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
    assert len(cal.subcomponents) == 2


@pytest.mark.django_db
def test_export_user_calendar(make_organization_and_user_with_token, make_schedule):

    organization, user, _ = make_organization_and_user_with_token()

    # make a schedule so that one is available
    make_schedule(
        organization,
        schedule_class=OnCallScheduleICal,
        name="test_ical_schedule",
        ical_url_primary=ICAL_URL,
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
