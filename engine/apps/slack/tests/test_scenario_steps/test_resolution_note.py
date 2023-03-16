import json

import pytest

from apps.slack.scenarios.scenario_step import ScenarioStep
from common.api_helpers.utils import create_engine_url


@pytest.mark.django_db
def test_get_resolution_notes_blocks_default_if_empty(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
):
    SlackResolutionNoteModalStep = ScenarioStep.get_step("resolution_note", "ResolutionNoteModalStep")
    organization, _, slack_team_identity, _ = make_organization_and_user_with_slack_identities()
    step = SlackResolutionNoteModalStep(slack_team_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    blocks = step.get_resolution_notes_blocks(alert_group, "", False)

    link_to_instruction = create_engine_url("static/images/postmortem.gif")
    expected_blocks = [
        {
            "type": "divider",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":bulb: You can add a message to the resolution notes via context menu:",
            },
        },
        {
            "type": "image",
            "title": {
                "type": "plain_text",
                "text": "Add a resolution note",
            },
            "image_url": link_to_instruction,
            "alt_text": "Add to postmortem context menu",
        },
    ]
    assert blocks == expected_blocks


@pytest.mark.django_db
def test_get_resolution_notes_blocks_non_empty(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_resolution_note_slack_message,
):
    SlackResolutionNoteModalStep = ScenarioStep.get_step("resolution_note", "ResolutionNoteModalStep")
    organization, user, slack_team_identity, _ = make_organization_and_user_with_slack_identities()
    step = SlackResolutionNoteModalStep(slack_team_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    resolution_note = make_resolution_note_slack_message(alert_group=alert_group, user=user, added_by_user=user, ts=1)

    blocks = step.get_resolution_notes_blocks(alert_group, "", False)

    expected_blocks = [
        {
            "type": "divider",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "{} <!date^{:.0f}^{{date_num}} {{time_secs}}|message_created_at>\n{}".format(
                    resolution_note.user.get_username_with_slack_verbal(mention=True),
                    float(resolution_note.ts),
                    resolution_note.text,
                ),
            },
            "accessory": {
                "type": "button",
                "style": "primary",
                "text": {
                    "type": "plain_text",
                    "text": "Add",
                    "emoji": True,
                },
                "action_id": "AddRemoveThreadMessageStep",
                "value": json.dumps(
                    {
                        "resolution_note_window_action": "edit",
                        "msg_value": "add",
                        "message_pk": resolution_note.pk,
                        "resolution_note_pk": None,
                        "alert_group_pk": alert_group.pk,
                    }
                ),
            },
        },
    ]

    assert blocks == expected_blocks


@pytest.mark.django_db
def test_get_resolution_notes_blocks_latest_limit(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_resolution_note_slack_message,
):
    SlackResolutionNoteModalStep = ScenarioStep.get_step("resolution_note", "ResolutionNoteModalStep")
    organization, user, slack_team_identity, _ = make_organization_and_user_with_slack_identities()
    step = SlackResolutionNoteModalStep(slack_team_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    max_count = SlackResolutionNoteModalStep.RESOLUTION_NOTE_MESSAGES_MAX_COUNT
    messages = [
        make_resolution_note_slack_message(alert_group=alert_group, user=user, added_by_user=user, ts=i, text=i)
        for i in range(max_count * 2)
    ]

    blocks = step.get_resolution_notes_blocks(alert_group, "", False)

    expected_blocks = [
        {
            "type": "divider",
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    ":warning: Listing up to last {} thread messages, "
                    "you can still add any other message using contextual menu actions."
                ).format(max_count),
            },
        },
    ]
    for m in list(reversed(messages))[:max_count]:
        expected_blocks += [
            {
                "type": "divider",
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "{} <!date^{:.0f}^{{date_num}} {{time_secs}}|message_created_at>\n{}".format(
                        m.user.get_username_with_slack_verbal(mention=True),
                        float(m.ts),
                        m.text,
                    ),
                },
                "accessory": {
                    "type": "button",
                    "style": "primary",
                    "text": {
                        "type": "plain_text",
                        "text": "Add",
                        "emoji": True,
                    },
                    "action_id": "AddRemoveThreadMessageStep",
                    "value": json.dumps(
                        {
                            "resolution_note_window_action": "edit",
                            "msg_value": "add",
                            "message_pk": m.pk,
                            "resolution_note_pk": None,
                            "alert_group_pk": alert_group.pk,
                        }
                    ),
                },
            },
        ]

    assert blocks == expected_blocks
