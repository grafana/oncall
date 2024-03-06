import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture()
def team_public_api_setup(
    make_organization_and_user,
    make_public_api_token,
    make_team,
):
    organization, user = make_organization_and_user()
    _, token = make_public_api_token(user, organization)
    team = make_team(organization)
    team.users.add(user)
    return organization, user, token, team


@pytest.mark.django_db
def test_get_teams_list(team_public_api_setup):
    _, _, token, team = team_public_api_setup

    client = APIClient()

    url = reverse("api-public:teams-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_payload = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": team.public_primary_key,
                "name": team.name,
                "email": team.email,
                "avatar_url": team.avatar_url,
            }
        ],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_get_team(team_public_api_setup):
    _, _, token, team = team_public_api_setup

    client = APIClient()

    url = reverse("api-public:teams-detail", kwargs={"pk": team.public_primary_key})

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    expected_payload = {
        "id": team.public_primary_key,
        "name": team.name,
        "email": team.email,
        "avatar_url": team.avatar_url,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload
