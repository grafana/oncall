import json
from unittest.mock import ANY, patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.test import APIClient

from apps.alerts.models import AlertReceiveChannel, EscalationPolicy
from apps.api.permissions import LegacyAccessControlRole
from apps.labels.models import LabelKeyCache, LabelValueCache


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
def test_get_alert_receive_channel_by_integration_ne(
    make_organization_and_user_with_plugin_token, make_user_auth_headers, make_alert_receive_channel
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA)
    make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING)
    make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING)

    client = APIClient()
    url = f"{reverse('api-internal:alert_receive_channel-list')}?integration_ne={AlertReceiveChannel.INTEGRATION_DIRECT_PAGING}"

    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    results = response.json()["results"]

    assert response.status_code == status.HTTP_200_OK
    assert len(results) == 2

    for result in results:
        assert result["integration"] != AlertReceiveChannel.INTEGRATION_DIRECT_PAGING


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
def test_alert_receive_channel_name_uniqueness(
    alert_receive_channel_internal_api_setup,
    make_team,
    make_user_auth_headers,
):
    user, token, alert_receive_channel = alert_receive_channel_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-list")
    data = {
        "integration": AlertReceiveChannel.INTEGRATION_GRAFANA,
        "team": alert_receive_channel.team.public_primary_key if alert_receive_channel.team else None,
        "verbal_name": alert_receive_channel.verbal_name,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # name can be reused in a different team
    another_team = make_team(alert_receive_channel.organization)
    data = {
        "integration": AlertReceiveChannel.INTEGRATION_GRAFANA,
        "team": another_team.public_primary_key,
        "verbal_name": alert_receive_channel.verbal_name,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_201_CREATED

    # update works
    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})
    response = client.put(
        url,
        data=json.dumps(
            {
                "team": alert_receive_channel.team,
                "verbal_name": alert_receive_channel.verbal_name,
                "description": "update description",
            }
        ),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )
    assert response.status_code == status.HTTP_200_OK

    # but updating team will fail if name exists
    response = client.put(
        url,
        data=json.dumps(
            {
                "team": another_team.public_primary_key,
                "verbal_name": alert_receive_channel.verbal_name,
            }
        ),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_alert_receive_channel_name_duplicated(
    alert_receive_channel_internal_api_setup,
    make_alert_receive_channel,
    make_user_auth_headers,
):
    # this could happen in case a team is removed and integrations are set to have "no team"
    user, token, alert_receive_channel = alert_receive_channel_internal_api_setup
    # another integration with the same verbal name
    make_alert_receive_channel(
        alert_receive_channel.organization,
        verbal_name=alert_receive_channel.verbal_name,
    )

    client = APIClient()

    # updating team will require changing the name or the team
    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})
    response = client.put(
        url,
        data=json.dumps({"verbal_name": alert_receive_channel.verbal_name}),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    response = client.put(
        url,
        data=json.dumps({"verbal_name": "a new name"}),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )
    assert response.status_code == status.HTTP_200_OK


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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
def test_cant_create_alert_receive_channels_direct_paging(
    make_organization_and_user_with_plugin_token, make_team, make_alert_receive_channel, make_user_auth_headers
):
    organization, user, token = make_organization_and_user_with_plugin_token()

    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-list")
    response = client.post(
        url, data={"integration": "direct_paging"}, format="json", **make_user_auth_headers(user, token)
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST


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
def test_cant_delete_direct_paging_integration(
    make_organization_and_user_with_plugin_token, make_alert_receive_channel, make_user_auth_headers
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    integration = make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING)

    # check allow_delete is False (so the frontend can hide the delete button)
    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": integration.public_primary_key})
    response = client.get(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["allow_delete"] is False

    # check delete is not allowed
    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": integration.public_primary_key})
    response = client.delete(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST


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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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
        (LegacyAccessControlRole.NONE, status.HTTP_403_FORBIDDEN),
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


@pytest.mark.django_db
def test_integration_filter_by_labels(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_integration_label_association,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel_1 = make_alert_receive_channel(organization)
    alert_receive_channel_2 = make_alert_receive_channel(organization)
    associated_label_1 = make_integration_label_association(organization, alert_receive_channel_1)
    associated_label_2 = make_integration_label_association(organization, alert_receive_channel_1)
    alert_receive_channel_2.labels.create(
        key=associated_label_1.key, value=associated_label_1.value, organization=organization
    )

    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-list")
    response = client.get(
        f"{url}?label={associated_label_1.key_id}:{associated_label_1.value_id}",
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 2

    response = client.get(
        f"{url}?label={associated_label_1.key_id}:{associated_label_1.value_id}"
        f"&label={associated_label_2.key_id}:{associated_label_2.value_id}",
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()["results"]) == 1
    assert response.json()["results"][0]["id"] == alert_receive_channel_1.public_primary_key


@pytest.mark.django_db
def test_update_alert_receive_channel_labels(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})
    key_id = "testkey"
    value_id = "testvalue"
    data = {
        "labels": [
            {
                "key": {"id": key_id, "name": "test", "prescribed": False},
                "value": {"id": value_id, "name": "testv", "prescribed": False},
            }
        ]
    }
    response = client.patch(
        url,
        data=json.dumps(data),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    alert_receive_channel.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert alert_receive_channel.labels.count() == 1
    label = alert_receive_channel.labels.first()
    assert label.key_id == key_id
    assert label.value_id == value_id

    response = client.patch(
        url,
        data=json.dumps({"labels": []}),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    alert_receive_channel.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert alert_receive_channel.labels.count() == 0


@pytest.mark.django_db
def test_update_alert_receive_channel_presribed_labels(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})
    key_id = "testkey"
    value_id = "testvalue"
    data = {
        "labels": [
            {
                "key": {"id": key_id, "name": "test", "prescribed": True},
                "value": {"id": value_id, "name": "testv", "prescribed": True},
            }
        ]
    }
    response = client.patch(
        url,
        data=json.dumps(data),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    alert_receive_channel.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert alert_receive_channel.labels.count() == 1
    label = alert_receive_channel.labels.first()
    assert label.key_id == key_id
    assert label.value_id == value_id

    # Check if cached labels are prescribed
    assert label.key.prescribed is True
    assert label.value.prescribed is True

    response = client.patch(
        url,
        data=json.dumps({"labels": []}),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    alert_receive_channel.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    assert alert_receive_channel.labels.count() == 0


@pytest.mark.django_db
def test_update_alert_receive_channel_labels_duplicate_key(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    client = APIClient()

    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})
    key_id = "testkey"
    data = {
        "labels": [
            {"key": {"id": key_id, "name": "test"}, "value": {"id": "testvalue1", "name": "testv1"}},
            {"key": {"id": key_id, "name": "test"}, "value": {"id": "testvalue2", "name": "testv2"}},
        ]
    }
    response = client.patch(
        url,
        data=json.dumps(data),
        content_type="application/json",
        **make_user_auth_headers(user, token),
    )

    alert_receive_channel.refresh_from_db()

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert alert_receive_channel.labels.count() == 0


@pytest.mark.django_db
def test_alert_group_labels_get(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_label_key_and_value,
    make_integration_label_association,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    label_key, label_value = make_label_key_and_value(organization)
    label_key_1, _ = make_label_key_and_value(organization)

    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})

    response = client.get(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["alert_group_labels"] == {"inheritable": {}, "custom": [], "template": None}

    label = make_integration_label_association(organization, alert_receive_channel)

    template = "{{ payload.labels | tojson }}"
    alert_receive_channel.alert_group_labels_template = template

    alert_receive_channel.alert_group_labels_custom = [
        (label_key.id, label_value.id, None),
        (label_key_1.id, None, "{{ payload.foo }}"),
    ]
    alert_receive_channel.save(update_fields=["alert_group_labels_custom", "alert_group_labels_template"])

    response = client.get(url, **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["alert_group_labels"] == {
        "inheritable": {label.key_id: True},
        "custom": [
            {
                "key": {"id": label_key.id, "name": label_key.name, "prescribed": False},
                "value": {"id": label_value.id, "name": label_value.name, "prescribed": False},
            },
            {
                "key": {"id": label_key_1.id, "name": label_key_1.name, "prescribed": False},
                "value": {"id": None, "name": "{{ payload.foo }}", "prescribed": False},
            },
        ],
        "template": template,
    }


@pytest.mark.django_db
def test_alert_group_labels_put(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_integration_label_association,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    label_1 = make_integration_label_association(organization, alert_receive_channel)
    label_2 = make_integration_label_association(organization, alert_receive_channel, inheritable=False)
    label_3 = make_integration_label_association(organization, alert_receive_channel, inheritable=False)

    custom = [
        # plain label
        {
            "key": {"id": label_2.key.id, "name": label_2.key.name, "prescribed": False},
            "value": {"id": label_2.value.id, "name": label_2.value.name, "prescribed": False},
        },
        # plain label not present in DB cache
        {
            "key": {"id": "hello", "name": "world", "prescribed": False},
            "value": {"id": "foo", "name": "bar", "prescribed": False},
        },
        # templated label
        {
            "key": {"id": label_3.key.id, "name": label_3.key.name, "prescribed": False},
            "value": {
                "id": None,
                "name": "{{ payload.foo }}",
                "prescribed": False,
            },
        },
    ]
    template = "{{ payload.labels | tojson }}"  # advanced template

    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})
    data = {
        "alert_group_labels": {
            "inheritable": {label_1.key_id: False, label_2.key_id: True, label_3.key_id: False},
            "custom": custom,
            "template": template,
        }
    }
    response = client.put(url, data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["alert_group_labels"] == {
        "inheritable": {label_1.key_id: False, label_2.key_id: True, label_3.key_id: False},
        "custom": custom,
        "template": template,
    }

    alert_receive_channel.refresh_from_db()
    assert alert_receive_channel.alert_group_labels_custom == [
        [label_2.key_id, label_2.value_id, None],
        ["hello", "foo", None],
        [label_3.key_id, None, "{{ payload.foo }}"],
    ]
    assert alert_receive_channel.alert_group_labels_template == template

    # check label keys & values are created
    key = LabelKeyCache.objects.filter(id="hello", name="world", organization=organization).first()
    assert key is not None
    assert LabelValueCache.objects.filter(key=key, id="foo", name="bar").exists()


@pytest.mark.django_db
def test_alert_group_labels_put_none(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)

    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})
    response = client.put(url, {"verbal_name": "123"}, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["verbal_name"] == "123"
    assert response.json()["alert_group_labels"] == {"inheritable": {}, "custom": [], "template": None}


@pytest.mark.django_db
def test_alert_group_labels_post(alert_receive_channel_internal_api_setup, make_user_auth_headers):
    user, token, _ = alert_receive_channel_internal_api_setup

    labels = [
        {
            "key": {"id": "test", "name": "test", "prescribed": False},
            "value": {"id": "123", "name": "123", "prescribed": False},
        }
    ]
    alert_group_labels = {
        "inheritable": {"test": False},
        "custom": [
            {
                "key": {"id": "test", "name": "test", "prescribed": False},
                "value": {"id": "123", "name": "123", "prescribed": False},
            }
        ],
        "template": "{{ payload.labels | tojson }}",
    }
    data = {
        "integration": AlertReceiveChannel.INTEGRATION_GRAFANA,
        "team": None,
        "labels": labels,
        "alert_group_labels": alert_group_labels,
    }

    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-list")
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["labels"] == labels
    assert response.json()["alert_group_labels"] == alert_group_labels

    alert_receive_channel = AlertReceiveChannel.objects.get(public_primary_key=response.json()["id"])
    assert alert_receive_channel.alert_group_labels_custom == [["test", "123", None]]
    assert alert_receive_channel.alert_group_labels_template == "{{ payload.labels | tojson }}"


@pytest.mark.django_db
def test_team_not_updated_if_not_in_data(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_team,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    team = make_team(organization)
    alert_receive_channel = make_alert_receive_channel(organization, team=team)

    assert alert_receive_channel.team == team

    client = APIClient()
    url = reverse("api-internal:alert_receive_channel-detail", kwargs={"pk": alert_receive_channel.public_primary_key})
    data = {"verbal_name": "test integration"}
    response = client.put(url, data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["team"] == alert_receive_channel.team.public_primary_key

    alert_receive_channel.refresh_from_db()
    assert alert_receive_channel.team == team


def _webhook_data(webhook_id=ANY, webhook_name=ANY, webhook_url=ANY, alert_receive_channel_id=ANY):
    return {
        "authorization_header": None,
        "data": None,
        "forward_all": True,
        "headers": None,
        "http_method": "POST",
        "id": webhook_id,
        "integration_filter": [alert_receive_channel_id],
        "is_legacy": False,
        "is_webhook_enabled": True,
        "labels": [],
        "last_response_log": {
            "content": "",
            "event_data": "",
            "request_data": "",
            "request_headers": "",
            "request_trigger": "",
            "status_code": None,
            "timestamp": None,
            "url": "",
        },
        "name": webhook_name,
        "password": None,
        "preset": None,
        "team": None,
        "trigger_template": None,
        "trigger_type": "0",
        "trigger_type_name": "Escalation step",
        "url": webhook_url,
        "username": None,
    }


@pytest.mark.django_db
def test_alert_receive_channel_webhooks_get(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_custom_webhook,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    webhook = make_custom_webhook(organization, is_from_connected_integration=True)
    webhook.filtered_integrations.set([alert_receive_channel])

    # create 2 webhooks that are not connected to the integration
    make_custom_webhook(organization)
    webhook2 = make_custom_webhook(organization, is_from_connected_integration=False)
    webhook2.filtered_integrations.set([alert_receive_channel])

    client = APIClient()
    url = reverse(
        "api-internal:alert_receive_channel-webhooks-get", kwargs={"pk": alert_receive_channel.public_primary_key}
    )
    response = client.get(url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [
        _webhook_data(
            webhook_id=webhook.public_primary_key,
            alert_receive_channel_id=alert_receive_channel.public_primary_key,
        )
    ]


@pytest.mark.django_db
def test_alert_receive_channel_webhooks_post(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)

    client = APIClient()
    url = reverse(
        "api-internal:alert_receive_channel-webhooks-get", kwargs={"pk": alert_receive_channel.public_primary_key}
    )

    data = {
        "name": None,
        "enabled": True,
        "url": "http://example.com/",
        "http_method": "POST",
        "trigger_type": "0",
        "trigger_template": None,
    }
    response = client.post(url, data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == _webhook_data(
        webhook_url="http://example.com/",
        alert_receive_channel_id=alert_receive_channel.public_primary_key,
    )
    assert alert_receive_channel.webhooks.get().is_from_connected_integration is True


@pytest.mark.django_db
def test_alert_receive_channel_webhooks_put(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_custom_webhook,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    webhook = make_custom_webhook(organization, is_from_connected_integration=True)
    webhook.filtered_integrations.set([alert_receive_channel])

    client = APIClient()
    url = reverse(
        "api-internal:alert_receive_channel-webhooks-put",
        kwargs={"pk": alert_receive_channel.public_primary_key, "webhook_id": webhook.public_primary_key},
    )

    data = _webhook_data(
        webhook_id=webhook.public_primary_key,
        webhook_name="Test",
        webhook_url="http://example.com/",
        alert_receive_channel_id=alert_receive_channel.public_primary_key,
    )
    response = client.put(url, data, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    webhook.refresh_from_db()
    assert webhook.url == "http://example.com/"


@pytest.mark.django_db
def test_alert_receive_channel_webhooks_delete(
    make_organization_and_user_with_plugin_token,
    make_alert_receive_channel,
    make_custom_webhook,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    webhook = make_custom_webhook(organization, is_from_connected_integration=True)
    webhook.filtered_integrations.set([alert_receive_channel])

    client = APIClient()
    url = reverse(
        "api-internal:alert_receive_channel-webhooks-put",
        kwargs={"pk": alert_receive_channel.public_primary_key, "webhook_id": webhook.public_primary_key},
    )
    response = client.delete(url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    webhook.refresh_from_db()
    assert webhook.deleted_at is not None
    assert alert_receive_channel.webhooks.count() == 0
