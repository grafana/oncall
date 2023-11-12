import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.alerts.models import AlertGroup
from apps.alerts.paging import DirectPagingAlertGroupResolvedError, DirectPagingUserTeamValidationError
from apps.api.permissions import LegacyAccessControlRole

title = "Custom title"
message = "Testing direct paging with new alert group"
source_url = "https://www.example.com"
grafana_incident_id = "abcd1234"


@pytest.mark.django_db
def test_direct_paging_new_alert_group(
    make_organization_and_user_with_plugin_token,
    make_user,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    users_to_page = [
        {
            "id": make_user(organization=organization, role=LegacyAccessControlRole.ADMIN).public_primary_key,
            "important": False,
        },
        {
            "id": make_user(organization=organization, role=LegacyAccessControlRole.EDITOR).public_primary_key,
            "important": True,
        },
    ]

    client = APIClient()
    url = reverse("api-internal:direct_paging")

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
    assert "alert_group_id" in response.json()

    alert_groups = AlertGroup.objects.all()
    assert alert_groups.count() == 1
    ag = alert_groups.get()
    alert = ag.alerts.get()

    assert ag.web_title_cache == title
    assert alert.title == title
    assert alert.message == message


@pytest.mark.django_db
def test_direct_paging_page_team(
    make_organization_and_user_with_plugin_token,
    make_team,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    team = make_team(organization=organization)

    # user must be part of the team
    user.teams.add(team)

    client = APIClient()
    url = reverse("api-internal:direct_paging")

    response = client.post(
        url,
        data={
            "team": team.public_primary_key,
            "message": message,
            "source_url": source_url,
            "grafana_incident_id": grafana_incident_id,
        },
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK

    alert_group = AlertGroup.objects.get(public_primary_key=response.json()["alert_group_id"])
    alert = alert_group.alerts.first()

    assert alert_group.grafana_incident_id == grafana_incident_id
    assert alert.raw_request_data["oncall"]["permalink"] == source_url


@pytest.mark.django_db
def test_direct_paging_page_from_grafana_incident(
    make_organization_and_user_with_plugin_token,
    make_team,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    team = make_team(organization=organization)

    # user must be part of the team
    user.teams.add(team)

    client = APIClient()
    url = reverse("api-internal:direct_paging")

    response = client.post(
        url,
        data={
            "team": team.public_primary_key,
            "message": message,
            "grafana_incident_id": "asdf",
        },
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK
    assert "alert_group_id" in response.json()


@pytest.mark.django_db
def test_direct_paging_existing_alert_group(
    make_organization_and_user_with_plugin_token,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    users_to_page = [
        {
            "id": make_user(organization=organization, role=LegacyAccessControlRole.ADMIN).public_primary_key,
            "important": False,
        },
        {
            "id": make_user(organization=organization, role=LegacyAccessControlRole.EDITOR).public_primary_key,
            "important": True,
        },
    ]

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    client = APIClient()
    url = reverse("api-internal:direct_paging")

    response = client.post(
        url,
        data={"users": users_to_page, "alert_group_id": alert_group.public_primary_key},
        format="json",
        **make_user_auth_headers(user, token),
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["alert_group_id"] == alert_group.public_primary_key


@pytest.mark.django_db
def test_direct_paging_existing_alert_group_resolved(
    make_organization_and_user_with_plugin_token,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_user_auth_headers,
):
    organization, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, resolved=True)

    users_to_page = [
        {
            "id": make_user(organization=organization, role=LegacyAccessControlRole.ADMIN).public_primary_key,
            "important": False,
        },
    ]

    client = APIClient()
    url = reverse("api-internal:direct_paging")

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
def test_direct_paging_no_user_or_team_specified(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
):
    _, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)

    client = APIClient()
    url = reverse("api-internal:direct_paging")

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


@pytest.mark.parametrize(
    "field_name,field_value",
    [
        ("title", title),
        ("message", message),
        ("source_url", source_url),
        ("grafana_incident_id", grafana_incident_id),
    ],
)
@pytest.mark.django_db
def test_direct_paging_alert_group_id_and_other_fields_are_mutually_exclusive(
    make_organization_and_user_with_plugin_token,
    make_team,
    make_user_auth_headers,
    make_alert_receive_channel,
    make_alert_group,
    field_name,
    field_value,
):
    error_msg = "alert_group_id and (title, message, source_url, grafana_incident_id) are mutually exclusive"

    organization, user, token = make_organization_and_user_with_plugin_token(role=LegacyAccessControlRole.EDITOR)
    team = make_team(organization=organization)

    # user must be part of the team
    user.teams.add(team)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, resolved=True)

    client = APIClient()
    url = reverse("api-internal:direct_paging")

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
