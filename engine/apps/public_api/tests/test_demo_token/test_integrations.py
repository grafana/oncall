from urllib.parse import urljoin

import pytest
from django.conf import settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertReceiveChannel
from apps.public_api import constants as public_api_constants

# https://api-docs.amixr.io/#post-integration
demo_integration_post_payload = {
    "id": public_api_constants.DEMO_INTEGRATION_ID,
    "team_id": None,
    "name": "Grafana :blush:",
    "link": urljoin(settings.BASE_URL, f"/integrations/v1/grafana/{public_api_constants.DEMO_INTEGRATION_LINK_TOKEN}/"),
    "heartbeat": None,
    "default_route": {
        "escalation_chain_id": None,
        "id": public_api_constants.DEMO_ROUTE_ID_2,
        "slack": {"channel_id": public_api_constants.DEMO_SLACK_CHANNEL_FOR_ROUTE_ID},
    },
    "type": "grafana",
    "templates": {
        "grouping_key": None,
        "resolve_signal": None,
        "acknowledge_signal": None,
        "slack": {"title": None, "message": None, "image_url": None},
        "web": {"title": None, "message": None, "image_url": None},
        "sms": {
            "title": None,
        },
        "phone_call": {
            "title": None,
        },
        "email": {
            "title": None,
            "message": None,
        },
        "telegram": {
            "title": None,
            "message": None,
            "image_url": None,
        },
    },
    "maintenance_mode": None,
    "maintenance_started_at": None,
    "maintenance_end_at": None,
}

# https://api-docs.amixr.io/#get-integration
demo_integration_payload = {
    "id": public_api_constants.DEMO_INTEGRATION_ID,
    "team_id": None,
    "name": "Grafana :blush:",
    "link": urljoin(settings.BASE_URL, f"/integrations/v1/grafana/{public_api_constants.DEMO_INTEGRATION_LINK_TOKEN}/"),
    "default_route": {
        "escalation_chain_id": None,
        "id": public_api_constants.DEMO_ROUTE_ID_2,
        "slack": {"channel_id": public_api_constants.DEMO_SLACK_CHANNEL_FOR_ROUTE_ID},
    },
    "type": "grafana",
    "heartbeat": None,
    "templates": {
        "grouping_key": None,
        "resolve_signal": None,
        "acknowledge_signal": None,
        "slack": {"title": None, "message": None, "image_url": None},
        "web": {"title": None, "message": None, "image_url": None},
        "sms": {
            "title": None,
        },
        "phone_call": {
            "title": None,
        },
        "email": {
            "title": None,
            "message": None,
        },
        "telegram": {
            "title": None,
            "message": None,
            "image_url": None,
        },
    },
    "maintenance_mode": None,
    "maintenance_started_at": None,
    "maintenance_end_at": None,
}

# https://api-docs.amixr.io/#list-integrations
demo_integrations_payload = {
    "count": 1,
    "next": None,
    "previous": None,
    "results": [
        {
            "id": public_api_constants.DEMO_INTEGRATION_ID,
            "team_id": None,
            "name": "Grafana :blush:",
            "link": urljoin(
                settings.BASE_URL, f"/integrations/v1/grafana/{public_api_constants.DEMO_INTEGRATION_LINK_TOKEN}/"
            ),
            "default_route": {
                "escalation_chain_id": None,
                "id": public_api_constants.DEMO_ROUTE_ID_2,
                "slack": {"channel_id": public_api_constants.DEMO_SLACK_CHANNEL_FOR_ROUTE_ID},
            },
            "type": "grafana",
            "heartbeat": None,
            "templates": {
                "grouping_key": None,
                "resolve_signal": None,
                "acknowledge_signal": None,
                "slack": {
                    "title": None,
                    "message": None,
                    "image_url": None,
                },
                "web": {"title": None, "message": None, "image_url": None},
                "sms": {
                    "title": None,
                },
                "phone_call": {
                    "title": None,
                },
                "email": {
                    "title": None,
                    "message": None,
                },
                "telegram": {
                    "title": None,
                    "message": None,
                    "image_url": None,
                },
            },
            "maintenance_mode": None,
            "maintenance_started_at": None,
            "maintenance_end_at": None,
        },
    ],
}


@pytest.mark.django_db
def test_get_integrations(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    url = reverse("api-public:integrations-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_integrations_payload


@pytest.mark.django_db
def test_create_integration(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    data_for_create = {"type": "grafana"}
    url = reverse("api-public:integrations-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_201_CREATED
    # check on nothing change
    assert response.json() == demo_integration_post_payload


@pytest.mark.django_db
def test_update_integration(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    integration = AlertReceiveChannel.objects.get(public_primary_key=public_api_constants.DEMO_INTEGRATION_ID)
    data_for_update = {"name": "new_name"}
    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.put(url, data=data_for_update, format="json", HTTP_AUTHORIZATION=token)

    integration.refresh_from_db()

    assert response.status_code == status.HTTP_200_OK
    # check on nothing change
    assert response.json() == demo_integration_payload


@pytest.mark.django_db
def test_invalid_integration_type(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    data_for_create = {"type": "this_is_invalid_integration_type"}
    url = reverse("api-public:integrations-list")
    response = client.post(url, data=data_for_create, format="json", HTTP_AUTHORIZATION=token)
    assert response.status_code == status.HTTP_201_CREATED
    # check on nothing change
    assert response.json() == demo_integration_post_payload


@pytest.mark.django_db
def test_delete_integration(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):

    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()

    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    integration = AlertReceiveChannel.objects.get(public_primary_key=public_api_constants.DEMO_INTEGRATION_ID)

    url = reverse("api-public:integrations-detail", args=[integration.public_primary_key])
    response = client.delete(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    # check on nothing change
    integration.refresh_from_db()
    assert integration is not None
