from unittest.mock import PropertyMock, patch

import pytest

from apps.schedules.models.on_call_schedule import OnCallScheduleQuerySet, OnCallScheduleWeb
from apps.slack.client import SlackClient
from apps.slack.errors import (
    SlackAPIError,
    SlackAPIInvalidUsersError,
    SlackAPITokenError,
    SlackAPIUsergroupNotFoundError,
)
from apps.slack.models import SlackUserGroup
from apps.slack.tasks import (
    populate_slack_usergroups_for_team,
    start_update_slack_user_group_for_schedules,
    update_slack_user_group_for_schedules,
)
from apps.slack.tests.conftest import build_slack_response
from apps.user_management.models import Organization


@pytest.mark.django_db
def test_update_members(make_organization_with_slack_team_identity, make_slack_user_group):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    user_group = make_slack_user_group(slack_team_identity)

    slack_ids = ["slack_id_1", "slack_id_2"]
    with patch("apps.slack.client.SlackClient.usergroups_users_update") as mock_update:
        user_group.update_members(slack_ids)

    mock_update.assert_called_once()
    assert user_group.members == slack_ids


@pytest.mark.django_db
@pytest.mark.parametrize("exception", [SlackAPITokenError, SlackAPIUsergroupNotFoundError, SlackAPIInvalidUsersError])
def test_slack_user_group_update_errors(
    make_organization_with_slack_team_identity,
    make_slack_user_group,
    exception,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    user_group = make_slack_user_group(slack_team_identity=slack_team_identity)

    slack_ids = ["slack_id_1", "slack_id_2"]
    with patch("apps.slack.client.SlackClient.usergroups_users_update", side_effect=exception("Error")) as mock_update:
        user_group.update_members(slack_ids)

    mock_update.assert_called_once()
    assert user_group.members is None


@pytest.mark.django_db
def test_slack_user_group_update_errors_raise(
    make_organization_with_slack_team_identity,
    make_slack_user_group,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    user_group = make_slack_user_group(slack_team_identity=slack_team_identity)

    slack_ids = ["slack_id_1", "slack_id_2"]
    with patch(
        "apps.slack.client.SlackClient.usergroups_users_update", side_effect=SlackAPIError("Error")
    ) as mock_update:
        with pytest.raises(SlackAPIError):
            user_group.update_members(slack_ids)

    mock_update.assert_called_once()


@pytest.mark.django_db
def test_oncall_slack_user_identities(
    make_organization_with_slack_team_identity,
    make_slack_user_group,
    make_user_with_slack_user_identity,
    make_user_for_organization,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    user_group = make_slack_user_group(slack_team_identity)

    user_1, slack_user_identity_1 = make_user_with_slack_user_identity(
        slack_team_identity, organization, slack_id="user_1"
    )
    user_2, slack_user_identity_2 = make_user_with_slack_user_identity(
        slack_team_identity, organization, slack_id="user_2"
    )
    user_3 = make_user_for_organization(organization)

    with patch.object(OnCallScheduleQuerySet, "get_oncall_users", return_value={"schedule1": [user_1, user_2, user_3]}):
        assert set(user_group.oncall_slack_user_identities) == {slack_user_identity_1, slack_user_identity_2}


@pytest.mark.django_db
def test_update_oncall_members(
    make_organization_with_slack_team_identity,
    make_slack_user_group,
    make_user_with_slack_user_identity,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    user_group = make_slack_user_group(slack_team_identity)

    user_1, slack_user_identity_1 = make_user_with_slack_user_identity(
        slack_team_identity, organization, slack_id="slack_id_1"
    )
    user_2, slack_user_identity_2 = make_user_with_slack_user_identity(
        slack_team_identity, organization, slack_id="slack_id_2"
    )

    with patch.object(
        SlackUserGroup, "oncall_slack_user_identities", new_callable=PropertyMock
    ) as oncall_slack_user_identities_mock:
        oncall_slack_user_identities_mock.return_value = [slack_user_identity_1, slack_user_identity_2]

        with patch.object(SlackUserGroup, "update_members") as update_members_mock:
            user_group.update_oncall_members()
            update_members_mock.assert_called()


@pytest.mark.django_db
def test_start_update_slack_user_group_for_schedules_organization_deleted(
    make_organization_with_slack_team_identity, make_slack_user_group, make_schedule
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    user_group = make_slack_user_group(slack_team_identity)
    make_schedule(organization, schedule_class=OnCallScheduleWeb, user_group=user_group)

    # check user group is updated
    with patch.object(update_slack_user_group_for_schedules, "delay") as mock:
        start_update_slack_user_group_for_schedules()
        mock.assert_called_once_with(user_group_pk=user_group.pk)

    # soft delete the organization
    Organization.objects.filter(pk=organization.pk).delete()

    # check user group is not updated for deleted organization
    with patch.object(update_slack_user_group_for_schedules, "delay") as mock:
        start_update_slack_user_group_for_schedules()
        mock.assert_not_called()


@patch.object(
    SlackClient,
    "usergroups_users_list",
    return_value=build_slack_response({"ok": True, "users": ["test_user_1", "test_user_2"]}),
)
@patch.object(
    SlackClient,
    "usergroups_list",
    return_value=build_slack_response(
        {
            "ok": True,
            "usergroups": [{"id": "test_slack_id", "name": "test_name", "handle": "test_handle", "date_delete": 0}],
        }
    ),
)
@pytest.mark.django_db
def test_update_or_create_slack_usergroup_from_slack(
    mock_usergroups_list, mock_usergroups_users_list, make_organization_with_slack_team_identity
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    SlackUserGroup.update_or_create_slack_usergroup_from_slack("test_slack_id", slack_team_identity)

    usergroup = SlackUserGroup.objects.get()
    assert usergroup.name == "test_name"
    assert usergroup.handle == "test_handle"
    assert usergroup.members == ["test_user_1", "test_user_2"]
    assert usergroup.is_active


@patch.object(
    SlackClient,
    "usergroups_list",
    return_value=build_slack_response(
        {
            "ok": True,
            "usergroups": [{"id": "test_slack_id", "name": "test_name", "handle": "test_handle", "date_delete": 0}],
        }
    ),
)
@pytest.mark.django_db
def test_update_or_create_slack_usergroup_from_slack_group_not_found(
    mock_usergroups_list, make_organization_with_slack_team_identity
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    SlackUserGroup.update_or_create_slack_usergroup_from_slack("other_id", slack_team_identity)

    # no group is created, no error is raised
    assert SlackUserGroup.objects.count() == 0


@patch.object(
    SlackClient,
    "usergroups_users_list",
    return_value=build_slack_response({"ok": True, "users": ["test_user_1", "test_user_2"]}),
)
@patch.object(
    SlackClient,
    "usergroups_list",
    return_value=build_slack_response(
        {
            "ok": True,
            "usergroups": [{"id": "test_slack_id", "name": "test_name", "handle": "test_handle", "date_delete": 0}],
        }
    ),
)
@pytest.mark.django_db
def test_populate_slack_usergroups_for_team(
    mock_usergroups_list, mock_usergroups_users_list, make_organization_with_slack_team_identity
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    populate_slack_usergroups_for_team(slack_team_identity.pk)

    usergroup = SlackUserGroup.objects.get()
    assert usergroup.name == "test_name"
    assert usergroup.handle == "test_handle"
    assert usergroup.members == ["test_user_1", "test_user_2"]
    assert usergroup.is_active


@pytest.mark.django_db
def test_get_users_from_members_for_organization(
    make_organization_with_slack_team_identity,
    make_slack_user_group,
    make_user_with_slack_user_identity,
):
    organization, slack_team_identity = make_organization_with_slack_team_identity()

    user_1, slack_user_identity_1 = make_user_with_slack_user_identity(
        slack_team_identity, organization, slack_id="slack_id_1"
    )
    user_2, slack_user_identity_2 = make_user_with_slack_user_identity(
        slack_team_identity, organization, slack_id="slack_id_2"
    )
    user_group = make_slack_user_group(slack_team_identity)
    user_group.members = ["slack_id_1", "slack_id_2"]
    user_group.save(update_fields=["members"])

    users = user_group.get_users_from_members_for_organization(organization)
    assert set(users) == {user_1, user_2}
