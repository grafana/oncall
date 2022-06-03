import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.public_api import constants as public_api_constants
from apps.schedules.models import CustomOnCallShift

demo_on_call_shift_payload_1 = {
    "id": public_api_constants.DEMO_ON_CALL_SHIFT_ID_1,
    "team_id": None,
    "name": public_api_constants.DEMO_ON_CALL_SHIFT_NAME_1,
    "type": "single_event",
    "time_zone": None,
    "level": 0,
    "start": public_api_constants.DEMO_ON_CALL_SHIFT_START_1,
    "duration": public_api_constants.DEMO_ON_CALL_SHIFT_DURATION,
    "users": [public_api_constants.DEMO_USER_ID],
}

demo_on_call_shift_payload_2 = {
    "id": public_api_constants.DEMO_ON_CALL_SHIFT_ID_2,
    "team_id": None,
    "name": public_api_constants.DEMO_ON_CALL_SHIFT_NAME_2,
    "type": "recurrent_event",
    "time_zone": None,
    "level": 0,
    "start": public_api_constants.DEMO_ON_CALL_SHIFT_START_2,
    "duration": public_api_constants.DEMO_ON_CALL_SHIFT_DURATION,
    "frequency": "weekly",
    "interval": 2,
    "week_start": "SU",
    "users": [public_api_constants.DEMO_USER_ID],
    "by_day": public_api_constants.DEMO_ON_CALL_SHIFT_BY_DAY,
    "by_month": None,
    "by_monthday": None,
}

demo_on_call_shift_payload_list = {
    "count": 2,
    "next": None,
    "previous": None,
    "results": [demo_on_call_shift_payload_1, demo_on_call_shift_payload_2],
}


@pytest.mark.django_db
def test_demo_get_on_call_shift_list(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:on_call_shifts-list")

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == demo_on_call_shift_payload_list


@pytest.mark.django_db
@pytest.mark.parametrize(
    "demo_on_call_shift_id,payload",
    [
        (public_api_constants.DEMO_ON_CALL_SHIFT_ID_1, demo_on_call_shift_payload_1),
        (public_api_constants.DEMO_ON_CALL_SHIFT_ID_2, demo_on_call_shift_payload_2),
    ],
)
def test_demo_get_on_call_shift_1(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
    demo_on_call_shift_id,
    payload,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:on_call_shifts-detail", kwargs={"pk": demo_on_call_shift_id})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == payload


@pytest.mark.django_db
def test_demo_post_on_call_shift(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:on_call_shifts-list")

    data = {
        "schedule_id": public_api_constants.DEMO_SCHEDULE_ID_CALENDAR,
        "name": "New demo shift",
        "type": CustomOnCallShift.TYPE_SINGLE_EVENT,
        "start": timezone.now().replace(tzinfo=None, microsecond=0).isoformat(),
        "duration": 3600,
    }

    response = client.post(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_201_CREATED
    assert response.data == demo_on_call_shift_payload_1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "demo_on_call_shift_id,payload",
    [
        (public_api_constants.DEMO_ON_CALL_SHIFT_ID_1, demo_on_call_shift_payload_1),
        (public_api_constants.DEMO_ON_CALL_SHIFT_ID_2, demo_on_call_shift_payload_2),
    ],
)
def test_demo_update_on_call_shift(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
    demo_on_call_shift_id,
    payload,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    data = {"name": "Updated demo name"}

    url = reverse("api-public:on_call_shifts-detail", kwargs={"pk": demo_on_call_shift_id})

    response = client.put(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == payload


@pytest.mark.django_db
@pytest.mark.parametrize(
    "demo_on_call_shift_id",
    [
        public_api_constants.DEMO_ON_CALL_SHIFT_ID_1,
        public_api_constants.DEMO_ON_CALL_SHIFT_ID_2,
    ],
)
def test_demo_delete_on_call_shift(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
    demo_on_call_shift_id,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:on_call_shifts-detail", kwargs={"pk": demo_on_call_shift_id})

    response = client.delete(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert CustomOnCallShift.objects.filter(public_primary_key=demo_on_call_shift_id).exists()
