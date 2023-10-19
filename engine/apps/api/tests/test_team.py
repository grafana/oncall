import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.api.permissions import LegacyAccessControlRole
from apps.schedules.models import CustomOnCallShift, OnCallScheduleCalendar, OnCallScheduleWeb
from apps.user_management.models import Team

GENERAL_TEAM = Team(public_primary_key="null", name="No team", email=None, avatar_url=None)


def get_payload_from_team(team):
    return {
        "id": team.public_primary_key,
        "name": team.name,
        "email": team.email,
        "avatar_url": team.avatar_url,
        "is_sharing_resources_to_all": team.is_sharing_resources_to_all,
        "number_of_users_currently_oncall": 0,
    }


@pytest.mark.django_db
def test_list_teams(
    make_organization,
    make_team,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    _, token = make_token_for_organization(organization)

    team = make_team(organization)
    team.users.add(user)

    general_team_payload = get_payload_from_team(GENERAL_TEAM)
    team_payload = get_payload_from_team(team)

    client = APIClient()
    url = reverse("api-internal:team-list")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [general_team_payload, team_payload]

    url = reverse("api-internal:team-list")
    response = client.get(f"{url}?include_no_team=false", format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [team_payload]


@pytest.mark.django_db
def test_teams_number_of_users_currently_oncall_attribute_works_properly(
    make_organization,
    make_team,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    make_schedule,
    make_on_call_shift,
):
    organization = make_organization()
    user1 = make_user_for_organization(organization)
    user2 = make_user_for_organization(organization)
    user3 = make_user_for_organization(organization)
    _, token = make_token_for_organization(organization)

    today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    team1 = make_team(organization)
    team2 = make_team(organization)
    team3 = make_team(organization)

    team1.users.set([user1, user2, user3])
    team2.users.set([user1])
    team3.users.set([user3])

    def _make_schedule(team=None, oncall_users=[]):
        schedule = make_schedule(organization, schedule_class=OnCallScheduleWeb)

        if team:
            schedule.team = team
            schedule.save()

        if oncall_users:
            on_call_shift = make_on_call_shift(
                organization=organization,
                shift_type=CustomOnCallShift.TYPE_ROLLING_USERS_EVENT,
                start=today,
                rotation_start=today,
                duration=timezone.timedelta(seconds=24 * 60 * 60),
                priority_level=1,
                frequency=CustomOnCallShift.FREQUENCY_DAILY,
                schedule=schedule,
            )
            on_call_shift.add_rolling_users([oncall_users])
            schedule.refresh_ical_file()
            schedule.refresh_ical_final_schedule()

    _make_schedule(team=team1, oncall_users=[user1, user2])
    _make_schedule(team=team2, oncall_users=[user1])
    _make_schedule(team=team3, oncall_users=[])

    client = APIClient()
    url = reverse("api-internal:team-list")

    response = client.get(url, format="json", **make_user_auth_headers(user1, token))

    number_of_oncall_users = {
        team1.public_primary_key: 2,
        team2.public_primary_key: 1,
        team3.public_primary_key: 0,
        "null": 0,  # this covers the case of "No team"
    }

    for team in response.json():
        assert team["number_of_users_currently_oncall"] == number_of_oncall_users[team["id"]]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "search,team_names",
    [
        ("", [GENERAL_TEAM.name, "team 1", "team 2"]),
        ("team", [GENERAL_TEAM.name, "team 1", "team 2"]),
        ("no team", [GENERAL_TEAM.name]),
        ("team ", [GENERAL_TEAM.name, "team 1", "team 2"]),
        ("team 1", [GENERAL_TEAM.name, "team 1"]),
    ],
)
def test_list_teams_search_by_name(
    make_organization,
    make_team,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
    search,
    team_names,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    _, token = make_token_for_organization(organization)

    for team_name in team_names:
        if team_name != GENERAL_TEAM.name:
            make_team(organization, name=team_name)

    client = APIClient()

    url = reverse("api-internal:team-list") + f"?search={search}"
    response = client.get(url, format="json", **make_user_auth_headers(user, token))
    assert response.status_code == status.HTTP_200_OK

    expected_json = [
        get_payload_from_team(organization.teams.get(name=team_name))
        if team_name != GENERAL_TEAM.name
        else get_payload_from_team(GENERAL_TEAM)
        for team_name in team_names
    ]
    assert response.json() == expected_json


@pytest.mark.django_db
def test_list_teams_for_non_member(
    make_organization,
    make_team,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    make_team(organization)
    user = make_user_for_organization(organization, role=LegacyAccessControlRole.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()
    url = reverse("api-internal:team-list")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [get_payload_from_team(GENERAL_TEAM)]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "role,expected_status",
    [
        (LegacyAccessControlRole.ADMIN, status.HTTP_200_OK),
        (LegacyAccessControlRole.EDITOR, status.HTTP_200_OK),
        (LegacyAccessControlRole.VIEWER, status.HTTP_200_OK),
    ],
)
def test_list_teams_permissions(
    make_organization_and_user_with_plugin_token,
    make_user_auth_headers,
    role,
    expected_status,
):
    _, user, token = make_organization_and_user_with_plugin_token(role)

    client = APIClient()
    url = reverse("api-internal:team-list")
    response = client.get(url, format="json", **make_user_auth_headers(user, token))

    assert response.status_code == expected_status


@pytest.mark.django_db
def test_update_team(
    make_organization,
    make_team,
    make_user_for_organization,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()
    user = make_user_for_organization(organization)
    _, token = make_token_for_organization(organization)

    team = make_team(organization)
    team.users.add(user)

    client = APIClient()
    url = reverse("api-internal:team-detail", kwargs={"pk": team.public_primary_key})

    response = client.put(
        url, data={"is_sharing_resources_to_all": True}, format="json", **make_user_auth_headers(user, token)
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["is_sharing_resources_to_all"] is True


@pytest.mark.django_db
def test_team_permissions_wrong_team(
    make_organization,
    make_team,
    make_alert_group,
    make_alert_receive_channel,
    make_user,
    make_escalation_chain,
    make_schedule,
    make_custom_action,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()

    user = make_user(organization=organization, role=LegacyAccessControlRole.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()

    team_with_user = make_team(organization)
    team_without_user = make_team(organization)

    user.teams.add(team_with_user)

    alert_receive_channel = make_alert_receive_channel(organization, team=team_without_user)
    alert_group = make_alert_group(alert_receive_channel)

    escalation_chain = make_escalation_chain(organization, team=team_without_user)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar, team=team_without_user)
    webhook = make_custom_action(organization, team=team_without_user)

    for endpoint, instance in (
        ("alertgroup", alert_group),
        ("alert_receive_channel", alert_receive_channel),
        ("escalation_chain", escalation_chain),
        ("schedule", schedule),
        ("custom_button", webhook),
    ):
        url = reverse(f"api-internal:{endpoint}-detail", kwargs={"pk": instance.public_primary_key})

        response = client.get(url, **make_user_auth_headers(user, token))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"error_code": "wrong_team"}


@pytest.mark.django_db
def test_team_permissions_not_in_team(
    make_organization,
    make_team,
    make_alert_group,
    make_alert_receive_channel,
    make_user,
    make_escalation_chain,
    make_schedule,
    make_custom_action,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()

    user = make_user(organization=organization, role=LegacyAccessControlRole.EDITOR)
    _, token = make_token_for_organization(organization)

    client = APIClient()

    team = make_team(organization)

    another_user = make_user(organization=organization)
    another_user.teams.add(team)
    another_user.current_team = team
    another_user.save(update_fields=["current_team"])

    alert_receive_channel = make_alert_receive_channel(organization, team=team)
    alert_group = make_alert_group(alert_receive_channel)

    escalation_chain = make_escalation_chain(organization, team=team)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar, team=team)
    webhook = make_custom_action(organization, team=team)

    for endpoint, instance in (
        ("alertgroup", alert_group),
        ("alert_receive_channel", alert_receive_channel),
        ("escalation_chain", escalation_chain),
        ("schedule", schedule),
        ("custom_button", webhook),
    ):
        url = reverse(f"api-internal:{endpoint}-detail", kwargs={"pk": instance.public_primary_key})

        response = client.get(url, **make_user_auth_headers(user, token))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json() == {"error_code": "wrong_team"}

    # Editor cannot retrieve other user information
    url = reverse("api-internal:user-detail", kwargs={"pk": another_user.public_primary_key})
    response = client.get(url, **make_user_auth_headers(user, token))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_team_permissions_right_team(
    make_organization,
    make_team,
    make_alert_group,
    make_alert_receive_channel,
    make_user,
    make_escalation_chain,
    make_schedule,
    make_custom_action,
    make_token_for_organization,
    make_user_auth_headers,
):
    organization = make_organization()

    user = make_user(organization=organization)
    _, token = make_token_for_organization(organization)

    client = APIClient()

    team = make_team(organization)

    user.teams.add(team)
    user.current_team = team
    user.save(update_fields=["current_team"])

    another_user = make_user(organization=organization)
    another_user.teams.add(team)

    alert_receive_channel = make_alert_receive_channel(organization, team=team)
    alert_group = make_alert_group(alert_receive_channel)

    escalation_chain = make_escalation_chain(organization, team=team)
    schedule = make_schedule(organization, schedule_class=OnCallScheduleCalendar, team=team)
    webhook = make_custom_action(organization, team=team)

    for endpoint, instance in (
        ("alertgroup", alert_group),
        ("alert_receive_channel", alert_receive_channel),
        ("escalation_chain", escalation_chain),
        ("schedule", schedule),
        ("custom_button", webhook),
        ("user", another_user),
    ):
        url = reverse(f"api-internal:{endpoint}-detail", kwargs={"pk": instance.public_primary_key})

        response = client.get(url, **make_user_auth_headers(user, token))

        assert response.status_code == status.HTTP_200_OK
