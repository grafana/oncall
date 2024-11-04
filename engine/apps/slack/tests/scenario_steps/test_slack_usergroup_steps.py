import pytest

from apps.slack.models import SlackUserGroup
from apps.slack.scenarios.scenario_step import ScenarioStep


def get_user_group_event_payload(slack_team_identity, slack_user_identity):
    slack_team_id = slack_team_identity.slack_id
    slack_user_id = slack_user_identity.slack_id
    payload = {
        "team_id": slack_team_id,
        "event": {
            "type": "subteam_updated",
            "subteam": {
                "id": "S017H64MD5K",
                "team_id": slack_team_id,
                "is_usergroup": True,
                "is_subteam": True,
                "name": "Test User Group",
                "description": "",
                "handle": "test-user-group",
                "is_external": False,
                "date_create": 1595430081,
                "date_update": 1595913736,
                "date_delete": 0,
                "auto_type": None,
                "auto_provision": False,
                "enterprise_subteam_id": "",
                "created_by": slack_user_id,
                "updated_by": slack_user_id,
                "deleted_by": None,
                "prefs": {"channels": [], "groups": []},
                "users": [slack_user_id],
                "user_count": 1,
                "channel_count": 0,
            },
            "event_ts": "1595924845.008900",
        },
        "type": "event_callback",
        "event_id": "Ev017UPSP1AP",
        "event_time": 1595924845,
        "authed_users": ["W0188BV77AL"],
    }
    return payload


def get_user_group_members_changed_event_payload(slack_team_identity, slack_user_identity, user_group):
    slack_team_id = slack_team_identity.slack_id
    slack_user_id = slack_user_identity.slack_id
    slack_user_group_id = user_group.slack_id
    payload = {
        "team_id": slack_team_id,
        "event": {
            "type": "subteam_members_changed",
            "subteam_id": slack_user_group_id,
            "team_id": slack_team_id,
            "date_previous_update": 1446670362,
            "date_update": 1492906952,
            "added_users": [slack_user_id],
            "added_users_count": "3",
            "removed_users": user_group.members,
            "removed_users_count": "1",
            "event_ts": "1595924845.008900",
        },
        "type": "event_callback",
        "event_id": "Ev017UPSP1AP",
        "event_time": 1595924845,
        "authed_users": [slack_user_id],
    }
    return payload


@pytest.mark.django_db
def test_slack_user_group_event_step(
    make_organization_and_user_with_slack_identities,
    get_slack_team_and_slack_user,
):
    SlackUserGroupEventStep = ScenarioStep.get_step("slack_usergroup", "SlackUserGroupEventStep")

    organization, user, _, _ = make_organization_and_user_with_slack_identities()
    slack_team_identity, slack_user_identity = get_slack_team_and_slack_user(organization, user)
    step = SlackUserGroupEventStep(slack_team_identity)
    payload = get_user_group_event_payload(slack_team_identity, slack_user_identity)

    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    user_group = SlackUserGroup.objects.filter(slack_id=payload["event"]["subteam"]["id"]).first()

    assert user_group is not None
    assert user_group.slack_team_identity == slack_team_identity
    assert user_group.slack_id == payload["event"]["subteam"]["id"]
    assert user_group.name == payload["event"]["subteam"]["name"]
    assert user_group.handle == payload["event"]["subteam"]["handle"]
    assert user_group.members == payload["event"]["subteam"]["users"]
    assert user_group.members == [slack_user_identity.slack_id]
    assert user_group.is_active == int(payload["event"]["subteam"]["date_delete"] == 0)


@pytest.mark.django_db
def test_slack_user_group_members_changed_event_step(
    make_organization_and_user_with_slack_identities,
    make_slack_user_group,
):
    SlackUserGroupMembersChangedEventStep = ScenarioStep.get_step(
        "slack_usergroup", "SlackUserGroupMembersChangedEventStep"
    )

    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    step = SlackUserGroupMembersChangedEventStep(slack_team_identity)
    user_group_members = ["TESTUSER1", "TESTUSER2"]
    user_group = make_slack_user_group(slack_team_identity=slack_team_identity, members=user_group_members)
    assert user_group.members == user_group_members

    # this payload removes existing group members (user_group_members)
    # and adds slack_user_identity.slack_id as new member
    payload = get_user_group_members_changed_event_payload(slack_team_identity, slack_user_identity, user_group)

    step.process_scenario(slack_user_identity, slack_team_identity, payload)
    user_group.refresh_from_db()
    assert user_group.members == [slack_user_identity.slack_id]
