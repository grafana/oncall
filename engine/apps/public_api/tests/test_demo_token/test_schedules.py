import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.public_api import constants as public_api_constants
from apps.schedules.models import OnCallSchedule

demo_ical_schedule_payload = {
    "id": public_api_constants.DEMO_SCHEDULE_ID_ICAL,
    "team_id": None,
    "name": public_api_constants.DEMO_SCHEDULE_NAME_ICAL,
    "type": "ical",
    "ical_url_primary": public_api_constants.DEMO_SCHEDULE_ICAL_URL_PRIMARY,
    "ical_url_overrides": public_api_constants.DEMO_SCHEDULE_ICAL_URL_OVERRIDES,
    "on_call_now": [public_api_constants.DEMO_USER_ID],
    "slack": {
        "channel_id": public_api_constants.DEMO_SLACK_CHANNEL_SLACK_ID,
        "user_group_id": public_api_constants.DEMO_SLACK_USER_GROUP_SLACK_ID,
    },
}

demo_calendar_schedule_payload = {
    "id": public_api_constants.DEMO_SCHEDULE_ID_CALENDAR,
    "team_id": None,
    "name": public_api_constants.DEMO_SCHEDULE_NAME_CALENDAR,
    "type": "calendar",
    "time_zone": "America/New_york",
    "on_call_now": [public_api_constants.DEMO_USER_ID],
    "shifts": [
        public_api_constants.DEMO_ON_CALL_SHIFT_ID_1,
        public_api_constants.DEMO_ON_CALL_SHIFT_ID_2,
    ],
    "slack": {
        "channel_id": public_api_constants.DEMO_SLACK_CHANNEL_SLACK_ID,
        "user_group_id": public_api_constants.DEMO_SLACK_USER_GROUP_SLACK_ID,
    },
    "ical_url_overrides": None,
}

demo_schedules_payload = {
    "count": 2,
    "next": None,
    "previous": None,
    "results": [
        demo_ical_schedule_payload,
        demo_calendar_schedule_payload,
    ],
}


@pytest.mark.django_db
def test_get_schedule(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    schedule = OnCallSchedule.objects.get(public_primary_key=public_api_constants.DEMO_SCHEDULE_ID_ICAL)

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == demo_ical_schedule_payload


@pytest.mark.django_db
def test_create_schedule(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:schedules-list")

    data = {
        "name": "schedule test name",
        "type": "ical",
    }

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_201_CREATED
    # check that demo instance was returned
    assert response.data == demo_ical_schedule_payload


@pytest.mark.django_db
def test_update_ical_schedule(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    schedule = OnCallSchedule.objects.get(public_primary_key=public_api_constants.DEMO_SCHEDULE_ID_ICAL)

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    data = {
        "name": "NEW NAME",
    }

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    # check on nothing change
    schedule.refresh_from_db()
    assert schedule.name != data["name"]
    assert response.data == demo_ical_schedule_payload


@pytest.mark.django_db
def test_update_calendar_schedule(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    schedule = OnCallSchedule.objects.get(public_primary_key=public_api_constants.DEMO_SCHEDULE_ID_CALENDAR)

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    data = {
        "name": "NEW NAME",
    }

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    # check on nothing change
    schedule.refresh_from_db()
    assert schedule.name != data["name"]
    assert response.data == demo_calendar_schedule_payload


@pytest.mark.django_db
def test_delete_schedule(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    schedule = OnCallSchedule.objects.get(public_primary_key=public_api_constants.DEMO_SCHEDULE_ID_ICAL)

    url = reverse("api-public:schedules-detail", kwargs={"pk": schedule.public_primary_key})

    response = client.delete(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    # check on nothing change
    schedule.refresh_from_db()
    assert schedule is not None
