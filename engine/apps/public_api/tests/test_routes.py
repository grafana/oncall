import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import ChannelFilter
from apps.base.tests.messaging_backend import TestOnlyBackend

TEST_MESSAGING_BACKEND_FIELD = TestOnlyBackend.backend_id.lower()
TEST_MESSAGING_BACKEND_ID = "TESTBACKENDID"


@pytest.fixture()
def route_public_api_setup(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_escalation_chain,
    make_channel_filter,
):
    organization, user, token = make_organization_and_user_with_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    escalation_chain = make_escalation_chain(organization)
    channel_filter = make_channel_filter(
        alert_receive_channel,
        is_default=True,
        slack_channel_id="TEST_SLACK_ID",
        escalation_chain=escalation_chain,
    )
    return organization, user, token, alert_receive_channel, escalation_chain, channel_filter


@pytest.mark.django_db
def test_get_route(
    route_public_api_setup,
):
    _, _, token, alert_receive_channel, escalation_chain, channel_filter = route_public_api_setup

    client = APIClient()

    url = reverse("api-public:routes-detail", kwargs={"pk": channel_filter.public_primary_key})
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    expected_response = {
        "id": channel_filter.public_primary_key,
        "integration_id": alert_receive_channel.public_primary_key,
        "escalation_chain_id": escalation_chain.public_primary_key,
        "routing_type": "regex",
        "routing_regex": channel_filter.filtering_term,
        "position": channel_filter.order,
        "is_the_last_route": channel_filter.is_default,
        "slack": {"channel_id": channel_filter.slack_channel_id, "enabled": True},
        "telegram": {"id": None, "enabled": False},
        TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_routes_list(
    route_public_api_setup,
):
    _, _, token, alert_receive_channel, escalation_chain, channel_filter = route_public_api_setup

    client = APIClient()

    url = reverse("api-public:routes-list")
    response = client.get(url, format="json", HTTP_AUTHORIZATION=token)

    expected_response = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": channel_filter.public_primary_key,
                "integration_id": alert_receive_channel.public_primary_key,
                "escalation_chain_id": escalation_chain.public_primary_key,
                "routing_type": "regex",
                "routing_regex": channel_filter.filtering_term,
                "position": channel_filter.order,
                "is_the_last_route": channel_filter.is_default,
                "slack": {"channel_id": channel_filter.slack_channel_id, "enabled": True},
                "telegram": {"id": None, "enabled": False},
                TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
            }
        ],
        "current_page_number": 1,
        "page_size": 25,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_get_routes_filter_by_integration_id(
    route_public_api_setup,
):
    _, _, token, alert_receive_channel, escalation_chain, channel_filter = route_public_api_setup

    client = APIClient()

    url = reverse("api-public:routes-list")
    response = client.get(
        url + f"?integration_id={alert_receive_channel.public_primary_key}", format="json", HTTP_AUTHORIZATION=token
    )

    expected_response = {
        "count": 1,
        "next": None,
        "previous": None,
        "results": [
            {
                "id": channel_filter.public_primary_key,
                "integration_id": alert_receive_channel.public_primary_key,
                "escalation_chain_id": escalation_chain.public_primary_key,
                "routing_type": "regex",
                "routing_regex": channel_filter.filtering_term,
                "position": channel_filter.order,
                "is_the_last_route": channel_filter.is_default,
                "slack": {"channel_id": channel_filter.slack_channel_id, "enabled": True},
                "telegram": {"id": None, "enabled": False},
                TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
            }
        ],
        "current_page_number": 1,
        "page_size": 25,
        "total_pages": 1,
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_create_route(
    route_public_api_setup,
):
    _, _, token, alert_receive_channel, escalation_chain, _ = route_public_api_setup

    client = APIClient()

    url = reverse("api-public:routes-list")
    data_for_create = {
        "integration_id": alert_receive_channel.public_primary_key,
        "routing_regex": "testreg",
        "escalation_chain_id": escalation_chain.public_primary_key,
    }
    response = client.post(url, format="json", HTTP_AUTHORIZATION=token, data=data_for_create)

    expected_response = {
        "id": response.data["id"],
        "integration_id": alert_receive_channel.public_primary_key,
        "escalation_chain_id": escalation_chain.public_primary_key,
        "routing_type": "regex",
        "routing_regex": data_for_create["routing_regex"],
        "position": 0,
        "is_the_last_route": False,
        "slack": {"channel_id": None, "enabled": True},
        "telegram": {"id": None, "enabled": False},
        TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response


@pytest.mark.django_db
def test_create_route_without_escalation_chain(route_public_api_setup):
    _, _, token, alert_receive_channel, escalation_chain, _ = route_public_api_setup

    client = APIClient()
    url = reverse("api-public:routes-list")

    data = {
        "integration_id": alert_receive_channel.public_primary_key,
        "routing_regex": "testreg",
        "escalation_chain_id": None,
    }
    response = client.post(url, format="json", HTTP_AUTHORIZATION=token, data=data)

    expected_response = {
        "id": response.data["id"],
        "integration_id": alert_receive_channel.public_primary_key,
        "escalation_chain_id": None,
        "routing_type": "regex",
        "routing_regex": data["routing_regex"],
        "position": 0,
        "is_the_last_route": False,
        "slack": {"channel_id": None, "enabled": True},
        "telegram": {"id": None, "enabled": False},
        TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response


@pytest.mark.django_db
def test_invalid_route_data(
    route_public_api_setup,
):
    _, _, token, alert_receive_channel, escalation_chain, _ = route_public_api_setup

    client = APIClient()

    url = reverse("api-public:routes-list")
    data_for_create = {
        "integration_id": alert_receive_channel.public_primary_key,
        "routing_regex": None,  # routing_regex cannot be null for non-default filters
        "escalation_chain_id": escalation_chain.public_primary_key,
    }
    response = client.post(url, format="json", HTTP_AUTHORIZATION=token, data=data_for_create)

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_update_route(
    route_public_api_setup,
    make_channel_filter,
):
    _, _, token, alert_receive_channel, escalation_chain, _ = route_public_api_setup
    new_channel_filter = make_channel_filter(
        alert_receive_channel,
        is_default=False,
        filtering_term="testreg",
    )

    client = APIClient()

    url = reverse("api-public:routes-detail", kwargs={"pk": new_channel_filter.public_primary_key})
    data_to_update = {
        "routing_regex": "testreg_updated",
        "escalation_chain_id": escalation_chain.public_primary_key,
    }

    assert new_channel_filter.filtering_term != data_to_update["routing_regex"]
    assert new_channel_filter.escalation_chain != escalation_chain

    response = client.put(url, format="json", HTTP_AUTHORIZATION=token, data=data_to_update)

    expected_response = {
        "id": new_channel_filter.public_primary_key,
        "integration_id": alert_receive_channel.public_primary_key,
        "escalation_chain_id": escalation_chain.public_primary_key,
        "routing_type": "regex",
        "routing_regex": data_to_update["routing_regex"],
        "position": new_channel_filter.order,
        "is_the_last_route": new_channel_filter.is_default,
        "slack": {"channel_id": new_channel_filter.slack_channel_id, "enabled": True},
        "telegram": {"id": None, "enabled": False},
        TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": False},
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response


@pytest.mark.django_db
def test_delete_route(
    route_public_api_setup,
    make_channel_filter,
):
    _, _, token, alert_receive_channel, _, _ = route_public_api_setup
    new_channel_filter = make_channel_filter(
        alert_receive_channel,
        is_default=False,
        filtering_term="testreg",
    )

    client = APIClient()

    url = reverse("api-public:routes-detail", kwargs={"pk": new_channel_filter.public_primary_key})
    response = client.delete(url, format="json", HTTP_AUTHORIZATION=token)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    with pytest.raises(ChannelFilter.DoesNotExist):
        new_channel_filter.refresh_from_db()


@pytest.mark.django_db
def test_create_route_with_messaging_backend(
    route_public_api_setup,
    make_slack_team_identity,
    make_slack_channel,
):
    organization, _, token, alert_receive_channel, escalation_chain, _ = route_public_api_setup
    slack_team_identity = make_slack_team_identity()
    organization.slack_team_identity = slack_team_identity
    organization.save(update_fields=["slack_team_identity"])

    slack_id = "TEST_SLACK_ID"

    slack_channel = make_slack_channel(slack_team_identity, slack_id=slack_id)

    client = APIClient()

    url = reverse("api-public:routes-list")

    data_for_create = {
        "integration_id": alert_receive_channel.public_primary_key,
        "routing_regex": "testreg",
        "escalation_chain_id": escalation_chain.public_primary_key,
        "slack": {"channel_id": slack_channel.slack_id, "enabled": True},
        "telegram": {"id": None, "enabled": True},
        TEST_MESSAGING_BACKEND_FIELD: {"id": TEST_MESSAGING_BACKEND_ID, "enabled": True},
    }
    response = client.post(url, format="json", HTTP_AUTHORIZATION=token, data=data_for_create)

    expected_response = {
        "id": response.data["id"],
        "integration_id": alert_receive_channel.public_primary_key,
        "escalation_chain_id": escalation_chain.public_primary_key,
        "routing_type": "regex",
        "routing_regex": data_for_create["routing_regex"],
        "position": 0,
        "is_the_last_route": False,
        "slack": {"channel_id": slack_channel.slack_id, "enabled": True},
        "telegram": {"id": None, "enabled": True},
        TEST_MESSAGING_BACKEND_FIELD: {"id": TEST_MESSAGING_BACKEND_ID, "enabled": True},
    }

    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == expected_response


@pytest.mark.django_db
def test_update_route_with_messaging_backend(
    route_public_api_setup,
    make_channel_filter,
    make_slack_team_identity,
    make_slack_channel,
):
    organization, _, token, alert_receive_channel, escalation_chain, _ = route_public_api_setup
    slack_team_identity = make_slack_team_identity()
    organization.slack_team_identity = slack_team_identity
    organization.save(update_fields=["slack_team_identity"])

    slack_id = "TEST_SLACK_ID"

    slack_channel = make_slack_channel(slack_team_identity, slack_id=slack_id)

    new_channel_filter = make_channel_filter(
        alert_receive_channel,
        is_default=False,
        filtering_term="testreg",
        escalation_chain=escalation_chain,
    )

    client = APIClient()

    url = reverse("api-public:routes-detail", kwargs={"pk": new_channel_filter.public_primary_key})
    data_to_update = {
        "slack": {"channel_id": slack_channel.slack_id, "enabled": False},
        "telegram": {"id": None, "enabled": True},
        TEST_MESSAGING_BACKEND_FIELD: {"id": TEST_MESSAGING_BACKEND_ID},
    }

    # check if route data is different
    assert new_channel_filter.slack_channel_id != slack_channel.slack_id
    assert new_channel_filter.notify_in_slack != data_to_update["slack"]["enabled"]
    assert new_channel_filter.notify_in_telegram != data_to_update["telegram"]["enabled"]
    assert new_channel_filter.notification_backends is None

    response = client.put(url, format="json", HTTP_AUTHORIZATION=token, data=data_to_update)

    expected_response = {
        "id": response.data["id"],
        "integration_id": alert_receive_channel.public_primary_key,
        "escalation_chain_id": escalation_chain.public_primary_key,
        "routing_type": "regex",
        "routing_regex": new_channel_filter.filtering_term,
        "position": 0,
        "is_the_last_route": False,
        "slack": {"channel_id": slack_channel.slack_id, "enabled": False},
        "telegram": {"id": None, "enabled": True},
        TEST_MESSAGING_BACKEND_FIELD: {"id": TEST_MESSAGING_BACKEND_ID, "enabled": False},
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response

    new_channel_filter.refresh_from_db()

    # check if route data is different was changed correctly
    assert new_channel_filter.slack_channel_id == slack_channel.slack_id
    assert new_channel_filter.notify_in_slack == data_to_update["slack"]["enabled"]
    assert new_channel_filter.notify_in_telegram == data_to_update["telegram"]["enabled"]
    assert new_channel_filter.notification_backends == {
        TestOnlyBackend.backend_id: {"channel": TEST_MESSAGING_BACKEND_ID}
    }

    data_to_update = {
        "slack": {"channel_id": None, "enabled": False},
        "telegram": {"id": None, "enabled": False},
        TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": True},
    }

    response = client.put(url, format="json", HTTP_AUTHORIZATION=token, data=data_to_update)

    expected_response = {
        "id": response.data["id"],
        "integration_id": alert_receive_channel.public_primary_key,
        "escalation_chain_id": escalation_chain.public_primary_key,
        "routing_type": "regex",
        "routing_regex": new_channel_filter.filtering_term,
        "position": 0,
        "is_the_last_route": False,
        "slack": {"channel_id": None, "enabled": False},
        "telegram": {"id": None, "enabled": False},
        TEST_MESSAGING_BACKEND_FIELD: {"id": None, "enabled": True},
    }

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_response

    new_channel_filter.refresh_from_db()

    # check if route data is different was changed correctly
    assert new_channel_filter.slack_channel_id == data_to_update["slack"]["channel_id"]
    assert new_channel_filter.notify_in_slack == data_to_update["slack"]["enabled"]
    assert new_channel_filter.notify_in_telegram == data_to_update["telegram"]["enabled"]
    assert new_channel_filter.notification_backends == {TestOnlyBackend.backend_id: {"channel": None, "enabled": True}}


@pytest.mark.django_db
def test_update_route_with_manual_ordering(
    make_organization_and_user_with_token,
    make_alert_receive_channel,
    make_channel_filter,
):
    organization, _, token = make_organization_and_user_with_token()
    alert_receive_channel = make_alert_receive_channel(organization)
    channel_filter = make_channel_filter(
        alert_receive_channel,
        is_default=False,
    )

    client = APIClient()

    url = reverse("api-public:routes-detail", kwargs={"pk": channel_filter.public_primary_key})

    # Test negative value. Note, that for "manual_order"=False, -1 is valid option (It will move route to the bottom)
    data_to_update = {"position": -1, "manual_order": True}

    response = client.put(url, format="json", HTTP_AUTHORIZATION=token, data=data_to_update)
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # Test value bigger then PositiveIntegerField can hold
    data_to_update = {"position": 9223372036854775807, "manual_order": True}

    response = client.put(url, format="json", HTTP_AUTHORIZATION=token, data=data_to_update)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
