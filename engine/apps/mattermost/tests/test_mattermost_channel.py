import json
from unittest.mock import Mock, patch

import pytest
import requests
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole


@pytest.mark.django_db
def test_not_authorized(make_organization_and_user_with_plugin_token, make_mattermost_channel):
    client = APIClient()

    organization, _, _ = make_organization_and_user_with_plugin_token()
    mattermost_channel = make_mattermost_channel(organization=organization)

    url = reverse("mattermost:channel-list")
    response = client.post(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    url = reverse("mattermost:channel-list")
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    url = reverse("mattermost:channel-detail", kwargs={"pk": mattermost_channel.public_primary_key})
    response = client.get(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    url = reverse("mattermost:channel-detail", kwargs={"pk": mattermost_channel.public_primary_key})
    response = client.delete(url)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_list_mattermost_channels_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    client = APIClient()
    _, user, token = make_organization_and_user_with_plugin_token(role)

    url = reverse("mattermost:channel-list")
    response = client.get(url, **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_get_mattermost_channels_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_mattermost_channel,
    role,
    expected_status,
):
    client = APIClient()
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    mattermost_channel = make_mattermost_channel(organization=organization)

    url = reverse("mattermost:channel-detail", kwargs={"pk": mattermost_channel.public_primary_key})
    response = client.get(url, **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_204_NO_CONTENT),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_delete_mattermost_channels_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_mattermost_channel,
    role,
    expected_status,
):
    client = APIClient()
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    mattermost_channel = make_mattermost_channel(organization=organization)

    url = reverse("mattermost:channel-detail", kwargs={"pk": mattermost_channel.public_primary_key})
    response = client.delete(url, **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_201_CREATED),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_post_mattermost_channels_permissions(
    make_organization_and_user_with_plugin_token,
    make_mattermost_get_channel_by_name_team_name_response,
    make_user_auth_headers,
    role,
    expected_status,
):
    client = APIClient()
    _, user, token = make_organization_and_user_with_plugin_token(role)

    data = make_mattermost_get_channel_by_name_team_name_response()
    channel_response = requests.Response()
    channel_response.status_code = status.HTTP_200_OK
    channel_response._content = json.dumps(data).encode()

    url = reverse("mattermost:channel-list")
    with patch("apps.mattermost.client.requests.get", return_value=channel_response) as mock_request:
        response = client.post(
            url,
            data={"team_name": "fuzzteam", "channel_name": "fuzzchannel"},
            format="json",
            **make_user_auth_headers(user, token),
        )
    assert response.status_code == expected_status
    if expected_status == status.HTTP_201_CREATED:
        res = response.json()
        mock_request.assert_called_once()
        assert res["channel_id"] == data["id"]
        assert res["channel_name"] == data["name"]
        assert res["display_name"] == f"{data['display_name']}-{data['team_id'][:5]}"
        assert res["is_default_channel"] is False


@pytest.mark.django_db
@pytest.mark.parametrize(
    "request_body,expected_status",
    [
        ({"team_name": "fuzzteam", "channel_name": "fuzzchannel"}, status.HTTP_201_CREATED),
        ({"team_name": "fuzzteam"}, status.HTTP_400_BAD_REQUEST),
        ({"channel_name": "fuzzchannel"}, status.HTTP_400_BAD_REQUEST),
    ],
)
def test_post_mattermost_channels(
    make_organization_and_user_with_plugin_token,
    make_mattermost_get_channel_by_name_team_name_response,
    make_user_auth_headers,
    request_body,
    expected_status,
):
    client = APIClient()
    _, user, token = make_organization_and_user_with_plugin_token()

    data = make_mattermost_get_channel_by_name_team_name_response()
    channel_response = requests.Response()
    channel_response.status_code = status.HTTP_200_OK
    channel_response._content = json.dumps(data).encode()

    url = reverse("mattermost:channel-list")
    with patch("apps.mattermost.client.requests.get", return_value=channel_response) as mock_request:
        response = client.post(url, data=request_body, format="json", **make_user_auth_headers(user, token))

    if expected_status == status.HTTP_201_CREATED:
        mock_request.assert_called_once()
    else:
        mock_request.assert_not_called()
    assert response.status_code == expected_status


@pytest.mark.django_db
def test_post_mattermost_channels_mattermost_api_call_failure(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    client = APIClient()
    _, user, token = make_organization_and_user_with_plugin_token()

    # Timeout Error
    mock_response = Mock()
    mock_response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    mock_response.request = requests.Request(
        url="https://example.com",
        method="GET",
    )
    mock_response.raise_for_status.side_effect = requests.Timeout(response=mock_response)

    url = reverse("mattermost:channel-list")
    with patch("apps.mattermost.client.requests.get", return_value=mock_response) as mock_request:
        response = client.post(
            url,
            data={"team_name": "fuzzteam", "channel_name": "fuzzchannel"},
            format="json",
            **make_user_auth_headers(user, token),
        )
    mock_request.assert_called_once()
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == "Mattermost api call gateway timedout"


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
    ],
)
def test_set_default_mattermost_channels_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_mattermost_channel,
    role,
    expected_status,
):
    client = APIClient()

    organization, user, token = make_organization_and_user_with_plugin_token(role)
    mattermost_channel = make_mattermost_channel(organization=organization)

    url = reverse("mattermost:channel-set-default", kwargs={"pk": mattermost_channel.public_primary_key})
    response = client.post(url, **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_list_mattermost_channels(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, make_mattermost_channel
):
    client = APIClient()

    organization, user, token = make_organization_and_user_with_plugin_token()

    first_mattermost_channel = make_mattermost_channel(organization=organization)
    second_mattermost_channel = make_mattermost_channel(organization=organization)

    expected_payload = [
        {
            "id": first_mattermost_channel.public_primary_key,
            "channel_id": first_mattermost_channel.channel_id,
            "channel_name": first_mattermost_channel.channel_name,
            "display_name": first_mattermost_channel.unique_display_name,
            "is_default_channel": first_mattermost_channel.is_default_channel,
        },
        {
            "id": second_mattermost_channel.public_primary_key,
            "channel_id": second_mattermost_channel.channel_id,
            "channel_name": second_mattermost_channel.channel_name,
            "display_name": second_mattermost_channel.unique_display_name,
            "is_default_channel": second_mattermost_channel.is_default_channel,
        },
    ]

    url = reverse("mattermost:channel-list")
    response = client.get(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_get_mattermost_channel(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, make_mattermost_channel
):
    client = APIClient()

    organization, user, token = make_organization_and_user_with_plugin_token()
    mattermost_channel = make_mattermost_channel(organization=organization)

    expected_payload = {
        "id": mattermost_channel.public_primary_key,
        "channel_id": mattermost_channel.channel_id,
        "channel_name": mattermost_channel.channel_name,
        "display_name": mattermost_channel.unique_display_name,
        "is_default_channel": mattermost_channel.is_default_channel,
    }

    url = reverse("mattermost:channel-detail", kwargs={"pk": mattermost_channel.public_primary_key})
    response = client.get(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_delete_mattermost_channel(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, make_mattermost_channel
):
    client = APIClient()

    organization, user, token = make_organization_and_user_with_plugin_token()
    mattermost_channel = make_mattermost_channel(organization=organization)

    url = reverse("mattermost:channel-detail", kwargs={"pk": mattermost_channel.public_primary_key})
    response = client.delete(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_204_NO_CONTENT

    url = reverse("mattermost:channel-detail", kwargs={"pk": mattermost_channel.public_primary_key})
    response = client.get(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_access_other_organization_mattermost_channels(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, make_mattermost_channel
):
    client = APIClient()

    organization, _, _ = make_organization_and_user_with_plugin_token()
    mattermost_channel = make_mattermost_channel(organization=organization)

    _, other_user, other_token = make_organization_and_user_with_plugin_token()

    url = reverse("mattermost:channel-detail", kwargs={"pk": mattermost_channel.public_primary_key})
    response = client.get(url, **make_user_auth_headers(other_user, other_token))
    assert response.status_code == status.HTTP_404_NOT_FOUND

    url = reverse("mattermost:channel-detail", kwargs={"pk": mattermost_channel.public_primary_key})
    response = client.delete(url, **make_user_auth_headers(other_user, other_token))
    assert response.status_code == status.HTTP_404_NOT_FOUND

    url = reverse("mattermost:channel-list")
    response = client.get(url, **make_user_auth_headers(other_user, other_token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

    url = reverse("mattermost:channel-set-default", kwargs={"pk": mattermost_channel.public_primary_key})
    response = client.post(url, **make_user_auth_headers(other_user, other_token))
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_set_default(make_organization_and_user_with_plugin_token, make_user_auth_headers, make_mattermost_channel):
    client = APIClient()

    organization, user, token = make_organization_and_user_with_plugin_token()

    first_mattermost_channel = make_mattermost_channel(organization=organization)
    second_mattermost_channel = make_mattermost_channel(organization=organization)

    # If no channel is default
    url = reverse("mattermost:channel-set-default", kwargs={"pk": first_mattermost_channel.public_primary_key})
    response = client.post(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    first_mattermost_channel.refresh_from_db()
    second_mattermost_channel.refresh_from_db()
    assert first_mattermost_channel.is_default_channel is True
    assert second_mattermost_channel.is_default_channel is False

    # If there is an existing default channel
    url = reverse("mattermost:channel-set-default", kwargs={"pk": second_mattermost_channel.public_primary_key})
    response = client.post(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    first_mattermost_channel.refresh_from_db()
    second_mattermost_channel.refresh_from_db()
    assert first_mattermost_channel.is_default_channel is False
    assert second_mattermost_channel.is_default_channel is True
