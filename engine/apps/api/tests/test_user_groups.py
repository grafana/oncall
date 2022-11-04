import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole


@pytest.mark.django_db
def test_usergroup_list(
    make_slack_team_identity,
    make_slack_user_group,
    make_organization,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    team_identity = make_slack_team_identity()
    user_group = make_slack_user_group(
        slack_team_identity=team_identity, name="Test User Group", handle="test-user-group"
    )

    organization = make_organization(slack_team_identity=team_identity)
    _, token = make_token_for_organization(organization=organization)
    user = make_user_for_organization(organization=organization)

    client = APIClient()
    url = reverse("api-internal:user_group-list")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    expected_data = [{"id": user_group.public_primary_key, "name": "Test User Group", "handle": "test-user-group"}]

    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_data


@pytest.mark.django_db
def test_usergroup_list_without_slack_installed(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    _, user, token = make_organization_and_user_with_plugin_token()

    client = APIClient()
    url = reverse("api-internal:user_group-list")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.data == []


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_usergroup_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:user_group-list")

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status
