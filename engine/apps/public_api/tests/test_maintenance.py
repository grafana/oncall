import dateutil.parser
import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_start_and_stop_maintenance_for_integration(
    make_organization_and_user_with_token, make_alert_receive_channel, make_escalation_chain
):
    organization, user, token = make_organization_and_user_with_token()
    integration = make_alert_receive_channel(organization)
    make_escalation_chain(organization)

    client = APIClient()
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    # Make sure there is no Maintenance
    assert response.json()["maintenance_mode"] is None
    assert response.json()["maintenance_started_at"] is None
    assert response.json()["maintenance_end_at"] is None

    # Starting maintenance
    client.post(
        url + "/maintenance_start/",
        data={
            "mode": "Maintenance",
            "duration": 100,
        },
        format="json",
        HTTP_AUTHORIZATION=f"{token}",
    )

    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")
    assert response.json()["maintenance_mode"] == "maintenance"
    assert dateutil.parser.parse(response.json()["maintenance_end_at"]) - dateutil.parser.parse(
        response.json()["maintenance_started_at"]
    ) == timezone.timedelta(seconds=100)

    # Ending maintenance
    client.post(url + "/maintenance_stop/", format="json", HTTP_AUTHORIZATION=f"{token}")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.json()["maintenance_mode"] is None
    assert response.json()["maintenance_started_at"] is None
    assert response.json()["maintenance_end_at"] is None
