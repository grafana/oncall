import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole


@pytest.mark.django_db
def test_not_authorized(make_organization_and_user_with_plugin_token, make_telegram_channel):
    client = APIClient()

    organization, _, _ = make_organization_and_user_with_plugin_token()
    telegram_channel = make_telegram_channel(organization=organization)

    url = reverse("api-internal:telegram_channel-list")
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    url = reverse("api-internal:telegram_channel-detail", kwargs={"pk": telegram_channel.public_primary_key})
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    url = reverse("api-internal:telegram_channel-detail", kwargs={"pk": telegram_channel.public_primary_key})
    response = client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    url = reverse("api-internal:telegram_channel-set-default", kwargs={"pk": telegram_channel.public_primary_key})
    response = client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_list_telegram_channels_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    client = APIClient()
    _, user, token = make_organization_and_user_with_plugin_token(role)

    url = reverse("api-internal:telegram_channel-list")
    response = client.get(url, **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_get_telegram_channels_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_telegram_channel,
    role,
    expected_status,
):
    client = APIClient()
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    telegram_channel = make_telegram_channel(organization=organization)

    url = reverse("api-internal:telegram_channel-detail", kwargs={"pk": telegram_channel.public_primary_key})
    response = client.get(url, **make_user_auth_headers(user, token))

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
def test_delete_telegram_channels_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_telegram_channel,
    role,
    expected_status,
):
    client = APIClient()

    organization, user, token = make_organization_and_user_with_plugin_token(role)
    telegram_channel = make_telegram_channel(organization=organization)

    url = reverse("api-internal:telegram_channel-detail", kwargs={"pk": telegram_channel.public_primary_key})
    response = client.delete(url, **make_user_auth_headers(user, token))

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
def test_set_default_telegram_channels_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_telegram_channel,
    role,
    expected_status,
):
    client = APIClient()

    organization, user, token = make_organization_and_user_with_plugin_token(role)
    telegram_channel = make_telegram_channel(organization=organization)

    url = reverse("api-internal:telegram_channel-set-default", kwargs={"pk": telegram_channel.public_primary_key})
    response = client.post(url, **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_list_telegram_channels(
    make_telegram_channel, make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    client = APIClient()

    organization, user, token = make_organization_and_user_with_plugin_token()

    first_telegram_channel = make_telegram_channel(organization=organization)
    second_telegram_channel = make_telegram_channel(organization=organization, is_default_channel=True)

    expected_payload = [
        {
            "id": first_telegram_channel.public_primary_key,
            "channel_chat_id": first_telegram_channel.channel_chat_id,
            "discussion_group_chat_id": first_telegram_channel.discussion_group_chat_id,
            "channel_name": first_telegram_channel.channel_name,
            "discussion_group_name": first_telegram_channel.discussion_group_name,
            "is_default_channel": False,
        },
        {
            "id": second_telegram_channel.public_primary_key,
            "channel_chat_id": second_telegram_channel.channel_chat_id,
            "discussion_group_chat_id": second_telegram_channel.discussion_group_chat_id,
            "channel_name": second_telegram_channel.channel_name,
            "discussion_group_name": second_telegram_channel.discussion_group_name,
            "is_default_channel": True,
        },
    ]

    url = reverse("api-internal:telegram_channel-list")
    response = client.get(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_get_telegram_channel(
    make_telegram_channel, make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    client = APIClient()

    organization, user, token = make_organization_and_user_with_plugin_token()
    telegram_channel = make_telegram_channel(organization=organization, is_default_channel=True)

    expected_payload = {
        "id": telegram_channel.public_primary_key,
        "channel_chat_id": telegram_channel.channel_chat_id,
        "discussion_group_chat_id": telegram_channel.discussion_group_chat_id,
        "channel_name": telegram_channel.channel_name,
        "discussion_group_name": telegram_channel.discussion_group_name,
        "is_default_channel": True,
    }

    url = reverse("api-internal:telegram_channel-detail", kwargs={"pk": telegram_channel.public_primary_key})
    response = client.get(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_delete_telegram_channel(
    make_telegram_channel, make_organization_and_user_with_plugin_token, make_user_auth_headers
):
    client = APIClient()

    organization, user, token = make_organization_and_user_with_plugin_token()
    telegram_channel = make_telegram_channel(organization=organization, is_default_channel=True)

    url = reverse("api-internal:telegram_channel-detail", kwargs={"pk": telegram_channel.public_primary_key})
    response = client.delete(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_204_NO_CONTENT

    url = reverse("api-internal:telegram_channel-detail", kwargs={"pk": telegram_channel.public_primary_key})
    response = client.get(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_access_other_organizations_telegram_channels(
    make_organization_and_user_with_plugin_token, make_telegram_channel, make_user_auth_headers
):
    client = APIClient()

    organization, user, token = make_organization_and_user_with_plugin_token()
    telegram_channel = make_telegram_channel(organization=organization)

    other_organization, other_user, other_token = make_organization_and_user_with_plugin_token()

    url = reverse("api-internal:telegram_channel-detail", kwargs={"pk": telegram_channel.public_primary_key})
    response = client.get(url, **make_user_auth_headers(other_user, other_token))
    assert response.status_code == status.HTTP_404_NOT_FOUND

    url = reverse("api-internal:telegram_channel-detail", kwargs={"pk": telegram_channel.public_primary_key})
    response = client.delete(url, **make_user_auth_headers(other_user, other_token))
    assert response.status_code == status.HTTP_404_NOT_FOUND

    url = reverse("api-internal:telegram_channel-list")
    response = client.get(url, **make_user_auth_headers(other_user, other_token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

    url = reverse("api-internal:telegram_channel-set-default", kwargs={"pk": telegram_channel.public_primary_key})
    response = client.post(url, **make_user_auth_headers(other_user, other_token))
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_set_default(make_telegram_channel, make_organization_and_user_with_plugin_token, make_user_auth_headers):
    client = APIClient()

    organization, user, token = make_organization_and_user_with_plugin_token()
    first_telegram_channel = make_telegram_channel(organization=organization, is_default_channel=True)
    second_telegram_channel = make_telegram_channel(organization=organization)

    url = reverse(
        "api-internal:telegram_channel-set-default", kwargs={"pk": second_telegram_channel.public_primary_key}
    )
    response = client.post(url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK

    first_telegram_channel.refresh_from_db()
    second_telegram_channel.refresh_from_db()

    assert first_telegram_channel.is_default_channel is False
    assert second_telegram_channel.is_default_channel is True
