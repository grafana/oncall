import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertReceiveChannel
from apps.user_management.models import Organization

# TODO: should probably modify these tests to take into account new rbac permissions


@pytest.fixture()
def maintenance_internal_api_setup(
    make_organization_and_user_with_plugin_token,
    make_escalation_chain,
    make_alert_receive_channel,
):
    organization, user, token = make_organization_and_user_with_plugin_token()
    make_escalation_chain(organization)
    alert_receive_channel = make_alert_receive_channel(organization)
    return token, organization, user, alert_receive_channel


@pytest.mark.django_db
def test_start_maintenance_integration(
    maintenance_internal_api_setup, mock_start_disable_maintenance_task, make_user_auth_headers
):
    token, _, user, alert_receive_channel = maintenance_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:start_maintenance")
    data = {
        "mode": AlertReceiveChannel.MAINTENANCE,
        "duration": AlertReceiveChannel.DURATION_ONE_HOUR.total_seconds(),
        "type": "alert_receive_channel",
        "alert_receive_channel_id": alert_receive_channel.public_primary_key,
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
def test_start_maintenance_integration_user_team(
    maintenance_internal_api_setup, mock_start_disable_maintenance_task, make_user_auth_headers, make_team
):
    token, organization, user, alert_receive_channel = maintenance_internal_api_setup
    another_team = make_team(organization)
    user.current_team = another_team
    user.save()

    client = APIClient()

    url = reverse("api-internal:start_maintenance")
    data = {
        "mode": AlertReceiveChannel.MAINTENANCE,
        "duration": AlertReceiveChannel.DURATION_ONE_HOUR.total_seconds(),
        "type": "alert_receive_channel",
        "alert_receive_channel_id": alert_receive_channel.public_primary_key,
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
def test_start_maintenance_integration_different_team(
    maintenance_internal_api_setup, mock_start_disable_maintenance_task, make_user_auth_headers, make_team
):
    token, organization, user, alert_receive_channel = maintenance_internal_api_setup
    another_team = make_team(organization)
    other_team = make_team(organization)
    user.current_team = another_team
    user.save()
    # integration belongs to non-general team, != user current team
    alert_receive_channel.team = other_team
    alert_receive_channel.save()

    client = APIClient()

    url = reverse("api-internal:start_maintenance")
    data = {
        "mode": AlertReceiveChannel.MAINTENANCE,
        "duration": AlertReceiveChannel.DURATION_ONE_HOUR.total_seconds(),
        "type": "alert_receive_channel",
        "alert_receive_channel_id": alert_receive_channel.public_primary_key,
    }
    response = client.post(url, data=data, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    alert_receive_channel.refresh_from_db()
    assert alert_receive_channel.maintenance_mode is None


@pytest.mark.django_db
def test_stop_maintenance_integration(
    maintenance_internal_api_setup,
    mock_start_disable_maintenance_task,
    make_user_auth_headers,
):
    token, _, user, alert_receive_channel = maintenance_internal_api_setup
    client = APIClient()
    mode = AlertReceiveChannel.MAINTENANCE
    duration = AlertReceiveChannel.DURATION_ONE_HOUR.seconds
    alert_receive_channel.start_maintenance(mode, duration, user)
    url = reverse("api-internal:stop_maintenance")
    data = {
        "type": "alert_receive_channel",
        "alert_receive_channel_id": alert_receive_channel.public_primary_key,
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
def test_start_maintenance_organization(
    maintenance_internal_api_setup,
    mock_start_disable_maintenance_task,
    make_user_auth_headers,
):
    token, organization, user, _ = maintenance_internal_api_setup
    client = APIClient()

    url = reverse("api-internal:start_maintenance")
    data = {
        "mode": Organization.MAINTENANCE,
        "duration": Organization.DURATION_ONE_HOUR.total_seconds(),
        "type": "organization",
    }
    response = client.post(url, data=data, format="json", **make_user_auth_headers(user, token))

    organization.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert organization.maintenance_mode == Organization.MAINTENANCE
    assert organization.maintenance_duration == Organization.DURATION_ONE_HOUR
    assert organization.maintenance_uuid is not None
    assert organization.maintenance_started_at is not None
    assert organization.maintenance_author is not None


@pytest.mark.django_db
def test_stop_maintenance_team(
    maintenance_internal_api_setup,
    mock_start_disable_maintenance_task,
    make_user_auth_headers,
):
    token, organization, user, _ = maintenance_internal_api_setup
    client = APIClient()
    mode = Organization.MAINTENANCE
    duration = AlertReceiveChannel.DURATION_ONE_HOUR.seconds
    organization.start_maintenance(mode, duration, user)
    url = reverse("api-internal:stop_maintenance")
    data = {
        "type": "organization",
    }
    response = client.post(url, data=data, format="json", **make_user_auth_headers(user, token))
    organization.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert organization.maintenance_mode is None
    assert organization.maintenance_duration is None
    assert organization.maintenance_uuid is None
    assert organization.maintenance_started_at is None
    assert organization.maintenance_author is None


@pytest.mark.django_db
def test_maintenances_list(
    maintenance_internal_api_setup,
    mock_start_disable_maintenance_task,
    make_user_auth_headers,
):
    token, organization, user, alert_receive_channel = maintenance_internal_api_setup
    client = APIClient()
    mode = AlertReceiveChannel.MAINTENANCE
    duration = AlertReceiveChannel.DURATION_ONE_HOUR.seconds
    alert_receive_channel.start_maintenance(mode, duration, user)
    organization.start_maintenance(mode, duration, user)
    url = reverse("api-internal:maintenance")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    expected_payload = [
        {
            "organization_id": organization.public_primary_key,
            "type": "organization",
            "maintenance_mode": 1,
            "maintenance_till_timestamp": organization.till_maintenance_timestamp,
            "started_at_timestamp": organization.started_at_timestamp,
        },
        {
            "alert_receive_channel_id": alert_receive_channel.public_primary_key,
            "type": "alert_receive_channel",
            "maintenance_mode": 1,
            "maintenance_till_timestamp": alert_receive_channel.till_maintenance_timestamp,
            "started_at_timestamp": alert_receive_channel.started_at_timestamp,
        },
    ]

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_maintenances_list_include_all_user_teams(
    maintenance_internal_api_setup,
    mock_start_disable_maintenance_task,
    make_user_auth_headers,
    make_team,
):
    token, organization, user, alert_receive_channel = maintenance_internal_api_setup
    another_team = make_team(organization)
    other_team = make_team(organization)
    # setup user teams
    user.teams.add(another_team)
    user.teams.add(other_team)
    user.current_team = other_team
    user.save()
    # integration belongs to non-general team, != user current team
    alert_receive_channel.team = another_team
    alert_receive_channel.save()

    client = APIClient()
    mode = AlertReceiveChannel.MAINTENANCE
    duration = AlertReceiveChannel.DURATION_ONE_HOUR.seconds
    alert_receive_channel.start_maintenance(mode, duration, user)
    url = reverse("api-internal:maintenance")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    expected_payload = [
        {
            "alert_receive_channel_id": alert_receive_channel.public_primary_key,
            "type": "alert_receive_channel",
            "maintenance_mode": 1,
            "maintenance_till_timestamp": alert_receive_channel.till_maintenance_timestamp,
            "started_at_timestamp": alert_receive_channel.started_at_timestamp,
        },
    ]

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == expected_payload


@pytest.mark.django_db
def test_empty_maintenances_list(
    maintenance_internal_api_setup, mock_start_disable_maintenance_task, make_user_auth_headers
):
    token, _, user, alert_receive_channel = maintenance_internal_api_setup
    client = APIClient()
    url = reverse("api-internal:maintenance")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    expected_payload = []
    alert_receive_channel.refresh_from_db()
    assert response.status_code == status.HTTP_200_OK
    assert response.data == expected_payload
