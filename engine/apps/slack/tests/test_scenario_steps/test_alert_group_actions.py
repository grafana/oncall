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
    ScenarioStep.get_step("resolution_note", "ResolutionNoteModalStep"),
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
        "trigger_id": "RANDOM_TRIGGER_ID",
        "actions": [{"type": "button", "value": json.dumps({"organization_id": organization.pk})}],
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


@pytest.mark.django_db
def test_step_acknowledge(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    payload = {
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk, "alert_group_pk": alert_group.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "AcknowledgeGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.acknowledged is True


@pytest.mark.django_db
def test_step_acknowledge_deprecated(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id)

    payload = {
        "message_ts": slack_message.slack_id,
        "channel": {"id": slack_channel.slack_id},
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "AcknowledgeGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.acknowledged is True


@pytest.mark.django_db
def test_step_unacknowledge(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, acknowledged=True)
    make_alert(alert_group, raw_request_data={})

    payload = {
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk, "alert_group_pk": alert_group.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "UnAcknowledgeGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.acknowledged is False


@pytest.mark.django_db
def test_step_unacknowledge_deprecated(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, acknowledged=True)
    make_alert(alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id)

    payload = {
        "message_ts": slack_message.slack_id,
        "channel": {"id": slack_channel.slack_id},
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "UnAcknowledgeGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.acknowledged is False


@pytest.mark.django_db
def test_step_resolve(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    payload = {
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk, "alert_group_pk": alert_group.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "ResolveGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.resolved is True


@pytest.mark.django_db
def test_step_resolve_deprecated(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id)

    payload = {
        "message_ts": slack_message.slack_id,
        "channel": {"id": slack_channel.slack_id},
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "ResolveGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.resolved is True


@pytest.mark.django_db
def test_step_unresolve(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, resolved=True)
    make_alert(alert_group, raw_request_data={})

    payload = {
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk, "alert_group_pk": alert_group.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "UnResolveGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.resolved is False


@pytest.mark.django_db
def test_step_unresolve_deprecated(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, resolved=True)
    make_alert(alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id)

    payload = {
        "message_ts": slack_message.slack_id,
        "channel": {"id": slack_channel.slack_id},
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "UnResolveGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.resolved is False


@pytest.mark.django_db
def test_step_invite(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    second_user = make_user(organization=organization)
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    payload = {
        "actions": [
            {
                "type": "static_select",
                "selected_option": {
                    "value": json.dumps(
                        {
                            "organization_id": organization.pk,
                            "alert_group_pk": alert_group.pk,
                            "user_id": second_user.pk,
                        }
                    )
                },
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "InviteOtherPersonToIncident")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.invitations.count() == 1

    invitation = alert_group.invitations.first()
    assert invitation.author == user
    assert invitation.invitee == second_user


@pytest.mark.django_db
def test_step_invite_deprecated(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    second_user = make_user(organization=organization)
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id)

    payload = {
        "message_ts": slack_message.slack_id,
        "channel": {"id": slack_channel.slack_id},
        "actions": [
            {
                "type": "static_select",
                "selected_option": {"value": json.dumps({"user_id": second_user.pk})},
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "InviteOtherPersonToIncident")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.invitations.count() == 1

    invitation = alert_group.invitations.first()
    assert invitation.author == user
    assert invitation.invitee == second_user


@pytest.mark.django_db
def test_step_stop_invite(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_invitation,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    second_user = make_user(organization=organization)
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    invitation = make_invitation(alert_group, user, second_user)

    payload = {
        "actions": [
            {
                "type": "button",
                "value": json.dumps(
                    {
                        "organization_id": organization.pk,
                        "alert_group_pk": alert_group.pk,
                        "invitation_id": invitation.pk,
                    }
                ),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "StopInvitationProcess")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    invitation.refresh_from_db()
    assert invitation.is_active is False


@pytest.mark.django_db
def test_step_stop_invite_deprecated(
    make_organization_and_user_with_slack_identities,
    make_user,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
    make_invitation,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    second_user = make_user(organization=organization)
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id)

    invitation = make_invitation(alert_group, user, second_user)

    payload = {
        "message_ts": slack_message.slack_id,
        "channel": {"id": slack_channel.slack_id},
        "actions": [
            {
                "name": f"StopInvitationProcess_{invitation.pk}",
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "StopInvitationProcess")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    invitation.refresh_from_db()
    assert invitation.is_active is False


@pytest.mark.django_db
def test_step_silence(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, silenced=False)
    make_alert(alert_group, raw_request_data={})

    payload = {
        "actions": [
            {
                "type": "static_select",
                "selected_option": {
                    "value": json.dumps(
                        {"organization_id": organization.pk, "alert_group_pk": alert_group.pk, "delay": 1800}
                    )
                },
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "SilenceGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.silenced is True


@pytest.mark.django_db
def test_step_silence_deprecated(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, silenced=False)
    make_alert(alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id)

    payload = {
        "message_ts": slack_message.slack_id,
        "channel": {"id": slack_channel.slack_id},
        "actions": [
            {
                "type": "static_select",
                "selected_option": {"value": "1800"},
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "SilenceGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.silenced is True


@pytest.mark.django_db
def test_step_unsilence(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, silenced=True)
    make_alert(alert_group, raw_request_data={})

    payload = {
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk, "alert_group_pk": alert_group.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "UnSilenceGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.silenced is False


@pytest.mark.django_db
def test_step_unsilence_deprecated(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel, silenced=True)
    make_alert(alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id)

    payload = {
        "message_ts": slack_message.slack_id,
        "channel": {"id": slack_channel.slack_id},
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "UnSilenceGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.silenced is False


@pytest.mark.django_db
def test_step_select_attach(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    payload = {
        "trigger_id": "RANDOM_TRIGGER_ID",
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk, "alert_group_pk": alert_group.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "SelectAttachGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    # TODO: assert


@pytest.mark.django_db
def test_step_select_attach_deprecated(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id)

    payload = {
        "message_ts": slack_message.slack_id,
        "channel": {"id": slack_channel.slack_id},
        "trigger_id": "RANDOM_TRIGGER_ID",
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "SelectAttachGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    # TODO: assert


@pytest.mark.django_db
def test_step_unattach(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    root_alert_group = make_alert_group(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, root_alert_group=root_alert_group)
    make_alert(alert_group, raw_request_data={})

    payload = {
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk, "alert_group_pk": alert_group.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "UnAttachGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.root_alert_group is None


@pytest.mark.django_db
def test_step_unattach_deprecated(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    root_alert_group = make_alert_group(alert_receive_channel)
    alert_group = make_alert_group(alert_receive_channel, root_alert_group=root_alert_group)
    make_alert(alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id)

    payload = {
        "message_ts": slack_message.slack_id,
        "channel": {"id": slack_channel.slack_id},
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("distribute_alerts", "UnAttachGroupStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    alert_group.refresh_from_db()
    assert alert_group.root_alert_group is None


@pytest.mark.django_db
def test_step_format_alert(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    payload = {
        "message_ts": "RANDOM_TS",
        "trigger_id": "RANDOM_TRIGGER_ID",
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk, "alert_group_pk": alert_group.pk}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("alertgroup_appearance", "OpenAlertAppearanceDialogStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    # TODO: assert


@pytest.mark.django_db
def test_step_format_alert_deprecated(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_slack_channel,
    make_slack_message,
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group, raw_request_data={})

    slack_channel = make_slack_channel(slack_team_identity)
    slack_message = make_slack_message(alert_group=alert_group, channel_id=slack_channel.slack_id)

    payload = {
        "message_ts": slack_message.slack_id,
        "channel": {"id": slack_channel.slack_id},
        "trigger_id": "RANDOM_TRIGGER_ID",
        "actions": [
            {
                "type": "button",
                "value": json.dumps({"organization_id": organization.pk, "alert_group_pk": str(alert_group.pk)}),
            }
        ],
    }

    step_class = ScenarioStep.get_step("alertgroup_appearance", "OpenAlertAppearanceDialogStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    # TODO: assert


@pytest.mark.django_db
def test_step_resolution_note(
    make_organization_and_user_with_slack_identities, make_alert_receive_channel, make_alert_group, make_alert
):
    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()
    organization.refresh_from_db()  # without this there's something weird with organization.archive_alerts_from

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
    }

    step_class = ScenarioStep.get_step("resolution_note", "ResolutionNoteModalStep")
    step = step_class(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    # TODO: assert
