from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.constants import ActionSource
from apps.alerts.models import AlertGroup, AlertReceiveChannel
from apps.alerts.tasks import delete_alert_group, wipe


def construct_expected_response_from_alert_groups(alert_groups):
    results = []
    for alert_group in alert_groups:
        # convert datetimes to serializers.DateTimeField
        created_at = None
        if alert_group.started_at:
            created_at = alert_group.started_at.isoformat()
            created_at = created_at[:-6] + "Z"

        resolved_at = None
        if alert_group.resolved_at:
            resolved_at = alert_group.resolved_at.isoformat()
            resolved_at = resolved_at[:-6] + "Z"

        acknowledged_at = None
        if alert_group.acknowledged_at:
            acknowledged_at = alert_group.acknowledged_at.isoformat()
            acknowledged_at = acknowledged_at[:-6] + "Z"

        results.append(
            {
                "id": alert_group.public_primary_key,
                "integration_id": alert_group.channel.public_primary_key,
                "route_id": alert_group.channel_filter.public_primary_key,
                "alerts_count": alert_group.alerts.count(),
                "state": alert_group.state,
                "created_at": created_at,
                "resolved_at": resolved_at,
                "acknowledged_at": acknowledged_at,
                "title": None,
                "permalinks": {
                    "slack": None,
                    "telegram": None,
                    "web": alert_group.web_link,
                },
            }
        )
    return {
        "count": alert_groups.count(),
        "next": None,
        "previous": None,
        "results": results,
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }


@pytest.fixture()
def alert_group_public_api_setup(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_channel_filter,
    make_alert_group,
    make_alert,
):
    organization, user, token = make_organization_and_user_with_token()
    grafana = make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_GRAFANA)
    formatted_webhook = make_alert_receive_channel(
        organization, integration=AlertReceiveChannel.INTEGRATION_FORMATTED_WEBHOOK
    )

    grafana_default_route = make_channel_filter(grafana, is_default=True)
    grafana_non_default_route = make_channel_filter(grafana, filtering_term="us-east")
    formatted_webhook_default_route = make_channel_filter(formatted_webhook, is_default=True)

    grafana_alert_group_default_route = make_alert_group(grafana, channel_filter=grafana_default_route)
    grafana_alert_group_non_default_route = make_alert_group(grafana, channel_filter=grafana_non_default_route)
    formatted_webhook_alert_group = make_alert_group(formatted_webhook, channel_filter=formatted_webhook_default_route)

    make_alert(alert_group=grafana_alert_group_default_route, raw_request_data=grafana.config.example_payload)
    make_alert(alert_group=grafana_alert_group_non_default_route, raw_request_data=grafana.config.example_payload)
    make_alert(alert_group=formatted_webhook_alert_group, raw_request_data=grafana.config.example_payload)

    integrations = grafana, formatted_webhook
    alert_groups = (
        grafana_alert_group_default_route,
        grafana_alert_group_non_default_route,
        formatted_webhook_alert_group,
    )
    routes = grafana_default_route, grafana_non_default_route, formatted_webhook_default_route

    return token, alert_groups, integrations, routes


@pytest.mark.django_db
def test_get_alert_groups(alert_group_public_api_setup):
    token, _, _, _ = alert_group_public_api_setup
    alert_groups = AlertGroup.objects.all().order_by("-started_at")
    client = APIClient()
    expected_response = construct_expected_response_from_alert_groups(alert_groups)

    url = reverse("api-public:alert_groups-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_integration(
    alert_group_public_api_setup,
):
    token, alert_groups, integrations, _ = alert_group_public_api_setup
    formatted_webhook = integrations[1]
    alert_groups = AlertGroup.objects.filter(channel=formatted_webhook).order_by("-started_at")
    expected_response = construct_expected_response_from_alert_groups(alert_groups)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(
        url + f"?integration_id={formatted_webhook.public_primary_key}", format="json", HTTP_AUTHORIZATION=token
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_state_new(
    alert_group_public_api_setup,
):
    token, _, _, _ = alert_group_public_api_setup
    alert_groups = AlertGroup.objects.filter(AlertGroup.get_new_state_filter()).order_by("-started_at")
    expected_response = construct_expected_response_from_alert_groups(alert_groups)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=new", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_state_acknowledged(
    alert_group_public_api_setup,
):
    token, _, _, _ = alert_group_public_api_setup
    alert_groups = AlertGroup.objects.filter(AlertGroup.get_acknowledged_state_filter()).order_by("-started_at")
    expected_response = construct_expected_response_from_alert_groups(alert_groups)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=acknowledged", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_state_silenced(
    alert_group_public_api_setup,
):
    token, _, _, _ = alert_group_public_api_setup
    alert_groups = AlertGroup.objects.filter(AlertGroup.get_silenced_state_filter()).order_by("-started_at")
    expected_response = construct_expected_response_from_alert_groups(alert_groups)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=silenced", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_state_resolved(
    alert_group_public_api_setup,
):
    token, _, _, _ = alert_group_public_api_setup
    alert_groups = AlertGroup.objects.filter(AlertGroup.get_resolved_state_filter()).order_by("-started_at")
    expected_response = construct_expected_response_from_alert_groups(alert_groups)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=resolved", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_state_unknown(
    alert_group_public_api_setup,
):
    token, _, _, _ = alert_group_public_api_setup
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=unknown", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_get_alert_groups_filter_by_integration_no_result(
    alert_group_public_api_setup,
):
    token, _, _, _ = alert_group_public_api_setup
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?integration_id=impossible_integration", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"] == []


