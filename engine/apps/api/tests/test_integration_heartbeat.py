import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.heartbeat.models import IntegrationHeartBeat

MOCK_LAST_HEARTBEAT_TIME_VERBAL = "a moment"


@pytest.fixture()
def integration_heartbeat_internal_api_setup(
    make_organization_and_user_with_plugin_token, make_alert_receive_channel, make_integration_heartbeat
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    now = timezone.now()
    integration_heartbeat = make_integration_heartbeat(alert_receive_channel, last_heartbeat_time=now)
    return user, token, alert_receive_channel, integration_heartbeat


@pytest.mark.django_db
@patch(
    "apps.api.serializers.integration_heartbeat.IntegrationHeartBeatSerializer.get_instruction",
    return_value="<p>Grafana instruction<p>",
)
@patch(
    "apps.api.serializers.integration_heartbeat.IntegrationHeartBeatSerializer._last_heartbeat_time_verbal",
    return_value=MOCK_LAST_HEARTBEAT_TIME_VERBAL,
)
def test_get_list_integration_heartbeat(
    mocked_verbal,
    mocked_instruction,
    integration_heartbeat_internal_api_setup,
    make_user_auth_headers,
):
    user, token, alert_receive_channel, integration_heartbeat = integration_heartbeat_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:integration_heartbeat-list")

    expected_payload = [
        {
            "id": integration_heartbeat.public_primary_key,
            "last_heartbeat_time_verbal": mocked_verbal.return_value,
            "alert_receive_channel": alert_receive_channel.public_primary_key,
            "link": integration_heartbeat.link,
            "timeout_seconds": 60,
            "status": True,
            "instruction": mocked_instruction.return_value,
        }
    ]

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
@patch(
    "apps.api.serializers.integration_heartbeat.IntegrationHeartBeatSerializer.get_instruction",
    return_value="<p>Grafana instruction<p>",
)
@patch(
    "apps.api.serializers.integration_heartbeat.IntegrationHeartBeatSerializer._last_heartbeat_time_verbal",
    return_value=MOCK_LAST_HEARTBEAT_TIME_VERBAL,
)
def test_get_detail_integration_heartbeat(
    mocked_verbal,
    mocked_instruction,
    integration_heartbeat_internal_api_setup,
    make_user_auth_headers,
):
    user, token, alert_receive_channel, integration_heartbeat = integration_heartbeat_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:integration_heartbeat-detail", kwargs={"pk": integration_heartbeat.public_primary_key})

    expected_payload = {
        "id": integration_heartbeat.public_primary_key,
        "last_heartbeat_time_verbal": mocked_verbal.return_value,
        "alert_receive_channel": alert_receive_channel.public_primary_key,
        "link": integration_heartbeat.link,
        "timeout_seconds": 60,
        "status": True,
        "instruction": mocked_instruction.return_value,
    }

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
@patch(
    "apps.api.serializers.integration_heartbeat.IntegrationHeartBeatSerializer.get_instruction",
    return_value="<p>Grafana instruction<p>",
)
def test_create_integration_heartbeat(
    mocked_instruction,
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()
    url = reverse("api-internal:integration_heartbeat-list")

    data_for_create = {"alert_receive_channel": alert_receive_channel.public_primary_key, "timeout_seconds": 60}
    response = client.post(url, data_for_create, format="json", **make_user_auth_headers(user, token))

    integration_heartbeat = IntegrationHeartBeat.objects.get(public_primary_key=response.data["id"])

    expected_payload = {
        "id": integration_heartbeat.public_primary_key,
        "alert_receive_channel": alert_receive_channel.public_primary_key,
        "last_heartbeat_time_verbal": None,
        "timeout_seconds": 60,
        "link": integration_heartbeat.link,
        "status": False,
        "instruction": mocked_instruction.return_value,
    }
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_create_invalid_timeout_integration_heartbeat(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()
    url = reverse("api-internal:integration_heartbeat-list")

    data_for_create = {"alert_receive_channel": alert_receive_channel.public_primary_key, "timeout_seconds": 71}
    response = client.post(url, data_for_create, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_create_empty_alert_receive_channel_integration_heartbeat(
    integration_heartbeat_internal_api_setup,
    make_user_auth_headers,
):
    user, token, _, _ = integration_heartbeat_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:integration_heartbeat-list")

    data_for_create = {"timeout_seconds": 60}
    response = client.post(url, data_for_create, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_integration_heartbeat(
    integration_heartbeat_internal_api_setup,
    make_user_auth_headers,
):
    user, token, alert_receive_channel, integration_heartbeat = integration_heartbeat_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:integration_heartbeat-detail", kwargs={"pk": integration_heartbeat.public_primary_key})

    data = {
        "alert_receive_channel": alert_receive_channel.public_primary_key,
        "timeout_seconds": 600,
    }
    response = client.put(
        url, data=json.dumps(data), content_type="application/json", **make_user_auth_headers(user, token)
    )
    updated_instance = IntegrationHeartBeat.objects.get(public_primary_key=integration_heartbeat.public_primary_key)
    assert response.status_code == status.HTTP_200_OK
    assert updated_instance.timeout_seconds == 600


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_integration_heartbeat_create_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:integration_heartbeat-list")

    with patch(
        "apps.api.views.integration_heartbeat.IntegrationHeartBeatView.create",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
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
    ],
)
def test_integration_heartbeat_update_permissions(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_integration_heartbeat,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    integration_heartbeat = make_integration_heartbeat(alert_receive_channel)
    client = APIClient()

    url = reverse("api-internal:integration_heartbeat-detail", kwargs={"pk": integration_heartbeat.public_primary_key})

    with patch(
        "apps.api.views.integration_heartbeat.IntegrationHeartBeatView.update",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.put(url, format="json", **make_user_auth_headers(user, token))

        assert response.status_code == expected_status

        response = client.patch(url, format="json", **make_user_auth_headers(user, token))

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
def test_integration_heartbeat_list_permissions(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_integration_heartbeat,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    make_integration_heartbeat(alert_receive_channel)
    client = APIClient()

    url = reverse("api-internal:integration_heartbeat-list")

    with patch(
        "apps.api.views.integration_heartbeat.IntegrationHeartBeatView.list",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

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
def test_integration_heartbeat_timeout_options_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:integration_heartbeat-timeout-options")

    with patch(
        "apps.api.views.integration_heartbeat.IntegrationHeartBeatView.timeout_options",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

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
def test_integration_heartbeat_retrieve_permissions(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_integration_heartbeat,
    make_user_auth_headers,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    integration_heartbeat = make_integration_heartbeat(alert_receive_channel)
    client = APIClient()

    url = reverse("api-internal:integration_heartbeat-detail", kwargs={"pk": integration_heartbeat.public_primary_key})

    with patch(
        "apps.api.views.integration_heartbeat.IntegrationHeartBeatView.retrieve",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status
