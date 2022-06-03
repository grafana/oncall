import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.public_api import constants as public_api_constants

demo_user_group_payload = {
    "id": public_api_constants.DEMO_SLACK_USER_GROUP_ID,
    "type": "slack_based",
    "slack": {
        "id": public_api_constants.DEMO_SLACK_USER_GROUP_SLACK_ID,
        "name": public_api_constants.DEMO_SLACK_USER_GROUP_NAME,
        "handle": public_api_constants.DEMO_SLACK_USER_GROUP_HANDLE,
    },
}

demo_user_group_payload_list = {"count": 1, "next": None, "previous": None, "results": [demo_user_group_payload]}


@pytest.mark.django_db
def test_demo_get_user_groups_list(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:user_groups-list")

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.data == demo_user_group_payload_list
