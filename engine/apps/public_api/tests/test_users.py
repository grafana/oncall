import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole


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
    _, user, token, slack_team_identity, slack_user_identity = user_public_api_setup

    client = APIClient()

    url = reverse("api-public:users-detail", args=[user.public_primary_key])
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    expected_response = {
        "id": user.public_primary_key,
        "email": user.email,
        "slack": {"user_id": slack_user_identity.slack_id, "team_id": slack_team_identity.slack_id},
        "username": user.username,
        "role": "admin",
        "is_phone_number_verified": False,
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
                "is_phone_number_verified": False,
            },
            {
                "id": user_2.public_primary_key,
                "email": user_2.email,
                "slack": None,
                "username": user_2.username,
                "role": "admin",
                "is_phone_number_verified": False,
            },
        ],
        "current_page_number": 1,
        "page_size": 100,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_users_list_short(
    user_public_api_setup,
    make_user_for_organization,
):
    organization, user_1, token, _, _ = user_public_api_setup
    user_2 = make_user_for_organization(organization)

    client = APIClient()

    url = reverse("api-public:users-list")
    response = client.get(f"{url}?short=true", format="json", HTTP_AUTHORIZATION=token)

    expected_response = {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": user_1.public_primary_key,
                "email": user_1.email,
                "username": user_1.username,
                "role": "admin",
                "is_phone_number_verified": False,
            },
            {
                "id": user_2.public_primary_key,
                "email": user_2.email,
                "username": user_2.username,
                "role": "admin",
                "is_phone_number_verified": False,
            },
        ],
        "current_page_number": 1,
        "page_size": 100,
        "total_pages": 1,
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


@pytest.mark.django_db
def test_get_users_list_all_role_users(user_public_api_setup, make_user_for_organization):
    organization, admin, token, _, _ = user_public_api_setup
    editor = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)
    viewer = make_user_for_organization(organization, role=LegacyAccessControlRole.VIEWER)

    client = APIClient()

    url = reverse("api-public:users-list")
    response = client.get(f"{url}?short=true", format="json", HTTP_AUTHORIZATION=token)

    expected_users = [(admin, "admin"), (editor, "editor"), (viewer, "viewer")]
    expected_response = {
        "count": 3,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": user.public_primary_key,
                "email": user.email,
                "username": user.username,
                "role": role,
                "is_phone_number_verified": False,
            }
            for user, role in expected_users
        ],
        "current_page_number": 1,
        "page_size": 100,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response
