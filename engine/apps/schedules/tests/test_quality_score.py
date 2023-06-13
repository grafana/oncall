import datetime

import pytest
from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APIClient

from apps.schedules.ical_utils import memoized_users_in_ical
from apps.schedules.models import CustomOnCallShift, OnCallScheduleICal, OnCallScheduleWeb


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


@pytest.mark.django_db
def test_get_schedule_score_weekdays(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_schedule,
    make_on_call_shift,
    make_user_auth_headers,
):
    organization = make_organization()
    _, token = make_token_for_organization(organization)

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_quality",
    )

    users = [make_user_for_organization(organization, username=f"user-{idx}") for idx in range(8)]
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        start=datetime.datetime(2022, 3, 20, 0, 0, 0, tzinfo=datetime.timezone.utc),
        duration=datetime.timedelta(hours=12),
        rotation_start=datetime.datetime(2022, 3, 20, 0, 0, 0, tzinfo=datetime.timezone.utc),
        until=None,
        rolling_users=[{user.pk: user.public_primary_key for user in users[:4]}],
        frequency=CustomOnCallShift.FREQUENCY_WEEKLY,
        by_day=["MO", "TU", "WE", "TH", "FR"],
    )

    make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        start=datetime.datetime(2022, 3, 20, 12, 0, 0, tzinfo=datetime.timezone.utc),
        duration=datetime.timedelta(hours=12),
        rotation_start=datetime.datetime(2022, 3, 20, 12, 0, 0, tzinfo=datetime.timezone.utc),
        until=None,
        rolling_users=[{user.pk: user.public_primary_key for user in users[4:]}],
        frequency=CustomOnCallShift.FREQUENCY_WEEKLY,
        by_day=["MO", "TU", "WE", "TH", "FR"],
    )

    client = APIClient()

    url = reverse("api-internal:schedule-quality", kwargs={"pk": schedule.public_primary_key}) + "?date=2022-03-24"
    response = client.get(url, **make_user_auth_headers(users[0], token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "total_score": 86,
        "comments": [
            {"type": "warning", "text": "Schedule has gaps (29% not covered)"},
            {"type": "info", "text": "Schedule is perfectly balanced"},
        ],
        "overloaded_users": [],
    }


@pytest.mark.django_db
def test_get_schedule_score_all_week(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_schedule,
    make_on_call_shift,
    make_user_auth_headers,
):
    organization = make_organization()
    _, token = make_token_for_organization(organization)

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_quality",
    )

    users = [make_user_for_organization(organization, username=f"user-{idx}") for idx in range(8)]
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        start=datetime.datetime(2022, 3, 20, 0, 0, 0, tzinfo=datetime.timezone.utc),
        duration=datetime.timedelta(hours=12),
        rotation_start=datetime.datetime(2022, 3, 20, 0, 0, 0, tzinfo=datetime.timezone.utc),
        until=None,
        rolling_users=[{user.pk: user.public_primary_key for user in users[:4]}],
        frequency=CustomOnCallShift.FREQUENCY_WEEKLY,
        by_day=["MO", "TU", "WE", "TH", "FR"],
    )

    make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        start=datetime.datetime(2022, 3, 20, 12, 0, 0, tzinfo=datetime.timezone.utc),
        duration=datetime.timedelta(hours=12),
        rotation_start=datetime.datetime(2022, 3, 20, 12, 0, 0, tzinfo=datetime.timezone.utc),
        until=None,
        rolling_users=[{user.pk: user.public_primary_key for user in users[4:]}],
        frequency=CustomOnCallShift.FREQUENCY_WEEKLY,
        by_day=["MO", "TU", "WE", "TH", "FR"],
    )

    make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        start=datetime.datetime(2022, 3, 20, 12, 0, 0, tzinfo=datetime.timezone.utc),
        duration=datetime.timedelta(hours=24),
        rotation_start=datetime.datetime(2022, 3, 20, 12, 0, 0, tzinfo=datetime.timezone.utc),
        until=None,
        rolling_users=[{user.pk: user.public_primary_key for user in users}],
        frequency=CustomOnCallShift.FREQUENCY_WEEKLY,
        by_day=["SA", "SU"],
    )

    client = APIClient()

    url = reverse("api-internal:schedule-quality", kwargs={"pk": schedule.public_primary_key}) + "?date=2022-03-24"
    response = client.get(url, **make_user_auth_headers(users[0], token))

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
def test_get_schedule_score_all_week_imbalanced_weekends(
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_schedule,
    make_on_call_shift,
    make_user_auth_headers,
):
    organization = make_organization()
    _, token = make_token_for_organization(organization)

    schedule = make_schedule(
        organization,
        schedule_class=OnCallScheduleWeb,
        name="test_quality",
    )

    users = [make_user_for_organization(organization, username=f"user-{idx}") for idx in range(8)]
    # clear users pks <-> organization cache (persisting between tests)
    memoized_users_in_ical.cache_clear()

    make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        start=datetime.datetime(2022, 3, 20, 0, 0, 0, tzinfo=datetime.timezone.utc),
        duration=datetime.timedelta(hours=12),
        rotation_start=datetime.datetime(2022, 3, 20, 0, 0, 0, tzinfo=datetime.timezone.utc),
        until=None,
        rolling_users=[{user.pk: user.public_primary_key for user in users[:4]}],
        frequency=CustomOnCallShift.FREQUENCY_WEEKLY,
        by_day=["MO", "TU", "WE", "TH", "FR"],
    )

    make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        start=datetime.datetime(2022, 3, 20, 12, 0, 0, tzinfo=datetime.timezone.utc),
        duration=datetime.timedelta(hours=12),
        rotation_start=datetime.datetime(2022, 3, 20, 12, 0, 0, tzinfo=datetime.timezone.utc),
        until=None,
        rolling_users=[{user.pk: user.public_primary_key for user in users[4:]}],
        frequency=CustomOnCallShift.FREQUENCY_WEEKLY,
        by_day=["MO", "TU", "WE", "TH", "FR"],
    )

    make_on_call_shift(
        schedule.organization,
        shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
        schedule=schedule,
        start=datetime.datetime(2022, 3, 20, 12, 0, 0, tzinfo=datetime.timezone.utc),
        duration=datetime.timedelta(hours=24),
        rotation_start=datetime.datetime(2022, 3, 20, 12, 0, 0, tzinfo=datetime.timezone.utc),
        until=None,
        rolling_users=[{user.pk: user.public_primary_key for user in users[:4]}],
        frequency=CustomOnCallShift.FREQUENCY_WEEKLY,
        by_day=["SA", "SU"],
    )

    client = APIClient()

    url = reverse("api-internal:schedule-quality", kwargs={"pk": schedule.public_primary_key}) + "?date=2022-03-24"
    response = client.get(url, **make_user_auth_headers(users[0], token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "total_score": 88,
        "comments": [
            {"type": "info", "text": "Schedule has no gaps"},
            {"type": "warning", "text": "Schedule has balance issues (see overloaded users)"},
        ],
        "overloaded_users": [
            {
                "id": user.public_primary_key,
                "username": user.username,
                "score": 29,
            }
            for user in users[:4]
        ],
    }
