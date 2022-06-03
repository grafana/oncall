import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.public_api import constants as public_api_constants

demo_slack_channels_payload = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [
        {
            "name": public_api_constants.DEMO_SLACK_CHANNEL_NAME,
            "slack_id": public_api_constants.DEMO_SLACK_CHANNEL_SLACK_ID,
        }
    ],
}


@pytest.mark.django_db
def test_get_slack_channels_list(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:slack_channels-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_slack_channels_payload
