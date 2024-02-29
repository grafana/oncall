from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.alerts.models import AlertReceiveChannel
from apps.api.permissions import LegacyAccessControlRole


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
def test_alert_receive_channel_get_connected_channels_permissions(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    source_alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_SERVICENOW
    )
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel-get-connected-channels",
        kwargs={"pk": source_alert_receive_channel.public_primary_key},
    )
    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.get_connected_channels",
        return_value=Response(status=status.HTTP_200_OK),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


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
def test_alert_receive_channel_update_connected_channel_permissions(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    source_alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_SERVICENOW
    )
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel-update-connected-channel",
        kwargs={
            "pk": source_alert_receive_channel.public_primary_key,
            "connected_channel_id": alert_receive_channel.public_primary_key,
        },
    )
    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.update_connected_channel",
        return_value=Response(status=status.HTTP_200_OK),
    ):
        response = client.put(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


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
def test_alert_receive_channel_connect_channels_permissions(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    source_alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_SERVICENOW
    )
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel-get-connected-channels",
        kwargs={"pk": source_alert_receive_channel.public_primary_key},
    )
    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.connect_channels",
        return_value=Response(status=status.HTTP_200_OK),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


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
def test_alert_receive_channel_disconnect_channels_permissions(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    source_alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_SERVICENOW
    )
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel-get-connected-channels",
        kwargs={"pk": source_alert_receive_channel.public_primary_key},
    )
    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.disconnect_channels",
        return_value=Response(status=status.HTTP_200_OK),
    ):
        response = client.delete(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_alert_receive_channel_get_connected_channels(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel_connection_with_channels,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    source_channel, connected_channel, channel_connection = make_alert_receive_channel_connection_with_channels(
        organization
    )
    # get integrations connected to source integration
    url = reverse(
        "api-internal:alert_receive_channel-get-connected-channels",
        kwargs={"pk": source_channel.public_primary_key},
    )

    expected_result = {
        "source_alert_receive_channels": [],
        "connected_alert_receive_channels": [
            {
                "alert_receive_channel": {
                    "id": connected_channel.public_primary_key,
                    "integration": connected_channel.integration,
                    "verbal_name": connected_channel.verbal_name,
                    "deleted": False,
                },
                "backsync": False,
            },
        ],
    }

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result

    # get source integrations for particular integration
    url = reverse(
        "api-internal:alert_receive_channel-get-connected-channels",
        kwargs={"pk": connected_channel.public_primary_key},
    )
    expected_result = {
        "source_alert_receive_channels": [
            {
                "alert_receive_channel": {
                    "id": source_channel.public_primary_key,
                    "integration": source_channel.integration,
                    "verbal_name": source_channel.verbal_name,
                    "deleted": False,
                },
                "backsync": False,
            },
        ],
        "connected_alert_receive_channels": [],
    }

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@pytest.mark.django_db
def test_alert_receive_channel_update_connected_channel(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel_connection_with_channels,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    source_channel, connected_channel, channel_connection = make_alert_receive_channel_connection_with_channels(
        organization
    )
    # update backsync for connected integration
    url = reverse(
        "api-internal:alert_receive_channel-update-connected-channel",
        kwargs={"pk": source_channel.public_primary_key, "connected_channel_id": connected_channel.public_primary_key},
    )

    data = {"backsync": True}

    expected_result = {
        "alert_receive_channel": {
            "id": connected_channel.public_primary_key,
            "integration": connected_channel.integration,
            "verbal_name": connected_channel.verbal_name,
            "deleted": False,
        },
        "backsync": True,
    }
    assert channel_connection.backsync is False

    response = client.put(url, data=data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result

    channel_connection.refresh_from_db()
    assert channel_connection.backsync is True

    # updates work only when pk is a source integration ppk and connected_channel_id is a connected integration ppk
    url = reverse(
        "api-internal:alert_receive_channel-update-connected-channel",
        kwargs={"pk": connected_channel.public_primary_key, "connected_channel_id": source_channel.public_primary_key},
    )

    response = client.put(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_alert_receive_channel_connect_channels(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    source_channel = make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_SERVICENOW)
    channel_to_connect_1 = make_alert_receive_channel(organization)
    channel_to_connect_2 = make_alert_receive_channel(organization)

    data = [
        {"id": channel_to_connect_1.public_primary_key, "backsync": False},
        {"id": channel_to_connect_2.public_primary_key, "backsync": True},
    ]
    # update backsync for connected integration
    url = reverse(
        "api-internal:alert_receive_channel-get-connected-channels",
        kwargs={"pk": source_channel.public_primary_key},
    )

    expected_result = {
        "source_alert_receive_channels": [],
        "connected_alert_receive_channels": [
            {
                "alert_receive_channel": {
                    "id": channel_to_connect_1.public_primary_key,
                    "integration": channel_to_connect_1.integration,
                    "verbal_name": channel_to_connect_1.verbal_name,
                    "deleted": False,
                },
                "backsync": False,
            },
            {
                "alert_receive_channel": {
                    "id": channel_to_connect_2.public_primary_key,
                    "integration": channel_to_connect_2.integration,
                    "verbal_name": channel_to_connect_2.verbal_name,
                    "deleted": False,
                },
                "backsync": True,
            },
        ],
    }
    assert source_channel.connected_alert_receive_channels.count() == 0
    response = client.post(url, data=data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result
    assert source_channel.connected_alert_receive_channels.count() == 2


@pytest.mark.django_db
def test_alert_receive_channel_disconnect_channels(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel_connection_with_channels,
    make_alert_receive_channel,
    make_alert_receive_channel_connection,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    source_channel, connected_channel_1, _ = make_alert_receive_channel_connection_with_channels(organization)
    connected_channel_2 = make_alert_receive_channel(organization)
    make_alert_receive_channel_connection(source_channel, connected_channel_2)

    data = [connected_channel_1.public_primary_key]
    url = reverse(
        "api-internal:alert_receive_channel-get-connected-channels",
        kwargs={"pk": source_channel.public_primary_key},
    )

    expected_result = {
        "source_alert_receive_channels": [],
        "connected_alert_receive_channels": [
            {
                "alert_receive_channel": {
                    "id": connected_channel_2.public_primary_key,
                    "integration": connected_channel_2.integration,
                    "verbal_name": connected_channel_2.verbal_name,
                    "deleted": False,
                },
                "backsync": False,
            },
        ],
    }
    assert source_channel.connected_alert_receive_channels.count() == 2
    response = client.delete(url, data=data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result
    assert source_channel.connected_alert_receive_channels.count() == 1
    assert source_channel.connected_alert_receive_channels.first().connected_channel == connected_channel_2
