import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.public_api import constants as public_api_constants

demo_alerts_results = []
for alert_id, created_at in public_api_constants.DEMO_ALERT_IDS:
    demo_alerts_results.append(
        {
            "id": alert_id,
            "alert_group_id": public_api_constants.DEMO_INCIDENT_ID,
            "created_at": created_at,
            "payload": {
                "state": "alerting",
                "title": "[Alerting] Test notification",
                "ruleId": 0,
                "message": "Someone is testing the alert notification within grafana.",
                "ruleUrl": "https://amixr.io/",
                "ruleName": "Test notification",
                "evalMatches": [
                    {"tags": None, "value": 100, "metric": "High value"},
                    {"tags": None, "value": 200, "metric": "Higher Value"},
                ],
            },
        }
    )

# https://api-docs.amixr.io/#list-alerts
demo_alerts_payload = {"count": 3, "next": None, "previous": None, "results": demo_alerts_results}


@pytest.mark.django_db
def test_get_alerts(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    url = reverse("api-public:alerts-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_alerts_payload


@pytest.mark.django_db
def test_get_alerts_filter_by_incident(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    url = reverse("api-public:alerts-list")
    response = client.get(
        url + f"?alert_group_id={public_api_constants.DEMO_INCIDENT_ID}", format="json", HTTP_AUTHORIZATION=token
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_alerts_payload


@pytest.mark.django_db
def test_get_alerts_filter_by_incident_no_results(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    url = reverse("api-public:alerts-list")
    response = client.get(url + "?alert_group_id=impossible_alert_group_id", format="json", HTTP_AUTHORIZATION=token)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"] == []


@pytest.mark.django_db
def test_get_alerts_search(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    url = reverse("api-public:alerts-list")
    response = client.get(url + "?search=evalMatches", format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_alerts_payload


@pytest.mark.django_db
def test_get_alerts_search_no_results(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    url = reverse("api-public:alerts-list")
    response = client.get(url + "?search=impossible_payload", format="json", HTTP_AUTHORIZATION=token)
    assert response.status_code == status.HTTP_200_OK
    assert response.data["results"] == []
