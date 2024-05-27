from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import override_settings

from apps.alerts.models import AlertReceiveChannel
from apps.api.permissions import LegacyAccessControlRole
from apps.grafana_plugin.helpers.client import GrafanaAPIClient
from apps.user_management.models import Team, User
from apps.user_management.sync import (
    _sync_grafana_incident_plugin,
    _sync_grafana_labels_plugin,
    cleanup_organization,
    sync_organization,
)

MOCK_GRAFANA_INCIDENT_BACKEND_URL = "https://grafana-incident.test"


@contextmanager
def patched_grafana_api_client(organization, is_rbac_enabled_for_organization=False):
    GRAFANA_INCIDENT_PLUGIN_BACKEND_URL_KEY = "backendUrl"

    with patch("apps.user_management.sync.GrafanaAPIClient") as mock_grafana_api_client:
        mock_grafana_api_client.GRAFANA_INCIDENT_PLUGIN_BACKEND_URL_KEY = GRAFANA_INCIDENT_PLUGIN_BACKEND_URL_KEY

        mock_client_instance = mock_grafana_api_client.return_value

        mock_client_instance.get_users.return_value = [
            {
                "userId": 1,
                "email": "test@test.test",
                "name": "Test",
                "login": "test",
                "role": "admin",
                "avatarUrl": "test.test/test",
                "permissions": [],
            },
        ]
        mock_client_instance.get_teams.return_value = (
            {
                "totalCount": 1,
                "teams": (
                    {
                        "id": 1,
                        "name": "Test",
                        "email": "test@test.test",
                        "avatarUrl": "test.test/test",
                    },
                ),
            },
            None,
        )
        mock_client_instance.get_team_members.return_value = (
            [
                {
                    "orgId": organization.org_id,
                    "teamId": 1,
                    "userId": 1,
                },
            ],
            None,
        )
        mock_client_instance.get_grafana_incident_plugin_settings.return_value = (
            {"enabled": True, "jsonData": {GRAFANA_INCIDENT_PLUGIN_BACKEND_URL_KEY: MOCK_GRAFANA_INCIDENT_BACKEND_URL}},
            None,
        )
        mock_client_instance.get_grafana_labels_plugin_settings.return_value = (
            {"enabled": True, "jsonData": {}},
            None,
        )
        mock_client_instance.check_token.return_value = (None, {"connected": True})
        mock_client_instance.is_rbac_enabled_for_organization.return_value = is_rbac_enabled_for_organization

        yield mock_grafana_api_client


