import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import ChannelFilter
from apps.public_api import constants as public_api_constants

# https://api-docs.amixr.io/#get-route
demo_route_payload = {
    "id": public_api_constants.DEMO_ROUTE_ID_1,
    "escalation_chain_id": None,
    "integration_id": public_api_constants.DEMO_INTEGRATION_ID,
    "routing_regex": "us-(east|west)",
    "position": 0,
    "is_the_last_route": False,
    "slack": {"channel_id": public_api_constants.DEMO_SLACK_CHANNEL_FOR_ROUTE_ID},
}

# https://api-docs.amixr.io/#list-routes
demo_routes_payload = {
    "count": 2,
    "next": None,
    "previous": None,
    "results": [
        {
            "id": public_api_constants.DEMO_ROUTE_ID_1,
            "escalation_chain_id": None,
            "integration_id": public_api_constants.DEMO_INTEGRATION_ID,
            "routing_regex": "us-(east|west)",
            "position": 0,
            "is_the_last_route": False,
            "slack": {"channel_id": public_api_constants.DEMO_SLACK_CHANNEL_FOR_ROUTE_ID},
        },
        {
            "id": public_api_constants.DEMO_ROUTE_ID_2,
            "escalation_chain_id": None,
            "integration_id": public_api_constants.DEMO_INTEGRATION_ID,
            "routing_regex": ".*",
            "position": 1,
            "is_the_last_route": True,
            "slack": {"channel_id": public_api_constants.DEMO_SLACK_CHANNEL_FOR_ROUTE_ID},
        },
    ],
}


@pytest.mark.django_db
def test_get_route(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    channel_filter = ChannelFilter.objects.get(public_primary_key=public_api_constants.DEMO_ROUTE_ID_1)

    url = reverse("api-public:routes-detail", kwargs={"pk": channel_filter.public_primary_key})
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_route_payload


@pytest.mark.django_db
def test_get_routes_list(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:routes-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_routes_payload


@pytest.mark.django_db
def test_get_routes_filter_by_integration_id(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:routes-list")
    response = client.get(
        url + f"?integration_id={public_api_constants.DEMO_INTEGRATION_ID}", format="json", HTTP_AUTHORIZATION=token
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == demo_routes_payload


@pytest.mark.django_db
def test_create_route(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:routes-list")
    data_for_create = {
        "integration_id": public_api_constants.DEMO_INTEGRATION_ID,
        "routing_regex": "testreg",
    }
    response = client.post(url, format="json", HTTP_AUTHORIZATION=token, data=data_for_create)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == demo_route_payload


@pytest.mark.django_db
def test_invalid_route_data(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)

    url = reverse("api-public:routes-list")
    data_for_create = {
        "integration_id": public_api_constants.DEMO_INTEGRATION_ID,
        "routing_regex": None,  # routing_regex cannot be null for non-default filters
    }
    response = client.post(url, format="json", HTTP_AUTHORIZATION=token, data=data_for_create)

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == demo_route_payload


@pytest.mark.django_db
def test_update_route(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    channel_filter = ChannelFilter.objects.get(public_primary_key=public_api_constants.DEMO_ROUTE_ID_1)

    url = reverse("api-public:routes-detail", kwargs={"pk": channel_filter.public_primary_key})
    data_to_update = {
        "routing_regex": "testreg_updated",
    }

    assert channel_filter.filtering_term != data_to_update["routing_regex"]

    response = client.put(url, format="json", HTTP_AUTHORIZATION=token, data=data_to_update)

    assert response.status_code == status.HTTP_200_OK
    # check on nothing change
    channel_filter.refresh_from_db()
    assert response.json() == demo_route_payload
    assert channel_filter.filtering_term != data_to_update["routing_regex"]


@pytest.mark.django_db
def test_delete_route(
    make_organization_and_user_with_slack_identities_for_demo_token,
    make_data_for_demo_token,
):
    organization, user, token = make_organization_and_user_with_slack_identities_for_demo_token()
    client = APIClient()
    _ = make_data_for_demo_token(organization, user)
    channel_filter = ChannelFilter.objects.get(public_primary_key=public_api_constants.DEMO_ROUTE_ID_1)

    url = reverse("api-public:routes-detail", kwargs={"pk": channel_filter.public_primary_key})
    response = client.delete(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    # check on nothing change
    channel_filter.refresh_from_db()
    assert channel_filter is not None
