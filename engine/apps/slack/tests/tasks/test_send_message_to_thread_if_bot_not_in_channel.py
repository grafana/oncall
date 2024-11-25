from unittest.mock import ANY, patch

import pytest
from celery import exceptions

from apps.slack.errors import SlackAPIRatelimitError
from apps.slack.tasks import send_message_to_thread_if_bot_not_in_channel
from apps.slack.tests.conftest import build_slack_response

BOT_USER_ID = "U12345678"
TEXT = f"Please invite <@{BOT_USER_ID}> to this channel to make all features available :wink:"


@pytest.mark.parametrize("channel_members", [["U0909090"], [BOT_USER_ID]])
@patch("apps.slack.models.SlackTeamIdentity.get_conversation_members")
@patch("apps.slack.tasks.SlackClient")
@patch("apps.slack.tasks.AlertGroupSlackService")
@pytest.mark.django_db
def test_send_message_to_thread_if_bot_not_in_channel(
    MockAlertGroupSlackService,
    MockSlackClient,
    mock_get_conversation_members,
    make_slack_team_identity,
    make_slack_channel,
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
    channel_members,
):
    mock_get_conversation_members.return_value = channel_members

    slack_team_identity = make_slack_team_identity(bot_user_id=BOT_USER_ID)
    slack_channel = make_slack_channel(slack_team_identity)

    organization = make_organization(slack_team_identity=slack_team_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    send_message_to_thread_if_bot_not_in_channel(alert_group.pk, slack_team_identity.pk, slack_channel.pk)

    MockSlackClient.assert_called_once_with(slack_team_identity, enable_ratelimit_retry=True)
    mock_get_conversation_members.assert_called_once_with(MockSlackClient.return_value, slack_channel.pk)

    if BOT_USER_ID not in channel_members:
        MockAlertGroupSlackService.assert_called_once_with(slack_team_identity, MockSlackClient.return_value)

        MockAlertGroupSlackService.return_value.publish_message_to_alert_group_thread.assert_called_once_with(
            alert_group, text=TEXT
        )
    else:
        MockAlertGroupSlackService.return_value.publish_message_to_alert_group_thread.assert_not_called()


@patch("apps.slack.models.SlackTeamIdentity.get_conversation_members")
@patch("apps.slack.tasks.SlackClient")
@patch("apps.slack.tasks.AlertGroupSlackService")
@patch("apps.slack.tasks.send_message_to_thread_if_bot_not_in_channel.retry")
@pytest.mark.django_db
def test_send_message_to_thread_if_bot_not_in_channel_slack_api_rate_limit_error(
    mock_send_message_to_thread_if_bot_not_in_channel_retry,
    MockAlertGroupSlackService,
    MockSlackClient,
    mock_get_conversation_members,
    make_slack_team_identity,
    make_slack_channel,
    make_organization,
    make_alert_receive_channel,
    make_alert_group,
):
    mock_send_message_to_thread_if_bot_not_in_channel_retry.side_effect = exceptions.Retry()
    mock_get_conversation_members.return_value = ["U0909090"]

    RETRY_AFTER = 42

    MockAlertGroupSlackService.return_value.publish_message_to_alert_group_thread.side_effect = SlackAPIRatelimitError(
        response=build_slack_response({"ok": False, "error": "ratelimited"}, headers={"Retry-After": RETRY_AFTER})
    )

    slack_team_identity = make_slack_team_identity(bot_user_id=BOT_USER_ID)
    slack_channel = make_slack_channel(slack_team_identity)

    organization = make_organization(slack_team_identity=slack_team_identity)

    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    with pytest.raises(exceptions.Retry):
        send_message_to_thread_if_bot_not_in_channel(alert_group.pk, slack_team_identity.pk, slack_channel.pk)

    MockAlertGroupSlackService.assert_called_once_with(slack_team_identity, MockSlackClient.return_value)

    MockAlertGroupSlackService.return_value.publish_message_to_alert_group_thread.assert_called_once_with(
        alert_group, text=TEXT
    )

    mock_send_message_to_thread_if_bot_not_in_channel_retry.assert_called_once_with(
        (alert_group.pk, slack_team_identity.pk, slack_channel.pk), countdown=RETRY_AFTER, exc=ANY
    )
