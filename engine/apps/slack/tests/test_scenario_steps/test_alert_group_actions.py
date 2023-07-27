import json
from unittest.mock import patch

import pytest

from apps.api.permissions import LegacyAccessControlRole
from apps.slack.scenarios.scenario_step import ScenarioStep
from apps.slack.scenarios.step_mixins import AlertGroupActionsMixin


class TestScenario(AlertGroupActionsMixin, ScenarioStep):
    """
    set a __test__ = False attribute in classes that pytest should ignore otherwise we end up getting the following:
    PytestCollectionWarning: cannot collect test class 'TestScenario' because it has a __init__ constructor
    """

    __test__ = False

    pass


# List of steps to be tested for alert group actions (getting alert group from Slack payload + user permissions check)
ALERT_GROUP_ACTIONS_STEPS = [
    # Acknowledge / Unacknowledge buttons
    ScenarioStep.get_step("distribute_alerts", "AcknowledgeGroupStep"),
    ScenarioStep.get_step("distribute_alerts", "UnAcknowledgeGroupStep"),
    # Resolve / Unresolve buttons
    ScenarioStep.get_step("distribute_alerts", "ResolveGroupStep"),
    ScenarioStep.get_step("distribute_alerts", "UnResolveGroupStep"),
    # Invite / Stop inviting buttons
    ScenarioStep.get_step("distribute_alerts", "InviteOtherPersonToIncident"),
    ScenarioStep.get_step("distribute_alerts", "StopInvitationProcess"),
    # Silence / Unsilence buttons
    ScenarioStep.get_step("distribute_alerts", "SilenceGroupStep"),
    ScenarioStep.get_step("distribute_alerts", "UnSilenceGroupStep"),
    # Attach / Unattach buttons
    ScenarioStep.get_step("distribute_alerts", "SelectAttachGroupStep"),
    ScenarioStep.get_step("distribute_alerts", "UnAttachGroupStep"),
    # Format alert button
    ScenarioStep.get_step("alertgroup_appearance", "OpenAlertAppearanceDialogStep"),
    # Add resolution notes button
    ScenarioStep.get_step("resolution_note", "ResolutionNoteModalStep"),
]


# Constants to simplify parametrized tests
ORGANIZATION_ID = 42
ALERT_GROUP_ID = 24
SLACK_MESSAGE_TS = "RANDOM_MESSAGE_TS"
SLACK_CHANNEL_ID = "RANDOM_CHANNEL_ID"
USER_ID = 56
INVITATION_ID = 78


def _get_payload(action_type="button", **kwargs):
    """
    Utility function to generate payload to be used by scenario steps.
    """
    if action_type == "button":
        return {
            "actions": [
                {
                    "type": "button",
                    "value": json.dumps(
                        {"organization_id": ORGANIZATION_ID, "alert_group_pk": ALERT_GROUP_ID, **kwargs}
                    ),
                }
            ],
        }
    elif action_type == "static_select":
        return {
            "actions": [
                {
                    "type": "static_select",
                    "selected_option": {
                        "value": json.dumps(
                            {"organization_id": ORGANIZATION_ID, "alert_group_pk": ALERT_GROUP_ID, **kwargs}
                        )
                    },
                }
            ],
        }


@pytest.mark.parametrize("step_class", ALERT_GROUP_ACTIONS_STEPS)
@pytest.mark.django_db
def test_alert_group_actions_unauthorized(
    step_class, make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities(
        role=LegacyAccessControlRole.VIEWER
    )

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    payload = {
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk, "alert_group_pk": alert_group.pk}),
            }
        ],
        "channel": {"id": "RANDOM_CHANNEL_ID"},
        "message": {"ts": "RANDOM_MESSAGE_TS"},
        "trigger_id": "RANDOM_TRIGGER_ID",
    }

    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)

    with patch.object(step, "open_unauthorized_warning") as mock_open_unauthorized_warning:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    mock_open_unauthorized_warning.assert_called_once()


