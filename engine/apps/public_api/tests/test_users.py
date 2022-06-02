import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture()
def user_public_api_setup(
    make_organization_and_user_with_slack_identities,
    make_public_api_token,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    _, token = make_public_api_token(user, organization)
    return organization, user, token, slack_team_identity, slack_user_identity


@pytest.mark.django_db
def test_get_user(
    user_public_api_setup,
):
    organization, user, token, slack_team_identity, slack_user_identity = user_public_api_setup

    client = APIClient()

    url = reverse("api-public:users-detail", args=[user.public_primary_key])
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    expected_response = {
        "id": user.public_primary_key,
        "email": user.email,
        "slack": {"user_id": slack_user_identity.slack_id, "team_id": slack_team_identity.slack_id},
        "username": user.username,
        "role": "admin",
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response

    # get current user
    url = reverse("api-public:users-detail", args=["current"])
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_users_list(
    user_public_api_setup,
    make_user_for_organization,
):
    organization, user_1, token, slack_team_identity, slack_user_identity = user_public_api_setup
    user_2 = make_user_for_organization(organization)

    client = APIClient()

    url = reverse("api-public:users-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    expected_response = {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": user_1.public_primary_key,
                "email": user_1.email,
                "slack": {"user_id": slack_user_identity.slack_id, "team_id": slack_team_identity.slack_id},
                "username": user_1.username,
                "role": "admin",
            },
            {
                "id": user_2.public_primary_key,
                "email": user_2.email,
                "slack": None,
                "username": user_2.username,
                "role": "admin",
            },
        ],
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_forbidden_access(
    make_organization_and_user,
    make_organization_and_user_with_token,
):
    _, user = make_organization_and_user()
    _, _, another_org_token = make_organization_and_user_with_token()

    client = APIClient()

    url = reverse("api-public:users-detail", args=[user.public_primary_key])

    response = client.get(url, format="json", HTTP_AUTHORIZATION=another_org_token)

    assert response.status_code == status.HTTP_404_NOT_FOUND
