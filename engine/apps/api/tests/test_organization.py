import os
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.api.serializers.organization import CurrentOrganizationSerializer

mock_banner = {"title": None, "body": None}
mock_env_status = {
    "telegram_configured": False,
    "phone_provider": {
        "configured": False,
        "test_sms": False,
        "test_call": False,
        "verification_call": False,
        "verification_sms": False,
    },
}


@patch.object(CurrentOrganizationSerializer, "get_banner", return_value=mock_banner)
@patch.object(CurrentOrganizationSerializer, "get_env_status", return_value=mock_env_status)
@pytest.mark.django_db
def test_get_organization(
    mocked_banner,
    mocked_env_status,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    client = APIClient()
    url = reverse("api-internal:api-organization")
    expected_result = {
        "pk": organization.public_primary_key,
        "name": organization.org_title,
        "stack_slug": organization.stack_slug,
        "slack_team_identity": None,
        "slack_channel": None,
        "rbac_enabled": organization.is_rbac_permissions_enabled,
        "grafana_incident_enabled": organization.is_grafana_incident_enabled,
        "is_resolution_note_required": False,
        "env_status": mock_env_status,
        "banner": mock_banner,
    }
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result


@pytest.mark.django_db
def test_get_organization_rbac_enabled(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    is_rbac_enabled = os.getenv("ONCALL_TESTING_RBAC_ENABLED", "True") == "True"
    organization, user, token = make_organization_and_user_with_plugin_token()
    # set rbac enabled based on env variable (factories use this value)
    organization.is_rbac_permissions_enabled = is_rbac_enabled
    organization.save()

    client = APIClient()
    url = reverse("api-internal:api-organization")

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["rbac_enabled"] == organization.is_rbac_permissions_enabled


@pytest.mark.django_db
def test_update_organization_settings(make_organization_and_user_with_plugin_token, make_user_auth_headers):
    organization, user, token = make_organization_and_user_with_plugin_token()

    client = APIClient()
    url = reverse("api-internal:api-organization")
    data = {"is_resolution_note_required": True}

    assert organization.is_resolution_note_required is False

    response = client.put(url, format="json", data=data, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    organization.refresh_from_db()
    assert organization.is_resolution_note_required is True


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
def test_organization_retrieve_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, tester, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:api-organization")
    with patch(
        "apps.api.views.organization.CurrentOrganizationView.get",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(tester, token))

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
def test_organization_update_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, tester, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:api-organization")

    with patch(
        "apps.api.views.organization.CurrentOrganizationView.put",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.put(url, format="json", **make_user_auth_headers(tester, token))

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
def test_organization_get_telegram_verification_code_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, tester, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:api-get-telegram-verification-code")
    response = client.get(url, format="json", **make_user_auth_headers(tester, token))

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
def test_organization_get_channel_verification_code_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, tester, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:api-get-channel-verification-code") + "?backend=TESTONLY"
    response = client.get(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_organization_get_channel_verification_code_ok(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    organization, tester, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    url = reverse("api-internal:api-get-channel-verification-code") + "?backend=TESTONLY"
    with patch(
        "apps.base.tests.messaging_backend.TestOnlyBackend.generate_channel_verification_code",
        return_value="the-code",
    ) as mock_generate_code:
        response = client.get(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == "the-code"
    mock_generate_code.assert_called_once_with(organization)


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
def test_organization_get_mattermost_setup_details(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, tester, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    url = reverse("api-internal:api-get-mattermost-setup-details")
    response = client.get(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_organization_get_channel_verification_code_invalid(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    _, tester, token = make_organization_and_user_with_plugin_token()
    client = APIClient()

    url = reverse("api-internal:api-get-channel-verification-code") + "?backend=INVALID"
    response = client.get(url, format="json", **make_user_auth_headers(tester, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_get_organization_slack_config_checks(
    make_organization_and_user_with_plugin_token,
    make_slack_team_identity,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    client = APIClient()
    url = reverse("api-internal:api-organization-config-checks")
    expected_result = {
        "is_chatops_connected": False,
        "is_integration_chatops_connected": False,
        "mattermost": {
            "env_status": True,
            "is_integrated": False,
        },
    }
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result

    # connect Slack
    slack_team_identity = make_slack_team_identity()
    organization.slack_team_identity = slack_team_identity
    organization.save()

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    expected_result["is_chatops_connected"] = True
    assert response.json() == expected_result

    # create integration
    integration = make_alert_receive_channel(organization)

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result

    # connect integration to Slack (no channel means default channel)
    channel_filter = make_channel_filter(integration, notify_in_slack=True)

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    expected_result["is_integration_chatops_connected"] = True
    assert response.json() == expected_result

    # connect integration to Slack (set a channel)
    channel_filter.slack_channel_id = "C123456"
    channel_filter.save()

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    expected_result["is_integration_chatops_connected"] = True
    assert response.json() == expected_result

    # TODO: Add test to validate mattermost is integrated once integration PR changes are made


@pytest.mark.django_db
def test_get_organization_telegram_config_checks(
    make_organization_and_user_with_plugin_token,
    make_telegram_channel,
    make_alert_receive_channel,
    make_channel_filter,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    client = APIClient()
    url = reverse("api-internal:api-organization-config-checks")
    expected_result = {
        "is_chatops_connected": False,
        "is_integration_chatops_connected": False,
        "mattermost": {
            "env_status": True,
            "is_integrated": False,
        },
    }
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result

    # connect Telegram
    make_telegram_channel(organization)

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    expected_result["is_chatops_connected"] = True
    assert response.json() == expected_result

    # create integration
    integration = make_alert_receive_channel(organization)

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_result

    # connect integration to Slack
    make_channel_filter(integration, notify_in_telegram=True)

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    expected_result["is_integration_chatops_connected"] = True
    assert response.json() == expected_result

    # TODO: Add test to validate mattermost is integrated once integration PR changes are made
