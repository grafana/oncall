import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.alerts.models import AlertReceiveChannel, EscalationPolicy
from apps.api.permissions import LegacyAccessControlRole


@pytest.fixture()
def alert_receive_channel_internal_api_setup(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_escalation_chain,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    make_escalation_chain(organization)
    return user, token, alert_receive_channel


@pytest.mark.django_db
def test_get_alert_receive_channel(alert_receive_channel_internal_api_setup, make_user_auth_headers):
    user, token, _ = alert_receive_channel_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-list")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_heartbeat_data_absence_alert_receive_channel(alert_receive_channel_internal_api_setup, make_user_auth_headers):
    """
    We get AlertReceiveChannel and there is no related heartbeat model object.
    """
    user, token, alert_receive_channel = alert_receive_channel_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["heartbeat"] is None


@pytest.mark.django_db
def test_heartbeat_data_presence_alert_receive_channel(
    alert_receive_channel_internal_api_setup,
    make_integration_heartbeat,
    make_user_auth_headers,
):
    """
    We get AlertReceiveChannel and there IS related heartbeat model object.
    That is why we check for heartbeat model properties.
    """
    user, token, alert_receive_channel = alert_receive_channel_internal_api_setup
    _ = make_integration_heartbeat(alert_receive_channel)
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    expected_heartbeat_payload = {
        "id": alert_receive_channel.integration_heartbeat.public_primary_key,
        "last_heartbeat_time_verbal": None,
        "alert_receive_channel": alert_receive_channel.public_primary_key,
        "link": alert_receive_channel.integration_heartbeat.link,
        "timeout_seconds": 60,
        "status": False,
        "instruction": response.json()["heartbeat"]["instruction"],
    }
    assert response.json()["heartbeat"] is not None
    assert response.json()["heartbeat"] == expected_heartbeat_payload


@pytest.mark.django_db
def test_create_alert_receive_channel(alert_receive_channel_internal_api_setup, make_user_auth_headers):
    user, token, _ = alert_receive_channel_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-list")
    data = {
        "integration": AlertReceiveChannel.INTEGRATION_GRAFANA,
        "team": None,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_create_invalid_alert_receive_channel(alert_receive_channel_internal_api_setup, make_user_auth_headers):
    user, token, _ = alert_receive_channel_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-list")
    data = {"integration": AlertReceiveChannel.INTEGRATION_GRAFANA, "verbal_name": ""}
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_alert_receive_channel(alert_receive_channel_internal_api_setup, make_user_auth_headers):
    user, token, alert_receive_channel = alert_receive_channel_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})
    response = client.patch(
        url,
        data=json.dumps({"verbal_name": "test_set_verbal_name"}),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    alert_receive_channel.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert alert_receive_channel.verbal_name == "test_set_verbal_name"


@pytest.mark.django_db
def test_integration_filter_by_maintenance(
    alert_receive_channel_internal_api_setup,
    make_user_auth_headers,
    mock_start_disable_maintenance_task,
    mock_alert_shooting_step_post_alert_group_to_slack,
):
    user, token, alert_receive_channel = alert_receive_channel_internal_api_setup
    client = APIClient()
    mode = AlertReceiveChannel.MAINTENANCE
    duration = AlertReceiveChannel.DURATION_ONE_HOUR.seconds
    alert_receive_channel.start_maintenance(mode, duration, user)
    url = reverse("api-internal:alert_receive_channel-list")
    response = client.get(
        f"{url}?maintenance_mode={AlertReceiveChannel.MAINTENANCE}",
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1


@pytest.mark.django_db
def test_integration_filter_by_debug(
    alert_receive_channel_internal_api_setup,
    make_user_auth_headers,
    mock_start_disable_maintenance_task,
    mock_alert_shooting_step_post_alert_group_to_slack,
):
    user, token, alert_receive_channel = alert_receive_channel_internal_api_setup
    client = APIClient()
    mode = AlertReceiveChannel.DEBUG_MAINTENANCE
    duration = AlertReceiveChannel.DURATION_ONE_HOUR.seconds
    with patch("apps.slack.utils.post_message_to_channel"):
        alert_receive_channel.start_maintenance(mode, duration, user)
    url = reverse("api-internal:alert_receive_channel-list")
    response = client.get(
        f"{url}?maintenance_mode={AlertReceiveChannel.DEBUG_MAINTENANCE}",
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1


@pytest.mark.django_db
def test_integration_search(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    make_alert_receive_channel(organization, verbal_name="grafana_prod")
    make_alert_receive_channel(organization, verbal_name="grafana_stage")
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-list")

    response = client.get(
        f"{url}?search=grafana", content_type="application/json", **make_user_auth_headers(user, token)
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 2

    response = client.get(
        f"{url}?search=zabbix", content_type="application/json", **make_user_auth_headers(user, token)
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 0

    response = client.get(f"{url}?search=prod", content_type="application/json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data) == 1


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_receive_channel_create_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-list")
    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.create",
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
def test_alert_receive_channel_update_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})

    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.update",
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
        (LegacyAccessControlRole.ADMIN, status.HTTP_204_NO_CONTENT),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_receive_channel_delete_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})
    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.destroy",
        return_value=Response(
            status=status.HTTP_204_NO_CONTENT,
        ),
    ):
        response = client.delete(url, format="json", **make_user_auth_headers(user, token))

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
def test_alert_receive_channel_list_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-list")

    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.list",
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
def test_alert_receive_channel_detail_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})

    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.retrieve",
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
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_receive_channel_send_demo_alert_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel-send-demo-alert", kwargs={"pk": alert_receive_channel.public_primary_key}
    )

    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.send_demo_alert",
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
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_alert_receive_channel_integration_options_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-integration-options")

    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.integration_options",
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
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_receive_channel_preview_template_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()
    url = reverse(
        "api-internal:alert_receive_channel-preview-template", kwargs={"pk": alert_receive_channel.public_primary_key}
    )

    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.preview_template",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize("template_name", ["title", "message", "image_url"])
