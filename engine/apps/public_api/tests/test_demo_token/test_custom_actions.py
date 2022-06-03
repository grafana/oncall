import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.public_api import constants as public_api_constants

demo_custom_action_payload = {
    "id": public_api_constants.DEMO_CUSTOM_ACTION_ID,
    "name": public_api_constants.DEMO_CUSTOM_ACTION_NAME,
    "team_id": None,
}

demo_custom_action_payload_list = {"count": 1, "next": None, "previous": None, "results": [demo_custom_action_payload]}


@pytest.mark.django_db
def test_demo_get_custom_actions_list(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:actions-list")

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == demo_custom_action_payload_list
