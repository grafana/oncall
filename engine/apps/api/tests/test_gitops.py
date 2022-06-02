import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from common.constants.role import Role


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
    ],
)
def test_terraform_gitops_permissions(
    make_organization_and_user_with_plugin_token,
    make_escalation_chain,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    make_escalation_chain(organization)

    client = APIClient()

    url = reverse("api-internal:terraform_file")

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (Role.ADMIN, status.HTTP_200_OK),
        (Role.EDITOR, status.HTTP_200_OK),
        (Role.VIEWER, status.HTTP_200_OK),
    ],
)
def test_terraform_state_permissions(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, role, expected_status
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:terraform_imports")

    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status