@pytest.mark.parametrize("notification_channel", ["slack", "web", "telegram"])
def test_alert_receive_channel_preview_template_require_notification_channel(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    template_name,
    notification_channel,
    make_alert_group,
    make_alert,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    client = APIClient()
    url = reverse(
        "api-internal:alert_receive_channel-preview-template", kwargs={"pk": alert_receive_channel.public_primary_key}
    )
    data = {
        "template_body": "Template",
        "template_name": template_name,
    }

    response = client.post(url, data=data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_400_BAD_REQUEST

    data = {
        "template_body": "Template",
        "template_name": f"{notification_channel}_{template_name}",
    }

    response = client.post(url, data=data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_receive_channel_change_team_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()
    url = reverse(
        "api-internal:alert_receive_channel-change-team", kwargs={"pk": alert_receive_channel.public_primary_key}
    )

    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.change_team",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.put(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_alert_receive_channel_change_team(
    make_organization_and_user_with_plugin_token,
    make_team,
    make_user_for_organization,
    make_user_auth_headers,
    make_alert_receive_channel,
    make_channel_filter,
    make_integration_escalation_chain_route_escalation_policy,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    team = make_team(organization)
    integration, escalation_chain, _, escalation_policy = make_integration_escalation_chain_route_escalation_policy(
        organization, EscalationPolicy.STEP_NOTIFY_MULTIPLE_USERS
    )
    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-change-team", kwargs={"pk": integration.public_primary_key})

    assert integration.team != team

    # return 400 on change team for integration if user is not a member of chosen team
    response = client.put(
        f"{url}?team_id={team.public_primary_key}", format="json", **make_user_auth_headers(user, token)
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    integration.refresh_from_db()
    assert integration.team != team

    team.users.add(user)
    # return 400 on change team for integration if escalation_chain is connected to another integration
    another_integration = make_alert_receive_channel(organization)
    another_channel_filter = make_channel_filter(another_integration, escalation_chain=escalation_chain)
    response = client.put(
        f"{url}?team_id={team.public_primary_key}", format="json", **make_user_auth_headers(user, token)
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    integration.refresh_from_db()
    assert integration.team != team

    another_channel_filter.escalation_chain = None
    another_channel_filter.save()

    # return 400 on change team for integration if user from escalation policy is not a member of team
    another_user = make_user_for_organization(organization)
    escalation_policy.notify_to_users_queue.add(another_user)
    response = client.put(
        f"{url}?team_id={team.public_primary_key}", format="json", **make_user_auth_headers(user, token)
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    integration.refresh_from_db()
    assert integration.team != team

    team.users.add(another_user)
    # otherwise change team
    response = client.put(
        f"{url}?team_id={team.public_primary_key}", format="json", **make_user_auth_headers(user, token)
    )
    assert response.status_code == status.HTTP_200_OK
    integration.refresh_from_db()
    assert integration.team == team


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_alert_receive_channel_counters_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel-counters",
    )

    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.counters",
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
def test_alert_receive_channel_counters_per_integration_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    alert_receive_channel = make_alert_receive_channel(organization)

    url = reverse(
        "api-internal:alert_receive_channel-counters-per-integration",
        kwargs={"pk": alert_receive_channel.public_primary_key},
    )

    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.counters_per_integration",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.get(url, format="json", **make_user_auth_headers(user, token))

        assert response.status_code == expected_status


@pytest.mark.django_db
def test_get_alert_receive_channels_direct_paging_hidden_from_list(
    make_organization_and_user_with_plugin_token, make_alert_receive_channel, make_user_auth_headers
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    make_alert_receive_channel(user.organization, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING)

    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-list")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    # Check no direct paging integrations in the response
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.django_db
def test_get_alert_receive_channels_direct_paging_present_for_filters(
    make_organization_and_user_with_plugin_token, make_alert_receive_channel, make_user_auth_headers
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(
        user.organization, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING
    )

    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-list")
    response = client.get(url + "?filters=true", format="json", **make_user_auth_headers(user, token))

    # Check direct paging integration is in the response
    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]["value"] == alert_receive_channel.public_primary_key
