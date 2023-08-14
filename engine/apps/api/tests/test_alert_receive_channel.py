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
@pytest.mark.parametrize(
    "query_param,should_be_unpaginated",
    [
        ("True", True),
        ("true", True),
        ("TRUE", True),
        ("", False),
        ("False", False),
        ("false", False),
        ("FALSE", False),
    ],
)
def test_list_alert_receive_channel_skip_pagination_for_grafana_alerting(
    alert_receive_channel_internal_api_setup,
    make_user_auth_headers,
    query_param,
    should_be_unpaginated,
):
    user, token, _ = alert_receive_channel_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-list")
    response = client.get(f"{url}?skip_pagination={query_param}", format="json", **make_user_auth_headers(user, token))
    results = response.json()
    assert response.status_code == status.HTTP_200_OK

    if should_be_unpaginated:
        assert type(results) == list
        assert len(results) > 0
    else:
        assert type(results["results"]) == list
        assert len(results["results"]) > 0


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
def test_create_invalid_alert_receive_channel_type(alert_receive_channel_internal_api_setup, make_user_auth_headers):
    user, token, _ = alert_receive_channel_internal_api_setup

    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-list")

    response_1 = client.post(
        url,
        data={"integration": "random123", "verbal_name": "Random 123"},
        format="json",
        **make_user_auth_headers(user, token),
    )
    response_2 = client.post(
        url, data={"verbal_name": "Random 123"}, format="json", **make_user_auth_headers(user, token)
    )

    assert response_1.status_code == status.HTTP_400_BAD_REQUEST
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST


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
    assert len(response.json()["results"]) == 1


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
    assert len(response.json()["results"]) == 1


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
    assert len(response.json()["results"]) == 2

    response = client.get(
        f"{url}?search=zabbix", content_type="application/json", **make_user_auth_headers(user, token)
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 0

    response = client.get(f"{url}?search=prod", content_type="application/json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1


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
@pytest.mark.parametrize("template_name", ["title", "message", "image_url"])
@pytest.mark.parametrize("notification_channel", ["slack", "web", "telegram"])
def test_alert_receive_channel_preview_template_dynamic_payload(
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
        "template_body": "{{ payload.foo }}",
        "template_name": f"{notification_channel}_{template_name}",
        "payload": {"foo": "bar"},
    }

    response = client.post(url, data=data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    if notification_channel == "web" and template_name == "message":
        assert response.data["preview"] == "<p>bar</p>"
    else:
        assert response.data["preview"] == "bar"


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

    # return 200 on change team for integration as user is Admin
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
    assert response.json()["results"][0]["value"] == alert_receive_channel.public_primary_key


@pytest.mark.django_db
def test_create_alert_receive_channels_direct_paging(
    make_organization_and_user_with_plugin_token, make_team, make_alert_receive_channel, make_user_auth_headers
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    team = make_team(organization)

    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-list")

    response_1 = client.post(
        url, data={"integration": "direct_paging"}, format="json", **make_user_auth_headers(user, token)
    )
    response_2 = client.post(
        url, data={"integration": "direct_paging"}, format="json", **make_user_auth_headers(user, token)
    )

    response_3 = client.post(
        url,
        data={"integration": "direct_paging", "team": team.public_primary_key},
        format="json",
        **make_user_auth_headers(user, token),
    )
    response_4 = client.post(
        url,
        data={"integration": "direct_paging", "team": team.public_primary_key},
        format="json",
        **make_user_auth_headers(user, token),
    )

    # Check direct paging integration for "No team" is created
    assert response_1.status_code == status.HTTP_201_CREATED
    # Check direct paging integration is not created, as it already exists for "No team"
    assert response_2.status_code == status.HTTP_400_BAD_REQUEST

    # Check direct paging integration for team is created
    assert response_3.status_code == status.HTTP_201_CREATED
    # Check direct paging integration is not created, as it already exists for team
    assert response_4.status_code == status.HTTP_400_BAD_REQUEST
    assert response_4.json()["detail"] == AlertReceiveChannel.DuplicateDirectPagingError.DETAIL


@pytest.mark.django_db
def test_update_alert_receive_channels_direct_paging(
    make_organization_and_user_with_plugin_token, make_team, make_alert_receive_channel, make_user_auth_headers
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    team = make_team(organization)
    integration = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING, team=None
    )
    make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING, team=team)

    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": integration.public_primary_key})

    # Move direct paging integration from "No team" to team
    response = client.put(
        url,
        data={"integration": "direct_paging", "team": team.public_primary_key},
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == AlertReceiveChannel.DuplicateDirectPagingError.DETAIL


@pytest.mark.django_db
def test_start_maintenance_integration(
    make_user_auth_headers,
    make_organization_and_user_with_plugin_token,
    make_escalation_chain,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    make_escalation_chain(organization)
    alert_receive_channel = make_alert_receive_channel(organization)

    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel-start-maintenance", kwargs={"pk": alert_receive_channel.public_primary_key}
    )

    data = {
        "mode": AlertReceiveChannel.MAINTENANCE,
        "duration": AlertReceiveChannel.DURATION_ONE_HOUR.total_seconds(),
        "type": "alert_receive_channel",
    }
    response = client.post(url, data=data, format="json", **make_user_auth_headers(user, token))

    alert_receive_channel.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert alert_receive_channel.maintenance_mode == AlertReceiveChannel.MAINTENANCE
    assert alert_receive_channel.maintenance_duration == AlertReceiveChannel.DURATION_ONE_HOUR
    assert alert_receive_channel.maintenance_uuid is not None
    assert alert_receive_channel.maintenance_started_at is not None
    assert alert_receive_channel.maintenance_author is not None


@pytest.mark.django_db
def test_stop_maintenance_integration(
    mock_start_disable_maintenance_task,
    make_user_auth_headers,
    make_organization_and_user_with_plugin_token,
    make_escalation_chain,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    make_escalation_chain(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()
    mode = AlertReceiveChannel.MAINTENANCE
    duration = AlertReceiveChannel.DURATION_ONE_HOUR.seconds
    alert_receive_channel.start_maintenance(mode, duration, user)
    url = reverse(
        "api-internal:alert_receive_channel-stop-maintenance", kwargs={"pk": alert_receive_channel.public_primary_key}
    )
    data = {
        "type": "alert_receive_channel",
    }
    response = client.post(url, data=data, format="json", **make_user_auth_headers(user, token))
    alert_receive_channel.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert alert_receive_channel.maintenance_mode is None
    assert alert_receive_channel.maintenance_duration is None
    assert alert_receive_channel.maintenance_uuid is None
    assert alert_receive_channel.maintenance_started_at is None
    assert alert_receive_channel.maintenance_author is None


@pytest.mark.django_db
def test_alert_receive_channel_send_demo_alert(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel-send-demo-alert",
        kwargs={"pk": alert_receive_channel.public_primary_key},
    )

    response = client.post(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_alert_receive_channel_send_demo_alert_not_enabled(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_MANUAL)
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel-send-demo-alert",
        kwargs={"pk": alert_receive_channel.public_primary_key},
    )

    response = client.post(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_alert_receive_channel_get_connected_contact_points_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    )

    url = reverse(
        "api-internal:alert_receive_channel-connected-contact-points",
        kwargs={"pk": alert_receive_channel.public_primary_key},
    )

    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.connected_contact_points",
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
def test_alert_receive_channel_get_contact_points_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()

    url = reverse(
        "api-internal:alert_receive_channel-contact-points",
    )

    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.contact_points",
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
        (LegacyAccessControlRole.EDITOR, status.HTTP_403_FORBIDDEN),
        (LegacyAccessControlRole.VIEWER, status.HTTP_403_FORBIDDEN),
    ],
)
def test_alert_receive_channel_connect_contact_point_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    )

    url = reverse(
        "api-internal:alert_receive_channel-connect-contact-point",
        kwargs={"pk": alert_receive_channel.public_primary_key},
    )

    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.connect_contact_point",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", data={}, **make_user_auth_headers(user, token))
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
def test_alert_receive_channel_create_contact_point_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    )

    url = reverse(
        "api-internal:alert_receive_channel-create-contact-point",
        kwargs={"pk": alert_receive_channel.public_primary_key},
    )

    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.create_contact_point",
        return_value=Response(
            status=status.HTTP_201_CREATED,
        ),
    ):
        response = client.post(url, format="json", data={}, **make_user_auth_headers(user, token))
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
def test_alert_receive_channel_disconnect_contact_point_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    role,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role)
    client = APIClient()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    )

    url = reverse(
        "api-internal:alert_receive_channel-disconnect-contact-point",
        kwargs={"pk": alert_receive_channel.public_primary_key},
    )

    with patch(
        "apps.api.views.alert_receive_channel.AlertReceiveChannelView.disconnect_contact_point",
        return_value=Response(
            status=status.HTTP_200_OK,
        ),
    ):
        response = client.post(url, format="json", data={}, **make_user_auth_headers(user, token))
        assert response.status_code == expected_status


