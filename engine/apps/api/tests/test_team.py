import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.user_management.models import Team
from common.constants.role import Role

GENERAL_TEAM = Team(public_primary_key=None, name="General", email=None, avatar_url=None)


def get_payload_from_team(team):
    return {"id": team.public_primary_key, "name": team.name, "email": team.email, "avatar_url": team.avatar_url}


@pytest.mark.django_db
def test_list_teams(
    make_organization,
    make_team,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    _, token = make_token_for_organization(organization)

    team = make_team(organization)
    team.users.add(user)

    client = APIClient()
    url = reverse("api-internal:team-list")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    expected_payload = [get_payload_from_team(team), get_payload_from_team(GENERAL_TEAM)]

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_list_teams_for_non_member(
    make_organization,
    make_team,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    make_team(organization)
    user = make_user_for_organization(organization)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:team-list")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [get_payload_from_team(GENERAL_TEAM)]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
    ],
)
def test_list_teams_permissions(
    make_organization,
    make_token_for_organization,
    make_user_for_organization,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization = make_organization()
    _, token = make_token_for_organization(organization)
    user = make_user_for_organization(organization, role=role)

    client = APIClient()
    url = reverse("api-internal:team-list")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