@pytest.mark.django_db
def test_sync_users_for_organization(make_organization, make_user_for_organization):
    organization = make_organization(grafana_url="https://test.test")
    users = tuple(make_user_for_organization(organization, user_id=user_id) for user_id in (1, 2))

    api_users = tuple(
        {
            "userId": user_id,
            "email": "test@test.test",
            "name": "Test",
            "login": "test",
            "role": "admin",
            "avatarUrl": "/test/1234",
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
    assert updated_user.avatar_full_url == "https://test.test/test/1234"

    # check that missing users are created
    created_user = organization.users.filter(user_id=api_users[1]["userId"]).first()
    assert created_user is not None
    assert created_user.user_id == api_users[1]["userId"]
    assert created_user.name == api_users[1]["name"]
    assert created_user.avatar_full_url == "https://test.test/test/1234"

    assert created_user.notification_policies.filter(important=False).count() == 1
    assert (
        created_user.notification_policies.filter(important=False).first().notify_by
        == settings.EMAIL_BACKEND_INTERNAL_ID
    )

    assert created_user.notification_policies.filter(important=True).count() == 1
    assert (
        created_user.notification_policies.filter(important=True).first().notify_by
        == settings.EMAIL_BACKEND_INTERNAL_ID
    )


@pytest.mark.django_db
def test_sync_users_for_organization_role_none(make_organization, make_user_for_organization):
    organization = make_organization(grafana_url="https://test.test")
    users = tuple(make_user_for_organization(organization, user_id=user_id) for user_id in (1, 2))

    api_users = tuple(
        {
            "userId": user_id,
            "email": "test@test.test",
            "name": "Test",
            "login": "test",
            "role": "None",
            "avatarUrl": "/test/1234",
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
    assert updated_user.role == LegacyAccessControlRole.NONE

    # check that missing users are created
    created_user = organization.users.filter(user_id=api_users[1]["userId"]).first()
    assert created_user is not None
    assert created_user.user_id == api_users[1]["userId"]
    assert created_user.role == LegacyAccessControlRole.NONE


@pytest.mark.django_db
def test_sync_teams_for_organization(make_organization, make_team, make_alert_receive_channel):
    organization = make_organization()
    teams = tuple(make_team(organization, team_id=team_id) for team_id in (1, 2, 3))
    direct_paging_integrations = tuple(
        make_alert_receive_channel(organization, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING, team=team)
        for team in teams[:2]
    )

    api_teams = tuple(
        {"id": team_id, "name": "Test", "email": "test@test.test", "avatarUrl": "test.test/test"}
        for team_id in (2, 3, 4)
    )

    Team.objects.sync_for_organization(organization, api_teams=api_teams)

    assert organization.teams.count() == 3

    # check that excess teams and direct paging integrations are deleted
    assert not organization.teams.filter(pk=teams[0].pk).exists()
    assert not organization.alert_receive_channels.filter(pk=direct_paging_integrations[0].pk).exists()

    # check that existing teams are updated
    updated_team = organization.teams.filter(pk=teams[1].pk).first()
    assert updated_team is not None
    assert updated_team.name == api_teams[0]["name"]
    assert updated_team.email == api_teams[0]["email"]
    assert organization.alert_receive_channels.filter(pk=direct_paging_integrations[1].pk).exists()

    # check that missing teams are created
    created_team = organization.teams.filter(team_id=api_teams[2]["id"]).first()
    assert created_team is not None
    assert created_team.team_id == api_teams[2]["id"]
    assert created_team.name == api_teams[2]["name"]

    # check that direct paging is created for created team
    direct_paging_integration = AlertReceiveChannel.objects.get(
        organization=organization,
        integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING,
        team=created_team,
    )
    assert direct_paging_integration.channel_filters.count() == 1
    assert direct_paging_integration.channel_filters.first().order == 0
    assert direct_paging_integration.channel_filters.first().is_default

    # check that direct paging is created for existing team
    direct_paging_integration = AlertReceiveChannel.objects.get(
        organization=organization, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING, team=teams[2]
    )
    assert direct_paging_integration.channel_filters.count() == 1
    assert direct_paging_integration.channel_filters.first().order == 0
    assert direct_paging_integration.channel_filters.first().is_default


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
@patch("apps.user_management.sync.org_sync_signal")
def test_sync_organization(mocked_org_sync_signal, make_organization):
    organization = make_organization()

    with patched_grafana_api_client(organization):
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

    # check that is_grafana_incident_enabled flag is set
    assert organization.is_grafana_incident_enabled is True
    assert organization.grafana_incident_backend_url == MOCK_GRAFANA_INCIDENT_BACKEND_URL

    # check that is_grafana_labels_enabled flag is set
    assert organization.is_grafana_labels_enabled is True

    mocked_org_sync_signal.send.assert_called_once_with(sender=None, organization=organization)


@pytest.mark.parametrize("is_rbac_enabled_for_organization", [False, True])
@override_settings(LICENSE=settings.OPEN_SOURCE_LICENSE_NAME)
@pytest.mark.django_db
def test_sync_organization_is_rbac_permissions_enabled_open_source(make_organization, is_rbac_enabled_for_organization):
    organization = make_organization()

    with patched_grafana_api_client(organization, is_rbac_enabled_for_organization):
        sync_organization(organization)

    organization.refresh_from_db()
    assert organization.is_rbac_permissions_enabled == is_rbac_enabled_for_organization


@pytest.mark.parametrize(
    "gcom_api_response,grafana_api_response,org_initial_value,org_is_rbac_permissions_enabled_expected_value",
    [
        # stack is in an inactive state, rely on org's previous state of is_rbac_permissions_enabled
        (False, False, False, False),
        (False, False, True, True),
        # stack is active, Grafana API tells us RBAC is not enabled
        (True, False, True, False),
        # stack is active, Grafana API tells us RBAC is enabled
        (True, True, False, True),
    ],
)
@patch("apps.user_management.sync.GcomAPIClient")
@override_settings(LICENSE=settings.CLOUD_LICENSE_NAME)
@pytest.mark.django_db
def test_sync_organization_is_rbac_permissions_enabled_cloud(
    mock_gcom_client,
    make_organization,
    gcom_api_response,
    grafana_api_response,
    org_initial_value,
    org_is_rbac_permissions_enabled_expected_value,
):
    stack_id = 5
    organization = make_organization(stack_id=stack_id, is_rbac_permissions_enabled=org_initial_value)
    mock_gcom_client.return_value.is_stack_active.return_value = gcom_api_response

    assert organization.is_rbac_permissions_enabled == org_initial_value

    with patched_grafana_api_client(organization, grafana_api_response) as mock_grafana_api_client:
        sync_organization(organization)

    organization.refresh_from_db()

    assert organization.is_rbac_permissions_enabled == org_is_rbac_permissions_enabled_expected_value

    mock_gcom_client.return_value.is_stack_active.assert_called_once_with(stack_id)

    if gcom_api_response:
        mock_grafana_api_client.return_value.is_rbac_enabled_for_organization.assert_called_once_with()


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
@pytest.mark.parametrize("is_deleted", [True, False])
def test_cleanup_organization_deleted(make_organization, is_deleted):
    organization = make_organization(gcom_token="TEST_GCOM_TOKEN")

    with patch("apps.grafana_plugin.helpers.client.GcomAPIClient.is_stack_deleted", return_value=is_deleted):
        cleanup_organization(organization.id)

    organization.refresh_from_db()
    assert (organization.deleted_at is not None) == is_deleted


@pytest.mark.django_db
def test_organization_not_deleted(make_organization):
    organization = make_organization(gcom_token="TEST_GCOM_TOKEN")

    with patch("apps.grafana_plugin.helpers.client.GcomAPIClient.is_stack_deleted") as mock_method:
        exception_message = "Test Exception"
        mock_method.side_effect = Exception(exception_message)
        with pytest.raises(Exception) as e:
            cleanup_organization(organization.id)
        assert str(e.value) == exception_message

    organization.refresh_from_db()
    assert organization.deleted_at is None


@pytest.mark.django_db
@pytest.mark.parametrize("task_lock_acquired", [True, False])
@patch("apps.user_management.sync.task_lock")
@patch("apps.user_management.sync.uuid.uuid4", return_value="random")
def test_sync_organization_lock(
    _mock_uuid4,
    mock_task_lock,
    make_organization,
    task_lock_acquired,
):
    organization = make_organization()

    lock_cache_key = f"sync-organization-lock-{organization.id}"
    mock_task_lock.return_value.__enter__.return_value = task_lock_acquired

    with patched_grafana_api_client(organization) as mock_grafana_api_client:
        sync_organization(organization)

    mock_task_lock.assert_called_once_with(lock_cache_key, "random")

    if task_lock_acquired:
        mock_grafana_api_client.assert_called_once()
    else:
        # task lock could not be acquired
        mock_grafana_api_client.assert_not_called()


@dataclass
class TestSyncGrafanaLabelsPluginParams:
    __test__ = False

    response: tuple
    expected_result: bool


@pytest.mark.django_db
@pytest.mark.parametrize(
    "test_params",
    [
        TestSyncGrafanaLabelsPluginParams(({"enabled": True, "jsonData": {}}, None), True),
        TestSyncGrafanaLabelsPluginParams(({"enabled": True}, None), True),
        TestSyncGrafanaLabelsPluginParams(({"enabled": False}, None), False),
    ],
)
@pytest.mark.django_db
def test_sync_grafana_labels_plugin(make_organization, test_params: TestSyncGrafanaLabelsPluginParams):
    organization = make_organization()
    organization.is_grafana_labels_enabled = False  # by default in tests it's true, so setting to false

    with patch.object(
        GrafanaAPIClient,
        "get_grafana_labels_plugin_settings",
        return_value=test_params.response,
    ):
        grafana_api_client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
        _sync_grafana_labels_plugin(organization, grafana_api_client)
    assert organization.is_grafana_labels_enabled is test_params.expected_result


@dataclass
class TestSyncGrafanaIncidentParams:
    __test__ = False

    response: tuple
    expected_flag: bool
    expected_url: Optional[str]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "test_params",
    [
        TestSyncGrafanaIncidentParams(
            ({"enabled": True, "jsonData": {"backendUrl": MOCK_GRAFANA_INCIDENT_BACKEND_URL}}, None),
            True,
            MOCK_GRAFANA_INCIDENT_BACKEND_URL,
        ),
        TestSyncGrafanaIncidentParams(({"enabled": True}, None), True, None),
        TestSyncGrafanaIncidentParams(({"enabled": True, "jsonData": None}, None), True, None),
        # missing jsonData (sometimes this is what we get back from the Grafana API)
        TestSyncGrafanaIncidentParams(({"enabled": False}, None), False, None),  # plugin is disabled for some reason
    ],
)
@pytest.mark.django_db
def test_sync_grafana_incident_plugin(make_organization, test_params: TestSyncGrafanaIncidentParams):
    organization = make_organization()
    with patch.object(
        GrafanaAPIClient,
        "get_grafana_incident_plugin_settings",
        return_value=test_params.response,
    ):
        grafana_api_client = GrafanaAPIClient(api_url=organization.grafana_url, api_token=organization.api_token)
        _sync_grafana_incident_plugin(organization, grafana_api_client)
    assert organization.is_grafana_incident_enabled is test_params.expected_flag
    assert organization.grafana_incident_backend_url is test_params.expected_url
