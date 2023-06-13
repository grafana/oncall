import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_public_api_tokens_retrieve_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_public_api_token,
    role,
    expected_status,
):
    organization, user, plugin_token = make_organization_and_user_with_plugin_token(role)
    api_token, _ = make_public_api_token(user, organization)
    client = APIClient()

    url = reverse("api-internal:api_token-detail", kwargs={"pk": api_token.id})
    response = client.get(url, format="json", **make_user_auth_headers(user, plugin_token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_public_api_tokens_list_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_public_api_token,
    role,
    expected_status,
):
    organization, user, plugin_token = make_organization_and_user_with_plugin_token(role)
    make_public_api_token(user, organization)
    client = APIClient()

    url = reverse("api-internal:api_token-list")
    response = client.get(url, format="json", **make_user_auth_headers(user, plugin_token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_201_CREATED),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_public_api_tokens_create_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, plugin_token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:api_token-list")
    response = client.post(
        url,
        data={
            "name": "helloooo",
        },
        format="json",
        **make_user_auth_headers(user, plugin_token),
    )

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_204_NO_CONTENT),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_public_api_tokens_delete_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_public_api_token,
    role,
    expected_status,
):
    organization, user, plugin_token = make_organization_and_user_with_plugin_token(role)
    api_token, _ = make_public_api_token(user, organization)
    client = APIClient()

    url = reverse("api-internal:api_token-detail", kwargs={"pk": api_token.id})
    response = client.delete(url, format="json", **make_user_auth_headers(user, plugin_token))

    assert response.status_code == expected_status
