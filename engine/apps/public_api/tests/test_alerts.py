import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

alert_raw_request_data = {
    "evalMatches": [
        {"value": 100, "metric": "High value", "tags": None},
        {"value": 200, "metric": "Higher Value", "tags": None},
    ],
    "message": "Someone is testing the alert notification within grafana.",
    "ruleId": 0,
    "ruleName": "Test notification",
    "ruleUrl": "http://localhost:3000/",
    "state": "alerting",
    "title": "[Alerting] Test notification",
}


@pytest.fixture()
def alert_public_api_setup(
    make_organization,
    make_alert_receive_channel,
    make_channel_filter,
):
    organization = make_organization()
    alert_receive_channel = make_alert_receive_channel(organization)
    default_channel_filter = make_channel_filter(alert_receive_channel, is_default=True)
    return organization, alert_receive_channel, default_channel_filter


@pytest.mark.django_db
def test_get_list_alerts(
    alert_public_api_setup,
    make_user_for_organization,
    make_public_api_token,
    make_alert_group,
    make_alert,
):
    # https://api-docs.amixr.io/#list-alerts
    organization, alert_receive_channel, default_channel_filter = alert_public_api_setup
    alert_group = make_alert_group(alert_receive_channel)
    alert_1 = make_alert(alert_group, alert_raw_request_data)
    alert_2 = make_alert(alert_group, alert_raw_request_data)
    admin = make_user_for_organization(organization)
    _, token = make_public_api_token(admin, organization)

    client = APIClient()

    url = reverse("api-public:alerts-list")
    response = client.get(url, HTTP_AUTHORIZATION=f"{token}")

    expected_response = {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": alert_2.public_primary_key,
                "alert_group_id": alert_group.public_primary_key,
                "created_at": alert_2.created_at.isoformat().replace("+00:00", "Z"),
                "payload": {
                    "state": "alerting",
                    "title": "[Alerting] Test notification",
                    "ruleId": 0,
                    "message": "Someone is testing the alert notification within grafana.",
                    "ruleUrl": "http://localhost:3000/",
                    "ruleName": "Test notification",
                    "evalMatches": [
                        {"tags": None, "value": 100, "metric": "High value"},
                        {"tags": None, "value": 200, "metric": "Higher Value"},
                    ],
                },
            },
            {
                "id": alert_1.public_primary_key,
                "alert_group_id": alert_group.public_primary_key,
                "created_at": alert_1.created_at.isoformat().replace("+00:00", "Z"),
                "payload": {
                    "state": "alerting",
                    "title": "[Alerting] Test notification",
                    "ruleId": 0,
                    "message": "Someone is testing the alert notification within grafana.",
                    "ruleUrl": "http://localhost:3000/",
                    "ruleName": "Test notification",
                    "evalMatches": [
                        {"tags": None, "value": 100, "metric": "High value"},
                        {"tags": None, "value": 200, "metric": "Higher Value"},
                    ],
                },
            },
        ],
        "current_page_number": 1,
        "page_size": 50,
        "total_pages": 1,
    }
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_list_alerts_filter_by_incident(
    alert_public_api_setup,
    make_user_for_organization,
    make_public_api_token,
    make_alert_group,
    make_alert,
):
    # https://api-docs.amixr.io/#list-alerts
    organization, alert_receive_channel, default_channel_filter = alert_public_api_setup
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, alert_raw_request_data)
    admin = make_user_for_organization(organization)
    _, token = make_public_api_token(admin, organization)

    client = APIClient()

    url = reverse("api-public:alerts-list")
    response = client.get(
        url + f"?alert_group_id={alert_group.public_primary_key}", format="json", HTTP_AUTHORIZATION=f"{token}"
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1


@pytest.mark.django_db
def test_get_list_alerts_filter_by_non_existing_incident(
    alert_public_api_setup,
    make_user_for_organization,
    make_public_api_token,
    make_alert_group,
    make_alert,
):
    organization, alert_receive_channel, default_channel_filter = alert_public_api_setup
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, alert_raw_request_data)
    admin = make_user_for_organization(organization)
    _, token = make_public_api_token(admin, organization)

    client = APIClient()

    url = reverse("api-public:alerts-list")
    response = client.get(url + "?alert_group_id=invalid_alert_group_id", format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 0


@pytest.mark.django_db
def test_alerts_search(
    alert_public_api_setup,
    make_user_for_organization,
    make_public_api_token,
    make_alert_group,
    make_alert,
):
    organization, alert_receive_channel, default_channel_filter = alert_public_api_setup
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, alert_raw_request_data)
    admin = make_user_for_organization(organization)
    _, token = make_public_api_token(admin, organization)

    client = APIClient()

    url = reverse("api-public:alerts-list")
    response = client.get(url + "?search=evalMatches", format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 1


@pytest.mark.django_db
def test_alerts_search_with_no_results(
    alert_public_api_setup,
    make_user_for_organization,
    make_public_api_token,
    make_alert_group,
    make_alert,
):
    organization, alert_receive_channel, default_channel_filter = alert_public_api_setup
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, alert_raw_request_data)
    admin = make_user_for_organization(organization)
    _, token = make_public_api_token(admin, organization)

    client = APIClient()

    url = reverse("api-public:alerts-list")
    response = client.get(url + "?search=impossible payload", format="json", HTTP_AUTHORIZATION=f"{token}")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["count"] == 0
