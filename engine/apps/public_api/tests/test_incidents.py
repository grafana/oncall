from unittest import mock
from unittest.mock import patch

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertGroup, AlertReceiveChannel


def construct_expected_response_from_incidents(incidents):
    results = []
    for incident in incidents:
        # convert datetimes to serializers.DateTimeField
        created_at = None
        if incident.started_at:
            created_at = incident.started_at.isoformat()
            created_at = created_at[:-6] + "Z"

        resolved_at = None
        if incident.resolved_at:
            resolved_at = incident.resolved_at.isoformat()
            resolved_at = resolved_at[:-6] + "Z"

        acknowledged_at = None
        if incident.acknowledged_at:
            acknowledged_at = incident.acknowledged_at.isoformat()
            acknowledged_at = acknowledged_at[:-6] + "Z"

        results.append(
            {
                "id": incident.public_primary_key,
                "integration_id": incident.channel.public_primary_key,
                "route_id": incident.channel_filter.public_primary_key,
                "alerts_count": incident.alerts.count(),
                "state": incident.state,
                "created_at": created_at,
                "resolved_at": resolved_at,
                "acknowledged_at": acknowledged_at,
                "title": None,
                "permalinks": {
                    "slack": None,
                    "telegram": None,
                    "web": incident.web_link,
                },
            }
        )
    return {
        "count": incidents.count(),
        "next": None,
        "previous": None,
        "results": results,
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }


@pytest.fixture()
def incident_public_api_setup(
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

    grafana_incident_default_route = make_alert_group(grafana, channel_filter=grafana_default_route)
    grafana_incident_non_default_route = make_alert_group(grafana, channel_filter=grafana_non_default_route)
    formatted_webhook_incident = make_alert_group(formatted_webhook, channel_filter=formatted_webhook_default_route)

    make_alert(alert_group=grafana_incident_default_route, raw_request_data=grafana.config.example_payload)
    make_alert(alert_group=grafana_incident_non_default_route, raw_request_data=grafana.config.example_payload)
    make_alert(alert_group=formatted_webhook_incident, raw_request_data=grafana.config.example_payload)

    integrations = grafana, formatted_webhook
    incidents = grafana_incident_default_route, grafana_incident_non_default_route, formatted_webhook_incident
    routes = grafana_default_route, grafana_non_default_route, formatted_webhook_default_route

    return token, incidents, integrations, routes


@pytest.mark.django_db
def test_get_incidents(incident_public_api_setup):
    token, _, _, _ = incident_public_api_setup
    incidents = AlertGroup.objects.all().order_by("-started_at")
    client = APIClient()
    expected_response = construct_expected_response_from_incidents(incidents)

    url = reverse("api-public:alert_groups-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_incidents_filter_by_integration(
    incident_public_api_setup,
):
    token, incidents, integrations, _ = incident_public_api_setup
    formatted_webhook = integrations[1]
    incidents = AlertGroup.objects.filter(channel=formatted_webhook).order_by("-started_at")
    expected_response = construct_expected_response_from_incidents(incidents)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(
        url + f"?integration_id={formatted_webhook.public_primary_key}", format="json", HTTP_AUTHORIZATION=f"{token}"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_incidents_filter_by_state_new(
    incident_public_api_setup,
):
    token, _, _, _ = incident_public_api_setup
    incidents = AlertGroup.objects.filter(AlertGroup.get_new_state_filter()).order_by("-started_at")
    expected_response = construct_expected_response_from_incidents(incidents)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=new", format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_incidents_filter_by_state_acknowledged(
    incident_public_api_setup,
):
    token, _, _, _ = incident_public_api_setup
    incidents = AlertGroup.objects.filter(AlertGroup.get_acknowledged_state_filter()).order_by("-started_at")
    expected_response = construct_expected_response_from_incidents(incidents)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=acknowledged", format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_incidents_filter_by_state_silenced(
    incident_public_api_setup,
):
    token, _, _, _ = incident_public_api_setup
    incidents = AlertGroup.objects.filter(AlertGroup.get_silenced_state_filter()).order_by("-started_at")
    expected_response = construct_expected_response_from_incidents(incidents)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=silenced", format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_incidents_filter_by_state_resolved(
    incident_public_api_setup,
):
    token, _, _, _ = incident_public_api_setup
    incidents = AlertGroup.objects.filter(AlertGroup.get_resolved_state_filter()).order_by("-started_at")
    expected_response = construct_expected_response_from_incidents(incidents)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=resolved", format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_incidents_filter_by_state_unknown(
    incident_public_api_setup,
):
    token, _, _, _ = incident_public_api_setup
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?state=unknown", format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_get_incidents_filter_by_integration_no_result(
    incident_public_api_setup,
):
    token, _, _, _ = incident_public_api_setup
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?integration_id=impossible_integration", format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"] == []


@pytest.mark.django_db
def test_get_incidents_filter_by_route(
    incident_public_api_setup,
):
    token, incidents, integrations, routes = incident_public_api_setup
    grafana_non_default_route = routes[1]
    incidents = AlertGroup.objects.filter(channel_filter=grafana_non_default_route).order_by("-started_at")
    expected_response = construct_expected_response_from_incidents(incidents)
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(
        url + f"?route_id={grafana_non_default_route.public_primary_key}", format="json", HTTP_AUTHORIZATION=f"{token}"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_incidents_filter_by_route_no_result(
    incident_public_api_setup,
):
    token, _, _, _ = incident_public_api_setup
    client = APIClient()

    url = reverse("api-public:alert_groups-list")
    response = client.get(url + "?route_id=impossible_route_ir", format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["results"] == []


@mock.patch("apps.public_api.views.incidents.delete_alert_group", return_value=None)
@pytest.mark.django_db
def test_delete_incident_success_response(mocked_task, incident_public_api_setup):
    token, incidents, _, _ = incident_public_api_setup
    grafana_first_incident = incidents[0]
    client = APIClient()

    url = reverse("api-public:alert_groups-detail", kwargs={"pk": grafana_first_incident.public_primary_key})
    data = {"mode": "delete"}
    response = client.delete(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert mocked_task.apply_async.call_count == 1


@pytest.mark.django_db
def test_delete_incident_invalid_request(incident_public_api_setup):
    token, incidents, _, _ = incident_public_api_setup
    grafana_first_incident = incidents[0]
    client = APIClient()

    url = reverse("api-public:alert_groups-detail", kwargs={"pk": grafana_first_incident.public_primary_key})
    data = "delete"
    response = client.delete(url, data=data, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_pagination(settings, incident_public_api_setup):
    settings.BASE_URL = "https://test.com/test/prefixed/urls"

    token, incidents, _, _ = incident_public_api_setup
    client = APIClient()

    url = reverse("api-public:alert_groups-list")

    with patch("common.api_helpers.paginators.PathPrefixedPagePagination.get_page_size", return_value=1):
        response = client.get(url, HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    assert result["next"].startswith("https://test.com/test/prefixed/urls")


# This is test from old django-based tests
# TODO: uncomment with date checking in delete mode
# def test_delete_incident_invalid_date(self):
#     not_valid_creation_date = VALID_DATE_FOR_DELETE_INCIDENT - timezone.timedelta(days=1)
#     self.grafana_second_alert_group.started_at = not_valid_creation_date
#     self.grafana_second_alert_group.save()
#
#     url = reverse("api-public:alert_groups-detail", kwargs={'pk': self.grafana_second_alert_group.public_primary_key})
#     data = {"mode": "delete"}
#     response = self.client.delete(url, data=data, format="json", HTTP_AUTHORIZATION=f"{self.token}")
#     self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
