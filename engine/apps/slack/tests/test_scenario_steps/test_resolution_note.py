import json
from unittest.mock import patch

import pytest

from apps.slack.client import SlackClient
from apps.slack.constants import BLOCK_SECTION_TEXT_MAX_SIZE
from apps.slack.errors import SlackAPIViewNotFoundError
from apps.slack.scenarios.scenario_step import ScenarioStep
from apps.slack.tests.conftest import build_slack_response
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
def test_get_resolution_note_blocks_truncate_text(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_resolution_note,
):
    UpdateResolutionNoteStep = ScenarioStep.get_step("resolution_note", "UpdateResolutionNoteStep")
    organization, user, slack_team_identity, _ = make_organization_and_user_with_slack_identities()
    step = UpdateResolutionNoteStep(slack_team_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    resolution_note = make_resolution_note(alert_group=alert_group, author=user, message_text="a" * 3000)
    author_verbal = resolution_note.author_verbal(mention=False)

    blocks = step.get_resolution_note_blocks(resolution_note)

    expected_blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                # text is truncated, ellipsis added
                "text": resolution_note.text[: BLOCK_SECTION_TEXT_MAX_SIZE - 1] + "…",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"{author_verbal} resolution note from {resolution_note.get_source_display()}.",
                }
            ],
        },
    ]

    assert blocks == expected_blocks


@pytest.mark.django_db
def test_post_or_update_resolution_note_in_thread_truncate_message_text(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_slack_message,
    make_resolution_note,
):
    UpdateResolutionNoteStep = ScenarioStep.get_step("resolution_note", "UpdateResolutionNoteStep")
    organization, user, slack_team_identity, _ = make_organization_and_user_with_slack_identities()
    step = UpdateResolutionNoteStep(slack_team_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_slack_message(alert_group=alert_group, channel_id="RANDOM_CHANNEL_ID", slack_id="RANDOM_MESSAGE_ID")
    resolution_note = make_resolution_note(alert_group=alert_group, author=user, message_text="a" * 3000)

    with patch("apps.slack.client.SlackClient.api_call") as mock_slack_api_call:
        mock_slack_api_call.return_value = {
            "ts": "timestamp",
            "message": {"ts": "timestamp"},
            "permalink": "https://link.to.message",
        }
        step.post_or_update_resolution_note_in_thread(resolution_note)

    assert mock_slack_api_call.called
    post_message_call = mock_slack_api_call.mock_calls[0]
    assert post_message_call.args[0] == "chat.postMessage"
    assert post_message_call.kwargs["json"]["text"] == resolution_note.text[: BLOCK_SECTION_TEXT_MAX_SIZE - 1] + "…"


@pytest.mark.django_db
def test_post_or_update_resolution_note_in_thread_update_truncate_message_text(
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_slack_message,
    make_resolution_note,
    make_resolution_note_slack_message,
):
    UpdateResolutionNoteStep = ScenarioStep.get_step("resolution_note", "UpdateResolutionNoteStep")
    organization, user, slack_team_identity, _ = make_organization_and_user_with_slack_identities()
    step = UpdateResolutionNoteStep(slack_team_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_slack_message(alert_group=alert_group, channel_id="RANDOM_CHANNEL_ID", slack_id="RANDOM_MESSAGE_ID")
    resolution_note = make_resolution_note(alert_group=alert_group, author=user, message_text="a" * 3000)
    make_resolution_note_slack_message(
        alert_group=alert_group,
        resolution_note=resolution_note,
        user=user,
        posted_by_bot=True,
        added_by_user=user,
        ts=1,
        text=resolution_note.text,
    )

    with patch("apps.slack.client.SlackClient.api_call") as mock_slack_api_call:
        mock_slack_api_call.return_value = {
            "ts": "timestamp",
            "message": {"ts": "timestamp"},
            "permalink": "https://link.to.message",
        }
        step.post_or_update_resolution_note_in_thread(resolution_note)

    assert mock_slack_api_call.called
    post_message_call = mock_slack_api_call.mock_calls[0]
    assert post_message_call.args[0] == "chat.update"
    assert post_message_call.kwargs["json"]["text"] == resolution_note.text[: BLOCK_SECTION_TEXT_MAX_SIZE - 1] + "…"


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


@pytest.mark.django_db
@patch.object(
    SlackClient,
    "api_call",
    side_effect=SlackAPIViewNotFoundError(response=build_slack_response({"ok": False, "error": "not_found"})),
)
def test_resolution_notes_modal_closed_before_update(
    mock_slack_api_call,
    make_organization_and_user_with_slack_identities,
    make_alert_receive_channel,
    make_alert_group,
    make_slack_message,
):
    ResolutionNoteModalStep = ScenarioStep.get_step("resolution_note", "ResolutionNoteModalStep")

    organization, user, slack_team_identity, slack_user_identity = make_organization_and_user_with_slack_identities()

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_slack_message(alert_group=alert_group, channel_id="RANDOM_CHANNEL_ID", slack_id="RANDOM_MESSAGE_ID")

    payload = {
        "trigger_id": "TEST",
        "view": {"id": "TEST"},
        "actions": [
            {
                "type": "button",
                "value": json.dumps(
                    {
                        "organization_id": organization.pk,
                        "alert_group_pk": alert_group.pk,
                        "resolution_note_window_action": "update",
                    }
                ),
            }
        ],
    }

    # Check that no error is raised even if the Slack API call fails
    step = ResolutionNoteModalStep(organization=organization, user=user, slack_team_identity=slack_team_identity)
    step.process_scenario(slack_user_identity, slack_team_identity, payload)

    # Check that "views.update" API call was made
    call_args, _ = mock_slack_api_call.call_args
    assert call_args[0] == "views.update"