@pytest.mark.django_db
def test_get_alert_group_button(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group
):
    organization, user, slack_team_identity, _ = make_organization_and_user_with_slack_identities()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    payload = {
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk, "alert_group_pk": alert_group.pk}),
            }
        ],
        "channel": {"id": "RANDOM_CHANNEL_ID"},
        "message": {"ts": "RANDOM_MESSAGE_TS"},
    }

    step = TestScenario(organization=organization, user=user, slack_team_identity=slack_team_identity)
    result = step.get_alert_group(slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group == result  # check it's the right alert group
    assert alert_group.slack_message is not None  # check that orphaned Slack message is repaired


@pytest.mark.django_db
def test_get_alert_group_static_select(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group
):
    organization, user, slack_team_identity, _ = make_organization_and_user_with_slack_identities()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    payload = {
        "actions": [
            {
                "type": "static_select",
                "selected_option": {
                    "value": json.dumps({"organization_id": organization.pk, "alert_group_pk": alert_group.pk})
                },
            }
        ],
        "channel": {"id": "RANDOM_CHANNEL_ID"},
        "message": {"ts": "RANDOM_MESSAGE_TS"},
    }

    step = TestScenario(organization=organization, user=user, slack_team_identity=slack_team_identity)
    result = step.get_alert_group(slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group == result  # check it's the right alert group
    assert alert_group.slack_message is not None  # check that orphaned Slack message is repaired


@pytest.mark.django_db
def test_get_alert_group_from_message(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group
):
    organization, user, slack_team_identity, _ = make_organization_and_user_with_slack_identities()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    payload = {
        "actions": [
            {
                "type": "button",
                "value": "no alert_group_pk",
            }
        ],
        "message": {
            "ts": "RANDOM_MESSAGE_TS",
            "attachments": [{"blocks": [{"elements": [{"value": json.dumps({"alert_group_pk": alert_group.pk})}]}]}],
        },
        "channel": {"id": "RANDOM_CHANNEL_ID"},
    }

    step = TestScenario(organization=organization, user=user, slack_team_identity=slack_team_identity)
    result = step.get_alert_group(slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group == result  # check it's the right alert group
    assert alert_group.slack_message is not None  # check that orphaned Slack message is repaired


@pytest.mark.django_db
def test_get_alert_group_from_slack_message_in_db(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, _ = make_organization_and_user_with_slack_identities()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id)

    payload = {
        "message_ts": slack_message.slack_id,
        "channel": {"id": slack_channel.slack_id},
        "actions": [{"type": "button", "value": "RANDOM_VALUE"}],
    }

    step = TestScenario(organization=organization, user=user, slack_team_identity=slack_team_identity)
    result = step.get_alert_group(slack_team_identity, payload)

    assert alert_group == result


@pytest.mark.parametrize(
    "payload",
    [
        _get_payload(),
        # deprecated payload shape, but still supported to handle older Slack messages
        {
            "message_ts": SLACK_MESSAGE_TS,
            "channel": {"id": SLACK_CHANNEL_ID},
            "actions": [{"type": "button", "value": json.dumps({"organization_id": ORGANIZATION_ID})}],
        },
    ],
)
@pytest.mark.django_db
def test_step_acknowledge(
    payload,
    make_organization,
    make_slack_team_identity,
    make_user,
    make_slack_user_identity,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    slack_team_identity = make_slack_team_identity()
    slack_user_identity = make_slack_user_identity(slack_team_identity=slack_team_identity)
    slack_channel = make_slack_channel(slack_team_identity, slack_id=SLACK_CHANNEL_ID)

    organization = make_organization(pk=ORGANIZATION_ID, slack_team_identity=slack_team_identity)
    user = make_user(organization=organization, slack_user_identity=slack_user_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, acknowledged=False, pk=ALERT_GROUP_ID)
    make_alert(alert_group, raw_request_data={})

    slack_message = make_slack_message(
        alert_group=alert_group, channel_id=slack_channel.slack_id, slack_id=SLACK_MESSAGE_TS
    )
    slack_message.get_alert_group()  # fix FKs

    step_class = ScenarioStep.get_step("distribute_alerts", "AcknowledgeGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.acknowledged is True


@pytest.mark.parametrize(
    "payload",
    [
        _get_payload(),
        # deprecated payload shape, but still supported to handle older Slack messages
        {
            "message_ts": SLACK_MESSAGE_TS,
            "channel": {"id": SLACK_CHANNEL_ID},
            "actions": [{"type": "button", "value": json.dumps({"organization_id": ORGANIZATION_ID})}],
        },
    ],
)
@pytest.mark.django_db
def test_step_unacknowledge(
    payload,
    make_organization,
    make_slack_team_identity,
    make_user,
    make_slack_user_identity,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    slack_team_identity = make_slack_team_identity()
    slack_user_identity = make_slack_user_identity(slack_team_identity=slack_team_identity)
    slack_channel = make_slack_channel(slack_team_identity, slack_id=SLACK_CHANNEL_ID)

    organization = make_organization(pk=ORGANIZATION_ID, slack_team_identity=slack_team_identity)
    user = make_user(organization=organization, slack_user_identity=slack_user_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, acknowledged=True, pk=ALERT_GROUP_ID)
    make_alert(alert_group, raw_request_data={})

    slack_message = make_slack_message(
        alert_group=alert_group, channel_id=slack_channel.slack_id, slack_id=SLACK_MESSAGE_TS
    )
    slack_message.get_alert_group()  # fix FKs

    step_class = ScenarioStep.get_step("distribute_alerts", "UnAcknowledgeGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.acknowledged is False


@pytest.mark.parametrize(
    "payload",
    [
        _get_payload(),
        # deprecated payload shape, but still supported to handle older Slack messages
        {
            "message_ts": SLACK_MESSAGE_TS,
            "channel": {"id": SLACK_CHANNEL_ID},
            "actions": [{"type": "button", "value": json.dumps({"organization_id": ORGANIZATION_ID})}],
        },
    ],
)
@pytest.mark.django_db
def test_step_resolve(
    payload,
    make_organization,
    make_slack_team_identity,
    make_user,
    make_slack_user_identity,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    slack_team_identity = make_slack_team_identity()
    slack_user_identity = make_slack_user_identity(slack_team_identity=slack_team_identity)
    slack_channel = make_slack_channel(slack_team_identity, slack_id=SLACK_CHANNEL_ID)

    organization = make_organization(pk=ORGANIZATION_ID, slack_team_identity=slack_team_identity)
    user = make_user(organization=organization, slack_user_identity=slack_user_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, resolved=False, pk=ALERT_GROUP_ID)
    make_alert(alert_group, raw_request_data={})

    slack_message = make_slack_message(
        alert_group=alert_group, channel_id=slack_channel.slack_id, slack_id=SLACK_MESSAGE_TS
    )
    slack_message.get_alert_group()  # fix FKs

    step_class = ScenarioStep.get_step("distribute_alerts", "ResolveGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.resolved is True


@pytest.mark.parametrize(
    "payload",
    [
        _get_payload(),
        # deprecated payload shape, but still supported to handle older Slack messages
        {
            "message_ts": SLACK_MESSAGE_TS,
            "channel": {"id": SLACK_CHANNEL_ID},
            "actions": [{"type": "button", "value": json.dumps({"organization_id": ORGANIZATION_ID})}],
        },
    ],
)
@pytest.mark.django_db
def test_step_unresolve(
    payload,
    make_organization,
    make_slack_team_identity,
    make_user,
    make_slack_user_identity,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    slack_team_identity = make_slack_team_identity()
    slack_user_identity = make_slack_user_identity(slack_team_identity=slack_team_identity)
    slack_channel = make_slack_channel(slack_team_identity, slack_id=SLACK_CHANNEL_ID)

    organization = make_organization(pk=ORGANIZATION_ID, slack_team_identity=slack_team_identity)
    user = make_user(organization=organization, slack_user_identity=slack_user_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, resolved=True, pk=ALERT_GROUP_ID)
    make_alert(alert_group, raw_request_data={})

    slack_message = make_slack_message(
        alert_group=alert_group, channel_id=slack_channel.slack_id, slack_id=SLACK_MESSAGE_TS
    )
    slack_message.get_alert_group()  # fix FKs

    step_class = ScenarioStep.get_step("distribute_alerts", "UnResolveGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.resolved is False


@pytest.mark.parametrize(
    "payload",
    [
        # Usual data such as alert_group_pk is not passed to InviteOtherPersonToIncident, so it doesn't increase
        # payload size too much.
        {
            "message_ts": SLACK_MESSAGE_TS,
            "channel": {"id": SLACK_CHANNEL_ID},
            "actions": [
                {
                    "type": "static_select",
                    "selected_option": {"value": json.dumps({"user_id": USER_ID})},
                }
            ],
        },
    ],
)
@pytest.mark.django_db
def test_step_invite(
    payload,
    make_organization,
    make_slack_team_identity,
    make_user,
    make_slack_user_identity,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    slack_team_identity = make_slack_team_identity()
    slack_user_identity = make_slack_user_identity(slack_team_identity=slack_team_identity)
    slack_channel = make_slack_channel(slack_team_identity, slack_id=SLACK_CHANNEL_ID)

    organization = make_organization(pk=ORGANIZATION_ID, slack_team_identity=slack_team_identity)
    user = make_user(organization=organization, slack_user_identity=slack_user_identity)
    second_user = make_user(organization=organization, pk=USER_ID)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, resolved=True, pk=ALERT_GROUP_ID)
    make_alert(alert_group, raw_request_data={})

    slack_message = make_slack_message(
        alert_group=alert_group, channel_id=slack_channel.slack_id, slack_id=SLACK_MESSAGE_TS
    )
    slack_message.get_alert_group()  # fix FKs

    step_class = ScenarioStep.get_step("distribute_alerts", "InviteOtherPersonToIncident")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.invitations.count() == 1

    invitation = alert_group.invitations.first()
    assert invitation.author == user
    assert invitation.invitee == second_user


@pytest.mark.parametrize(
    "payload",
    [
        _get_payload(invitation_id=INVITATION_ID),
        # deprecated payload shape, but still supported to handle older Slack messages
        {
            "message_ts": SLACK_MESSAGE_TS,
            "channel": {"id": SLACK_CHANNEL_ID},
            "actions": [
                {
                    "name": f"StopInvitationProcess_{INVITATION_ID}",
                    "type": "button",
                    "value": json.dumps({"organization_id": ORGANIZATION_ID}),
                }
            ],
        },
    ],
)
@pytest.mark.django_db
def test_step_stop_invite(
    payload,
    make_organization,
    make_slack_team_identity,
    make_user,
    make_slack_user_identity,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
    make_invitation,
):
    slack_team_identity = make_slack_team_identity()
    slack_user_identity = make_slack_user_identity(slack_team_identity=slack_team_identity)
    slack_channel = make_slack_channel(slack_team_identity, slack_id=SLACK_CHANNEL_ID)

    organization = make_organization(pk=ORGANIZATION_ID, slack_team_identity=slack_team_identity)
    user = make_user(organization=organization, slack_user_identity=slack_user_identity)
    second_user = make_user(organization=organization, pk=USER_ID)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, resolved=True, pk=ALERT_GROUP_ID)
    make_alert(alert_group, raw_request_data={})

    slack_message = make_slack_message(
        alert_group=alert_group, channel_id=slack_channel.slack_id, slack_id=SLACK_MESSAGE_TS
    )
    slack_message.get_alert_group()  # fix FKs

    invitation = make_invitation(alert_group, user, second_user, pk=INVITATION_ID)

    step_class = ScenarioStep.get_step("distribute_alerts", "StopInvitationProcess")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    invitation.refresh_from_db()
    assert invitation.is_active is False


@pytest.mark.parametrize(
    "payload",
    [
        _get_payload(action_type="static_select", delay=1800),
        # deprecated payload shape, but still supported to handle older Slack messages
        {
            "message_ts": SLACK_MESSAGE_TS,
            "channel": {"id": SLACK_CHANNEL_ID},
            "actions": [
                {
                    "type": "static_select",
                    "selected_option": {"value": "1800"},
                }
            ],
        },
    ],
)
@pytest.mark.django_db
def test_step_silence(
    payload,
    make_organization,
    make_slack_team_identity,
    make_user,
    make_slack_user_identity,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    slack_team_identity = make_slack_team_identity()
    slack_user_identity = make_slack_user_identity(slack_team_identity=slack_team_identity)
    slack_channel = make_slack_channel(slack_team_identity, slack_id=SLACK_CHANNEL_ID)

    organization = make_organization(pk=ORGANIZATION_ID, slack_team_identity=slack_team_identity)
    user = make_user(organization=organization, slack_user_identity=slack_user_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, silenced=False, pk=ALERT_GROUP_ID)
    make_alert(alert_group, raw_request_data={})

    slack_message = make_slack_message(
        alert_group=alert_group, channel_id=slack_channel.slack_id, slack_id=SLACK_MESSAGE_TS
    )
    slack_message.get_alert_group()  # fix FKs

    step_class = ScenarioStep.get_step("distribute_alerts", "SilenceGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.silenced is True


@pytest.mark.parametrize(
    "payload",
    [
        _get_payload(action_type="static_select", delay=1800),
        # deprecated payload shape, but still supported to handle older Slack messages
        {
            "message_ts": SLACK_MESSAGE_TS,
            "channel": {"id": SLACK_CHANNEL_ID},
            "actions": [
                {
                    "type": "button",
                    "value": json.dumps({"organization_id": ORGANIZATION_ID}),
                }
            ],
        },
    ],
)
@pytest.mark.django_db
def test_step_unsilence(
    payload,
    make_organization,
    make_slack_team_identity,
    make_user,
    make_slack_user_identity,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    slack_team_identity = make_slack_team_identity()
    slack_user_identity = make_slack_user_identity(slack_team_identity=slack_team_identity)
    slack_channel = make_slack_channel(slack_team_identity, slack_id=SLACK_CHANNEL_ID)

    organization = make_organization(pk=ORGANIZATION_ID, slack_team_identity=slack_team_identity)
    user = make_user(organization=organization, slack_user_identity=slack_user_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, silenced=True, pk=ALERT_GROUP_ID)
    make_alert(alert_group, raw_request_data={})

    slack_message = make_slack_message(
        alert_group=alert_group, channel_id=slack_channel.slack_id, slack_id=SLACK_MESSAGE_TS
    )
    slack_message.get_alert_group()  # fix FKs

    step_class = ScenarioStep.get_step("distribute_alerts", "UnSilenceGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.silenced is False


@pytest.mark.parametrize(
    "payload",
    [
        _get_payload() | {"trigger_id": "RANDOM_TRIGGER_ID"},
    ],
)
@pytest.mark.django_db
def test_step_select_attach(
    payload,
    make_organization,
    make_slack_team_identity,
    make_user,
    make_slack_user_identity,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    slack_team_identity = make_slack_team_identity()
    slack_user_identity = make_slack_user_identity(slack_team_identity=slack_team_identity)
    slack_channel = make_slack_channel(slack_team_identity, slack_id=SLACK_CHANNEL_ID)

    organization = make_organization(pk=ORGANIZATION_ID, slack_team_identity=slack_team_identity)
    user = make_user(organization=organization, slack_user_identity=slack_user_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, pk=ALERT_GROUP_ID)
    make_alert(alert_group, raw_request_data={})

    slack_message = make_slack_message(
        alert_group=alert_group, channel_id=slack_channel.slack_id, slack_id=SLACK_MESSAGE_TS
    )
    slack_message.get_alert_group()  # fix FKs

    step_class = ScenarioStep.get_step("distribute_alerts", "SelectAttachGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)

    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.open",)


@pytest.mark.parametrize(
    "payload",
    [
        _get_payload() | {"trigger_id": "RANDOM_TRIGGER_ID"},
        # deprecated payload shape, but still supported to handle older Slack messages
        {
            "message_ts": SLACK_MESSAGE_TS,
            "channel": {"id": SLACK_CHANNEL_ID},
            "trigger_id": "RANDOM_TRIGGER_ID",
            "actions": [
                {
                    "type": "button",
                    "value": json.dumps({"organization_id": ORGANIZATION_ID}),
                }
            ],
        },
    ],
)
@pytest.mark.django_db
def test_step_unattach(
    payload,
    make_organization,
    make_slack_team_identity,
    make_user,
    make_slack_user_identity,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    slack_team_identity = make_slack_team_identity()
    slack_user_identity = make_slack_user_identity(slack_team_identity=slack_team_identity)
    slack_channel = make_slack_channel(slack_team_identity, slack_id=SLACK_CHANNEL_ID)

    organization = make_organization(pk=ORGANIZATION_ID, slack_team_identity=slack_team_identity)
    user = make_user(organization=organization, slack_user_identity=slack_user_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    root_alert_group = make_alert_group(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, root_alert_group=root_alert_group, pk=ALERT_GROUP_ID)
    make_alert(alert_group, raw_request_data={})

    slack_message = make_slack_message(
        alert_group=alert_group, channel_id=slack_channel.slack_id, slack_id=SLACK_MESSAGE_TS
    )
    slack_message.get_alert_group()  # fix FKs

    step_class = ScenarioStep.get_step("distribute_alerts", "UnAttachGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.root_alert_group is None


@pytest.mark.parametrize(
    "payload",
    [
        _get_payload() | {"message_ts": "RANDOM_TS", "trigger_id": "RANDOM_TRIGGER_ID"},
        # deprecated payload shape, but still supported to handle older Slack messages
        {
            "message_ts": SLACK_MESSAGE_TS,
            "channel": {"id": SLACK_CHANNEL_ID},
            "trigger_id": "RANDOM_TRIGGER_ID",
            "actions": [
                {
                    "type": "button",
                    "value": json.dumps({"organization_id": ORGANIZATION_ID, "alert_group_pk": str(ALERT_GROUP_ID)}),
                }
            ],
        },
    ],
)
@pytest.mark.django_db
def test_step_format_alert(
    payload,
    make_organization,
    make_slack_team_identity,
    make_user,
    make_slack_user_identity,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    slack_team_identity = make_slack_team_identity()
    slack_user_identity = make_slack_user_identity(slack_team_identity=slack_team_identity)
    slack_channel = make_slack_channel(slack_team_identity, slack_id=SLACK_CHANNEL_ID)

    organization = make_organization(pk=ORGANIZATION_ID, slack_team_identity=slack_team_identity)
    user = make_user(organization=organization, slack_user_identity=slack_user_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, pk=ALERT_GROUP_ID)
    make_alert(alert_group, raw_request_data={})

    slack_message = make_slack_message(
        alert_group=alert_group, channel_id=slack_channel.slack_id, slack_id=SLACK_MESSAGE_TS
    )
    slack_message.get_alert_group()  # fix FKs

    step_class = ScenarioStep.get_step("alertgroup_appearance", "OpenAlertAppearanceDialogStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)

    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.open",)


@pytest.mark.django_db
def test_step_resolution_note(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    payload = {
        "trigger_id": "RANDOM_TRIGGER_ID",
        "actions": [
            {
                "type": "button",
                "value": json.dumps(
                    {
                        "organization_id": organization.pk,
                        "alert_group_pk": alert_group.pk,
                        "resolution_note_window_action": "edit",
                    }
                ),
            }
        ],
        "channel": {"id": "RANDOM_CHANNEL_ID"},
        "message": {"ts": "RANDOM_MESSAGE_TS"},
    }

    step_class = ScenarioStep.get_step("resolution_note", "ResolutionNoteModalStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)

    with patch.object(step._slack_client, "api_call") as mock_slack_api_call:
        step.process_scenario(slack_user_identity, slack_team_identity, payload)

    assert mock_slack_api_call.call_args.args == ("views.open",)
