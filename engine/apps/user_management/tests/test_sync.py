from unittest.mock import patch

import pytest
from django.core.exceptions import ObjectDoesNotExist

from apps.grafana_plugin.helpers.client import GcomAPIClient, GrafanaAPIClient
from apps.user_management.models import Team, User
from apps.user_management.sync import cleanup_organization, sync_organization
from conftest import IS_RBAC_ENABLED


@pytest.mark.django_db
def test_sync_users_for_organization(make_organization, make_user_for_organization):
    organization = make_organization()
    users = tuple(make_user_for_organization(organization, user_id=user_id) for user_id in (1, 2))

    api_users = tuple(
        {
            "userId": user_id,
            "email": "test@test.test",
            "name": "Test",
            "login": "test",
            "role": "admin",
            "avatarUrl": "test.test/test",
            "permissions": [],
        }
        for user_id in (2, 3)
    )

    User.objects.sync_for_organization(organization, api_users=api_users)

    assert organization.users.count() == 2

    # check that excess users are deleted
    assert not organization.users.filter(pk=users[0].pk).exists()

    # check that existing users are updated
    updated_user = organization.users.filter(pk=users[1].pk).first()
    assert updated_user is not None
    assert updated_user.name == api_users[0]["name"]
    assert updated_user.email == api_users[0]["email"]

    # check that missing users are created
    created_user = organization.users.filter(user_id=api_users[1]["userId"]).first()
    assert created_user is not None
    assert created_user.user_id == api_users[1]["userId"]
    assert created_user.name == api_users[1]["name"]


@pytest.mark.django_db
def test_sync_teams_for_organization(make_organization, make_team):
    organization = make_organization()
    teams = tuple(make_team(organization, team_id=team_id) for team_id in (1, 2))

    api_teams = tuple(
        {"id": team_id, "name": "Test", "email": "test@test.test", "avatarUrl": "test.test/test"} for team_id in (2, 3)
    )

    Team.objects.sync_for_organization(organization, api_teams=api_teams)

    assert organization.teams.count() == 2

    # check that excess teams are deleted
    assert not organization.teams.filter(pk=teams[0].pk).exists()

    # check that existing teams are updated
    updated_team = organization.teams.filter(pk=teams[1].pk).first()
    assert updated_team is not None
    assert updated_team.name == api_teams[0]["name"]
    assert updated_team.email == api_teams[0]["email"]

    # check that missing teams are created
    created_team = organization.teams.filter(team_id=api_teams[1]["id"]).first()
    assert created_team is not None
    assert created_team.team_id == api_teams[1]["id"]
    assert created_team.name == api_teams[1]["name"]


@pytest.mark.django_db
def test_sync_users_for_team(make_organization, make_user_for_organization, make_team):
    organization = make_organization()
    team = make_team(organization)
    users = tuple(make_user_for_organization(organization) for _ in range(2))

    api_members = (
        {
            "orgId": organization.org_id,
            "teamId": team.team_id,
            "userId": users[0].user_id,
        },
    )

    User.objects.sync_for_team(team, api_members=api_members)

    assert team.users.count() == 1
    assert team.users.get() == users[0]


@pytest.mark.django_db
def test_sync_organization(make_organization, make_team, make_user_for_organization):
    organization = make_organization()

    api_users_response = (
        {
            "userId": 1,
            "email": "test@test.test",
            "name": "Test",
            "login": "test",
            "role": "admin",
            "avatarUrl": "test.test/test",
            "permissions": [],
        },
    )

    api_teams_response = {
        "totalCount": 1,
        "teams": (
            {
                "id": 1,
                "name": "Test",
                "email": "test@test.test",
                "avatarUrl": "test.test/test",
            },
        ),
    }

    api_members_response = (
        {
            "orgId": organization.org_id,
            "teamId": 1,
            "userId": 1,
        },
    )

    with patch.object(GrafanaAPIClient, "is_rbac_enabled_for_organization", return_value=IS_RBAC_ENABLED):
        with patch.object(GrafanaAPIClient, "get_users", return_value=api_users_response):
            with patch.object(GrafanaAPIClient, "get_teams", return_value=(api_teams_response, None)):
                with patch.object(GrafanaAPIClient, "get_team_members", return_value=(api_members_response, None)):
                    sync_organization(organization)

    # check that users are populated
    assert organization.users.count() == 1
    user = organization.users.get()
    assert user.user_id == 1

    # check that teams are populated
    assert organization.teams.count() == 1
    team = organization.teams.get()
    assert team.team_id == 1

    # check that team members are populated
    assert team.users.count() == 1
    assert team.users.get() == user

    # check that the rbac flag is properly set on the org
    assert organization.is_rbac_permissions_enabled == IS_RBAC_ENABLED


@pytest.mark.django_db
def test_duplicate_user_ids(make_organization, make_user_for_organization):
    organization = make_organization()

    user = make_user_for_organization(organization, user_id=1)
    api_users = []

    User.objects.sync_for_organization(organization, api_users=api_users)

    user.refresh_from_db()

    assert user.is_active is None
    assert organization.users.count() == 0
    assert User.objects.filter_with_deleted().count() == 1

    api_users = [
        {
            "userId": 1,
            "email": "newtest@test.test",
            "name": "New Test",
            "login": "test",
            "role": "admin",
            "avatarUrl": "test.test/test",
            "permissions": [],
        }
    ]

    User.objects.sync_for_organization(organization, api_users=api_users)

    assert organization.users.count() == 1
    assert organization.users.get().email == "newtest@test.test"
    assert User.objects.filter_with_deleted().count() == 2


@pytest.mark.django_db
def test_cleanup_organization_deleted(make_organization):
    organization = make_organization(gcom_token="TEST_GCOM_TOKEN")

    with patch.object(GcomAPIClient, "get_instance_info", return_value={"status": "deleted"}):
        cleanup_organization(organization.id)

    with pytest.raises(ObjectDoesNotExist):
        organization.refresh_from_db()
