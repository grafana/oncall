import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture()
def slack_user_group_public_api_setup(
    make_organization_and_user_with_slack_identities,
    make_public_api_token,
    make_slack_user_group,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    _, token = make_public_api_token(user, organization)
    slack_user_group = make_slack_user_group(slack_team_identity, slack_id="SLACK_GROUP_ID")
    return organization, user, token, slack_team_identity, slack_user_identity, slack_user_group


@pytest.mark.django_db
def test_get_user_groups(
    slack_user_group_public_api_setup,
):
    _, _, token, _, _, slack_user_group = slack_user_group_public_api_setup

    client = APIClient()

    url = reverse("api-public:user_groups-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_payload = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": slack_user_group.public_primary_key,
                "type": "slack_based",
                "slack": {
                    "id": slack_user_group.slack_id,
                    "name": slack_user_group.name,
                    "handle": slack_user_group.handle,
                },
            }
        ],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_get_user_groups_filter_by_handle(
    slack_user_group_public_api_setup,
    make_slack_user_group,
):
    _, _, token, slack_team_identity, slack_user_identity, slack_user_group_1 = slack_user_group_public_api_setup

    client = APIClient()

    make_slack_user_group(slack_team_identity, slack_id="SLACK_GROUP_ID_2")

    url = reverse("api-public:user_groups-list")

    response = client.get(
        f"{url}?slack_handle={slack_user_group_1.handle}", format="json", HTTP_AUTHORIZATION=f"{token}"
    )

    expected_payload = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": slack_user_group_1.public_primary_key,
                "type": "slack_based",
                "slack": {
                    "id": slack_user_group_1.slack_id,
                    "name": slack_user_group_1.name,
                    "handle": slack_user_group_1.handle,
                },
            }
        ],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_get_user_groups_filter_by_handle_empty_result(
    slack_user_group_public_api_setup,
):
    _, _, token, slack_team_identity, _, slack_user_group = slack_user_group_public_api_setup

    client = APIClient()

    url = reverse("api-public:user_groups-list")

    response = client.get(f"{url}?slack_handle=NonExistentSlackHandle", format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_payload = {
        "count": 0,
        "next": None,
        "previous": None,
        "results": [],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload
