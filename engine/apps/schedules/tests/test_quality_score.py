import pytest
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from apps.schedules.ical_utils import memoized_users_in_ical
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
        # clear cache
        memoized_users_in_ical.cache_clear()

        calendar = get_ical("quality.ics")

        organization = make_organization()
        user1 = make_user_for_organization(organization, username="user1")
        _, token = make_token_for_organization(organization)
        user2 = make_user_for_organization(organization, username="user2")

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
            **make_user_auth_headers(user1, token),
        )
        return response, user1, user2

    return _get_schedule_quality_response


@pytest.mark.django_db
def test_get_schedule_score_no_events(get_schedule_quality_response):
    response, _, _ = get_schedule_quality_response("1999-01-01", 10)
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        "total_score": 0,
        "comments": [
            {"type": "warning", "text": "Schedule is empty"},
        ],
        "overloaded_users": [],
    }


@pytest.mark.django_db
def test_get_schedule_score_09_05(get_schedule_quality_response):
    response, user1, _ = get_schedule_quality_response("2022-09-05", 7)
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        "total_score": 28,
        "comments": [
            {"type": "warning", "text": "Schedule has gaps (79% not covered)"},
            {"type": "warning", "text": "Schedule has balance issues (see overloaded users)"},
        ],
        "overloaded_users": [
            {
                "id": user1.public_primary_key,
                "username": user1.username,
                "score": 49,
            },
        ],
    }


@pytest.mark.django_db
def test_get_schedule_score_09_09(get_schedule_quality_response):
    response, user1, user2 = get_schedule_quality_response("2022-09-09", 1)
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        "total_score": 51,
        "comments": [
            {"type": "warning", "text": "Schedule has gaps (81% not covered)"},
            {"type": "warning", "text": "Schedule has balance issues (see overloaded users)"},
        ],
        "overloaded_users": [
            {
                "id": user2.public_primary_key,
                "username": user2.username,
                "score": 9,
            },
        ],
    }


@pytest.mark.django_db
def test_get_schedule_score_09_12(get_schedule_quality_response):
    response, user1, _ = get_schedule_quality_response("2022-09-12", 4)
    assert response.status_code == status.HTTP_200_OK

    assert response.json() == {
        "total_score": 100,
        "comments": [
            {"type": "info", "text": "Schedule has no gaps"},
            {"type": "info", "text": "Schedule is perfectly balanced"},
        ],
        "overloaded_users": [],
    }


@pytest.mark.django_db
def test_get_schedule_score_09_19(get_schedule_quality_response):
    response, _, _ = get_schedule_quality_response("2022-09-19", 1)

    assert response.json() == {
        "total_score": 70,
        "comments": [
            {"type": "warning", "text": "Schedule has gaps (59% not covered)"},
            {"type": "info", "text": "Schedule is perfectly balanced"},
        ],
        "overloaded_users": [],
    }