@patch(
    "apps.alerts.grafana_alerting_sync_manager.GrafanaAlertingSyncManager.get_connected_contact_points",
    return_value=True,
)
@patch(
    "apps.alerts.grafana_alerting_sync_manager.GrafanaAlertingSyncManager.connect_contact_point",
    return_value=(True, ""),
)
@patch(
    "apps.alerts.grafana_alerting_sync_manager.GrafanaAlertingSyncManager.disconnect_contact_point",
    return_value=(True, ""),
)
@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint,expected_status",
    [
        ("connected-contact-points", status.HTTP_200_OK),
        ("connect-contact-point", status.HTTP_200_OK),
        ("create-contact-point", status.HTTP_201_CREATED),
        ("disconnect-contact-point", status.HTTP_200_OK),
    ],
)
def test_alert_receive_channel_contact_points_endpoints(
    mocked_get_connected_contact_points,
    mocked_get_connect_contact_point,
    mocked_get_disconnect_contact_point,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    endpoint,
    expected_status,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING
    )

    url = reverse(
        f"api-internal:alert_receive_channel-{endpoint}",
        kwargs={"pk": alert_receive_channel.public_primary_key},
    )
    if endpoint == "connected-contact-points":
        response = client.get(url, format="json", **make_user_auth_headers(user, token))
    else:
        data = {
            "datasource_uid": "test_datasource",
            "contact_point_name": "test contact point",
        }
        response = client.post(url, format="json", data=data, **make_user_auth_headers(user, token))
    assert response.status_code == expected_status


@patch("apps.alerts.grafana_alerting_sync_manager.GrafanaAlertingSyncManager.get_contact_points", return_value=[])
@pytest.mark.django_db
def test_alert_receive_channel_get_contact_points(
    mocked_get_contact_points,
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-contact-points")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint",
    ["connected-contact-points", "connect-contact-point", "create-contact-point", "disconnect-contact-point"],
)
def test_alert_receive_channel_contact_points_wrong_integration(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    make_alert_receive_channel,
    endpoint,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    client = APIClient()
    alert_receive_channel = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA
    )

    url = reverse(
        f"api-internal:alert_receive_channel-{endpoint}",
        kwargs={"pk": alert_receive_channel.public_primary_key},
    )
    if endpoint == "connected-contact-points":
        response = client.get(url, format="json", **make_user_auth_headers(user, token))
    else:
        response = client.post(url, format="json", data={}, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST
