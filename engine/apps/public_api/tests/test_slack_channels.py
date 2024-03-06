import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture()
def slack_channels_public_api_setup(
    make_organization_and_user_with_slack_identities,
    make_public_api_token,
    make_slack_channel,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    _, token = make_public_api_token(user, organization)
    slack_channel = make_slack_channel(slack_team_identity, slack_id="TEST_SLACK_CHANNEL")
    return organization, user, token, slack_team_identity, slack_user_identity, slack_channel


@pytest.mark.django_db
def test_get_slack_channels_list(
    slack_channels_public_api_setup,
):
    _, _, token, _, _, slack_channel = slack_channels_public_api_setup

    client = APIClient()

    url = reverse("api-public:slack_channels-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    expected_response = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [{"name": slack_channel.name, "slack_id": slack_channel.slack_id}],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response
