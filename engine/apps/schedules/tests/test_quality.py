import pytest
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from apps.schedules.models import OnCallScheduleICal


@pytest.fixture
def get_schedule_quality_response(
    get_ical,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_schedule,
    make_user_auth_headers,
):
    def _get_schedule_quality_response(date, days):
        calendar = get_ical("quality.ics")

        organization = make_organization()
        user = make_user_for_organization(organization, username="user1")
        _, token = make_token_for_organization(organization)
        make_user_for_organization(organization, username="user2")

        schedule = make_schedule(
            organization,
            schedule_class=OnCallScheduleICal,
            name="test_quality",
            cached_ical_file_primary=calendar.to_ical().decode(),
        )

        client = APIClient()

        url = reverse("api-internal:schedule-quality", kwargs={"pk": schedule.public_primary_key})
        response = client.get(
            url + f"?date={date}&days={days}",
            **make_user_auth_headers(user, token),
        )
        return response

    return _get_schedule_quality_response


def get_score_values(response):
    scores = [score["value"] for score in response.json()["scores"]]
    return scores + [response.json()["total_score"]]


@pytest.mark.django_db
def test_get_schedule_score_no_events(get_schedule_quality_response):
    response = get_schedule_quality_response("1999-01-01", 10)
    assert response.status_code == status.HTTP_200_OK

    scores = get_score_values(response)
    assert scores == [0, 100, 100, 100, 50]


@pytest.mark.django_db
def test_get_schedule_score_1(get_schedule_quality_response):
    response = get_schedule_quality_response("2022-09-19", 1)
    assert response.status_code == status.HTTP_200_OK

    scores = get_score_values(response)
    assert scores == [41, 31, 100, 100, 59]
