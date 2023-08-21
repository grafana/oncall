from unittest.mock import PropertyMock, patch

import pytest

from apps.schedules.models.on_call_schedule import OnCallScheduleQuerySet
from apps.slack.models import SlackUserGroup
from apps.slack.slack_client import SlackClientWithErrorHandling


@pytest.mark.django_db
def test_update_members(make_organization_with_slack_team_identity, make_slack_user_group):
    organization, slack_team_identity = make_organization_with_slack_team_identity()
    user_group = make_slack_user_group(slack_team_identity)

    slack_ids = ["slack_id_1", "slack_id_2"]

    with patch.object(SlackClientWithErrorHandling, "api_call") as mock:
        user_group.update_members(slack_ids)
        mock.assert_called()

    assert user_group.members == slack_ids


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