@pytest.mark.django_db
def test_get_alert_groups_filter_by_route(
    alert_group_public_api_setup,
):
    token, alert_groups, integrations, routes = alert_group_public_api_setup
    grafana_non_default_route = routes[1]
    alert_groups = AlertGroup.objects.filter(channel_filter=grafana_non_default_route).order_by("-started_at")
    expected_response = construct_expected_response_from_alert_groups(alert_groups)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(
        url + f"?route_id={grafana_non_default_route.public_primary_key}", format="json", HTTP_AUTHORIZATION=token
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_alert_groups_filter_by_route_no_result(
    alert_group_public_api_setup,
):
    token, _, _, _ = alert_group_public_api_setup
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?route_id=impossible_route_ir", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"] == []


@pytest.mark.parametrize(
    "data,task,status_code",
    [
        (None, wipe, status.HTTP_204_NO_CONTENT),
        ({"mode": "wipe"}, wipe, status.HTTP_204_NO_CONTENT),
        ({"mode": "delete"}, delete_alert_group, status.HTTP_204_NO_CONTENT),
        ({"mode": "random"}, None, status.HTTP_400_BAD_REQUEST),
        ("delete", None, status.HTTP_400_BAD_REQUEST),
    ],
)
@pytest.mark.django_db
def test_delete_alert_group(alert_group_public_api_setup, data, task, status_code):
    token, alert_groups, _, _ = alert_group_public_api_setup
    alert_group = alert_groups[0]

    client = APIClient()
    url = reverse("api-public:alert_groups-detail", kwargs={"pk": alert_group.public_primary_key})

    if task:
        with patch.object(task, "apply_async") as mock_task:
            response = client.delete(url, data=data, format="json", HTTP_AUTHORIZATION=token)
            mock_task.assert_called_once()
    else:
        response = client.delete(url, data=data, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status_code


@pytest.mark.django_db
def test_pagination(settings, alert_group_public_api_setup):
    settings.BASE_URL = "https://test.com/test/prefixed/urls"

    token, alert_groups, _, _ = alert_group_public_api_setup
    client = APIClient()

    url = reverse("api-public:alert_groups-list")

    with patch("common.api_helpers.paginators.PathPrefixedPagePagination.get_page_size", return_value=1):
        response = client.get(url, HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    assert result["next"].startswith("https://test.com/test/prefixed/urls")


@pytest.mark.parametrize(
    "acknowledged,resolved,attached,maintenance,status_code",
    [
        (False, False, False, False, status.HTTP_200_OK),
        (True, False, False, False, status.HTTP_400_BAD_REQUEST),
        (False, True, False, False, status.HTTP_400_BAD_REQUEST),
        (False, False, True, False, status.HTTP_400_BAD_REQUEST),
        (False, False, False, True, status.HTTP_400_BAD_REQUEST),
    ],
)
@pytest.mark.django_db
def test_alert_group_acknowledge(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    acknowledged,
    resolved,
    attached,
    maintenance,
    status_code,
):
    organization, _, token = make_organization_and_user_with_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    root_alert_group = make_alert_group(alert_receive_channel)
    alert_group = make_alert_group(
        alert_receive_channel,
        acknowledged=acknowledged,
        resolved=resolved,
        root_alert_group=root_alert_group if attached else None,
        maintenance_uuid="test_maintenance_uuid" if maintenance else None,
    )

    client = APIClient()
    url = reverse("api-public:alert_groups-acknowledge", kwargs={"pk": alert_group.public_primary_key})
    response = client.post(url, HTTP_AUTHORIZATION=token)
    assert response.status_code == status_code

    if status_code == status.HTTP_200_OK:
        alert_group.refresh_from_db()
        assert alert_group.acknowledged is True
        assert alert_group.log_records.last().action_source == ActionSource.API


@pytest.mark.parametrize(
    "acknowledged,resolved,attached,maintenance,status_code",
    [
        (True, False, False, False, status.HTTP_200_OK),
        (True, True, False, False, status.HTTP_400_BAD_REQUEST),
        (True, False, True, False, status.HTTP_400_BAD_REQUEST),
        (True, False, False, True, status.HTTP_400_BAD_REQUEST),
        (False, False, False, False, status.HTTP_400_BAD_REQUEST),
    ],
)
@pytest.mark.django_db
def test_alert_group_unacknowledge(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    acknowledged,
    resolved,
    attached,
    maintenance,
    status_code,
):
    organization, _, token = make_organization_and_user_with_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    root_alert_group = make_alert_group(alert_receive_channel)
    alert_group = make_alert_group(
        alert_receive_channel,
        acknowledged=acknowledged,
        resolved=resolved,
        root_alert_group=root_alert_group if attached else None,
        maintenance_uuid="test_maintenance_uuid" if maintenance else None,
    )

    client = APIClient()
    url = reverse("api-public:alert_groups-unacknowledge", kwargs={"pk": alert_group.public_primary_key})
    response = client.post(url, HTTP_AUTHORIZATION=token)
    assert response.status_code == status_code

    if status_code == status.HTTP_200_OK:
        alert_group.refresh_from_db()
        assert alert_group.acknowledged is False
        assert alert_group.log_records.last().action_source == ActionSource.API


@pytest.mark.parametrize(
    "resolved,attached,maintenance,status_code",
    [
        (False, False, False, status.HTTP_200_OK),
        (False, False, True, status.HTTP_200_OK),
        (True, False, False, status.HTTP_400_BAD_REQUEST),
        (False, True, False, status.HTTP_400_BAD_REQUEST),
    ],
)
@pytest.mark.django_db
def test_alert_group_resolve(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    resolved,
    attached,
    maintenance,
    status_code,
):
    organization, _, token = make_organization_and_user_with_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    root_alert_group = make_alert_group(alert_receive_channel)
    alert_group = make_alert_group(
        alert_receive_channel,
        resolved=resolved,
        root_alert_group=root_alert_group if attached else None,
        maintenance_uuid="test_maintenance_uuid" if maintenance else None,
    )

    client = APIClient()
    url = reverse("api-public:alert_groups-resolve", kwargs={"pk": alert_group.public_primary_key})
    response = client.post(url, HTTP_AUTHORIZATION=token)
    assert response.status_code == status_code

    if status_code == status.HTTP_200_OK and not maintenance:
        alert_group.refresh_from_db()
        assert alert_group.resolved is True
        assert alert_group.log_records.last().action_source == ActionSource.API


@pytest.mark.parametrize(
    "resolved,attached,maintenance,status_code",
    [
        (True, False, False, status.HTTP_200_OK),
        (True, True, False, status.HTTP_400_BAD_REQUEST),
        (True, False, True, status.HTTP_400_BAD_REQUEST),
        (False, False, False, status.HTTP_400_BAD_REQUEST),
    ],
)
@pytest.mark.django_db
def test_alert_group_unresolve(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_alert_group,
    resolved,
    attached,
    maintenance,
    status_code,
):
    organization, _, token = make_organization_and_user_with_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    root_alert_group = make_alert_group(alert_receive_channel)
    alert_group = make_alert_group(
        alert_receive_channel,
        resolved=resolved,
        root_alert_group=root_alert_group if attached else None,
        maintenance_uuid="test_maintenance_uuid" if maintenance else None,
    )

    client = APIClient()
    url = reverse("api-public:alert_groups-unresolve", kwargs={"pk": alert_group.public_primary_key})
    response = client.post(url, HTTP_AUTHORIZATION=token)
    assert response.status_code == status_code

    if status_code == status.HTTP_200_OK:
        alert_group.refresh_from_db()
        assert alert_group.resolved is False
        assert alert_group.log_records.last().action_source == ActionSource.API
