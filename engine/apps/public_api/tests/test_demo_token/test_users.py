import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.public_api import constants as public_api_constants

# NB can compare with https://api-docs.amixr.io/#get-user

demo_token_user_payload = {
    "id": public_api_constants.DEMO_USER_ID,
    "email": public_api_constants.DEMO_USER_EMAIL,
    "slack": {"user_id": public_api_constants.DEMO_SLACK_USER_ID, "team_id": public_api_constants.DEMO_SLACK_TEAM_ID},
    "username": public_api_constants.DEMO_USER_USERNAME,
    "role": "admin",
}

# https://api-docs.amixr.io/#list-users
demo_token_users_payload = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [
        {
            "id": public_api_constants.DEMO_USER_ID,
            "email": public_api_constants.DEMO_USER_EMAIL,
            "slack": {
                "user_id": public_api_constants.DEMO_SLACK_USER_ID,
                "team_id": public_api_constants.DEMO_SLACK_TEAM_ID,
            },
            "username": public_api_constants.DEMO_USER_USERNAME,
            "role": "admin",
        }
    ],
}


@pytest.mark.django_db
def test_get_user(
    make_organization_and_user_with_slack_identities_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()

    url = reverse("api-public:users-detail", args=[user.public_primary_key])
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_token_user_payload

    # get current user
    url = reverse("api-public:users-detail", args=["current"])
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_token_user_payload


@pytest.mark.django_db
def test_get_users(
    make_organization_and_user_with_slack_identities_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()

    url = reverse("api-public:users-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_token_users_payload


@pytest.mark.django_db
def test_forbidden_access(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_organization_and_user_with_token,
):
    _, user, _ = make_organization_and_user_with_slack_identities_for_demo_token()
    _, _, another_org_token = make_organization_and_user_with_token()

    client = APIClient()

    url = reverse("api-public:users-detail", args=[user.public_primary_key])

    response = client.get(url, format="json", HTTP_AUTHORIZATION=another_org_token)

    assert response.status_code == status.HTTP_404_NOT_FOUND
