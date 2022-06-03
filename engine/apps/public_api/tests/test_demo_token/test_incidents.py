import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertGroup
from apps.public_api import constants as public_api_constants

demo_incidents_payload = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [
        {
            "id": public_api_constants.DEMO_INCIDENT_ID,
            "integration_id": public_api_constants.DEMO_INTEGRATION_ID,
            "route_id": public_api_constants.DEMO_ROUTE_ID_1,
            "alerts_count": 3,
            "state": "resolved",
            "created_at": public_api_constants.DEMO_INCIDENT_CREATED_AT,
            "resolved_at": public_api_constants.DEMO_INCIDENT_RESOLVED_AT,
            "acknowledged_at": None,
            "title": None,
        }
    ],
}


@pytest.mark.django_db
def test_create_incidents(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    url = reverse("api-public:alert_groups-list")
    response = client.post(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.django_db
def test_get_incidents(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    url = reverse("api-public:alert_groups-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_incidents_payload


@pytest.mark.django_db
def test_delete_incidents(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    url = reverse("api-public:alert_groups-list")
    incidents = AlertGroup.unarchived_objects.filter(public_primary_key=public_api_constants.DEMO_INCIDENT_ID)
    total_count = incidents.count()
    incident = incidents[0]
    data = {
        "mode": "delete",
    }
    response = client.delete(url + f"/{incident.public_primary_key}/", data, format="json", HTTP_AUTHORIZATION=token)
    new_count = AlertGroup.unarchived_objects.filter(public_primary_key=public_api_constants.DEMO_INCIDENT_ID).count()

    assert response.status_code == status.HTTP_204_NO_CONTENT
    incident.refresh_from_db()
    assert total_count == new_count
    assert incident is not None
