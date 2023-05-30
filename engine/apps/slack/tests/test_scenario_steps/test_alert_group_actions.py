import json
from unittest.mock import patch

import pytest

from apps.slack.models import SlackMessage
from apps.slack.scenarios.scenario_step import ScenarioStep
from apps.slack.scenarios.step_mixins import AlertGroupActionsMixin
from apps.slack.slack_client import SlackClientWithErrorHandling


class TestScenario(AlertGroupActionsMixin, ScenarioStep):
    pass


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
    ScenarioStep.get_step("resolution_note", "AddToResolutionNoteStep"),
]


@pytest.mark.parametrize("step_class", ALERT_GROUP_ACTIONS_STEPS)
@patch.object(
    SlackClientWithErrorHandling,
    "api_call",
    return_value={"ok": True},
)
@pytest.mark.django_db
def test_alert_group_actions_slack_message_not_in_db(
    mock_slack_api_call, step_class, make_organization_and_user_with_slack_identities
):
    organization, _, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    payload = {
        "message_ts": "RANDOM_MESSAGE_TS",
        "channel": {"id": "RANDOM_CHANNEL_ID"},
    }

    step = step_class(organization=organization, slack_team_identity=slack_team_identity)

    with pytest.raises(SlackMessage.DoesNotExist):  # TODO: change this
        step.process_scenario(slack_user_identity, slack_team_identity, payload)


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
        ]
    }

    step = TestScenario(organization=organization, user=user, slack_team_identity=slack_team_identity)
    result = step.get_alert_group(slack_team_identity, payload)

    assert alert_group == result


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
        ]
    }

    step = TestScenario(organization=organization, user=user, slack_team_identity=slack_team_identity)
    result = step.get_alert_group(slack_team_identity, payload)

    assert alert_group == result


@pytest.mark.django_db
def test_get_alert_group_deprecated(
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
