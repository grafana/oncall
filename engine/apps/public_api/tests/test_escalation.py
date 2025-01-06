from unittest import mock

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertGroup
from apps.alerts.paging import DirectPagingAlertGroupResolvedError, DirectPagingUserTeamValidationError
from common.constants.plugin_ids import PluginID

title = "Custom title"
message = "Testing escalation with new alert group"
source_url = "https://www.example.com"


@pytest.mark.django_db
def test_escalation_new_alert_group(
    make_organization_and_user_with_token,
    make_user,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_token()

    users_to_page = [
        {
            "id": make_user(organization=organization).public_primary_key,
            "important": False,
        },
        {
            "id": make_user(organization=organization).public_primary_key,
            "important": True,
        },
    ]

    client = APIClient()
    url = reverse("api-public:escalation")

    response = client.post(
        url,
        data={
            "users": users_to_page,
            "title": title,
            "message": message,
        },
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK

    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 1
    ag = alert_groups.get()

    assert response.json() == {
        "id": ag.public_primary_key,
        "integration_id": ag.channel.public_primary_key,
        "route_id": ag.channel_filter.public_primary_key,
        "team_id": None,
        "labels": [],
        "alerts_count": 1,
        "state": "firing",
        "created_at": mock.ANY,
        "resolved_at": None,
        "resolved_by": None,
        "acknowledged_at": None,
        "acknowledged_by": None,
        "title": title,
        "permalinks": {
            "slack": None,
            "slack_app": None,
            "telegram": None,
            "web": f"a/{PluginID.ONCALL}/alert-groups/{ag.public_primary_key}",
        },
        "silenced_at": None,
        "last_alert": {
            "id": ag.alerts.last().public_primary_key,
            "alert_group_id": ag.public_primary_key,
            "created_at": ag.alerts.last().created_at.isoformat().replace("+00:00", "Z"),
            "payload": ag.alerts.last().raw_request_data,
        },
    }

    alert = ag.alerts.get()

    assert ag.web_title_cache == title
    assert alert.title == title
    assert alert.message == message


@pytest.mark.parametrize("important_team_escalation", [True, False])
@pytest.mark.django_db
def test_escalation_team(
    make_organization_and_user_with_token,
    make_team,
    make_user_auth_headers,
    important_team_escalation,
):
    organization, user, token = make_organization_and_user_with_token()
    team = make_team(organization=organization)

    # user must be part of the team
    user.teams.add(team)

    client = APIClient()
    url = reverse("api-public:escalation")

    response = client.post(
        url,
        data={
            "team": team.public_primary_key,
            "message": message,
            "source_url": source_url,
            "important_team_escalation": important_team_escalation,
        },
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK

    alert_group = AlertGroup.objects.get(public_primary_key=response.json()["id"])
    alert = alert_group.alerts.first()

    assert alert.raw_request_data == {
        "oncall": {
            "title": mock.ANY,
            "message": message,
            "uid": mock.ANY,
            "author_username": mock.ANY,
            "permalink": source_url,
            "important": important_team_escalation,
        },
    }


@pytest.mark.django_db
def test_escalation_existing_alert_group(
    make_organization_and_user_with_token,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_token()

    users_to_page = [
        {
            "id": make_user(organization=organization).public_primary_key,
            "important": False,
        },
        {
            "id": make_user(
                organization=organization,
            ).public_primary_key,
            "important": True,
        },
    ]

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    client = APIClient()
    url = reverse("api-public:escalation")

    response = client.post(
        url,
        data={"users": users_to_page, "alert_group_id": alert_group.public_primary_key},
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == alert_group.public_primary_key


@pytest.mark.django_db
def test_escalation_existing_alert_group_resolved(
    make_organization_and_user_with_token,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_token()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, resolved=True)

    users_to_page = [
        {
            "id": make_user(organization=organization).public_primary_key,
            "important": False,
        },
    ]

    client = APIClient()
    url = reverse("api-public:escalation")

    response = client.post(
        url,
        data={
            "alert_group_id": alert_group.public_primary_key,
            "users": users_to_page,
        },
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == DirectPagingAlertGroupResolvedError.DETAIL


@pytest.mark.django_db
def test_escalation_no_user_or_team_specified(
    make_organization_and_user_with_token,
    make_user_auth_headers,
):
    _, user, token = make_organization_and_user_with_token()

    client = APIClient()
    url = reverse("api-public:escalation")

    response = client.post(
        url,
        data={
            "team": None,
            "users": [],
        },
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["detail"] == DirectPagingUserTeamValidationError.DETAIL


@pytest.mark.django_db
def test_escalation_both_team_and_users_specified(
    make_organization_and_user_with_token,
    make_user_auth_headers,
    make_user,
    make_team,
):
    organization, user, token = make_organization_and_user_with_token()
    team = make_team(organization=organization)

    client = APIClient()
    url = reverse("api-public:escalation")

    response = client.post(
        url,
        data={
            "team": team.public_primary_key,
            "users": [
                {
                    "id": make_user(organization=organization).public_primary_key,
                    "important": False,
                },
            ],
        },
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["non_field_errors"] == ["users and team are mutually exclusive"]


@pytest.mark.parametrize(
    "field_name,field_value",
    [
        ("title", title),
        ("message", message),
        ("source_url", source_url),
    ],
)
@pytest.mark.django_db
def test_escalation_alert_group_id_and_other_fields_are_mutually_exclusive(
    make_organization_and_user_with_token,
    make_team,
    make_user_auth_headers,
    make_alert_receive_channel,
    make_alert_group,
    field_name,
    field_value,
):
    error_msg = "alert_group_id and (title, message, source_url) are mutually exclusive"

    organization, user, token = make_organization_and_user_with_token()
    team = make_team(organization=organization)

    # user must be part of the team
    user.teams.add(team)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, resolved=True)

    client = APIClient()
    url = reverse("api-public:escalation")

    response = client.post(
        url,
        data={
            "team": team.public_primary_key,
            "alert_group_id": alert_group.public_primary_key,
            field_name: field_value,
        },
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()["non_field_errors"] == [error_msg]
