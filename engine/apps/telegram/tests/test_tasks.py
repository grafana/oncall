from unittest.mock import patch

import pytest
from telegram import error

from apps.base.models import UserNotificationPolicy
from apps.telegram.client import TelegramClient
from apps.telegram.exceptions import AlertGroupTelegramMessageDoesNotExist
from apps.telegram.models import TelegramMessage, TelegramToUserConnector
from apps.telegram.tasks import (
    send_link_to_channel_message_or_fallback_to_full_alert_group,
    send_log_and_actions_message,
)


@patch.object(TelegramClient, "send_raw_message", side_effect=error.BadRequest("Message to reply not found"))
@pytest.mark.django_db
def test_send_log_and_actions_replied_message_not_found(
    mock_send_message,
    make_organization_and_user,
    make_telegram_user_connector,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_telegram_message,
    caplog,
):
    # set up a user with Telegram account connected
    organization, user = make_organization_and_user()
    make_telegram_user_connector(user)

    # create an alert group with an existing Telegram message in user's DM
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    telegram_message = make_telegram_message(
        alert_group=alert_group,
        message_type=TelegramMessage.PERSONAL_MESSAGE,
        chat_id=str(user.telegram_connection.telegram_chat_id),
        message_id=123,
    )

    reply_to_message_id = 321
    send_log_and_actions_message(
        telegram_message.chat_id, "group_chat_id", telegram_message.message_id, reply_to_message_id
    )

    expected_msg = (
        f"Could not send log and actions messages to Telegram group with id group_chat_id "
        f"due to 'Message to reply not found'. alert_group {alert_group.pk}"
    )
    assert expected_msg in caplog.text


@patch.object(TelegramToUserConnector, "send_link_to_channel_message")
@pytest.mark.django_db
def test_send_link_to_channel_message_or_fallback_to_full_alert_group_message_does_not_exist(
    mock_send_link_to_channel_message,
    make_organization_and_user,
    make_telegram_user_connector,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
):
    organization, user = make_organization_and_user()
    user_connector = make_telegram_user_connector(user)
    user_notification_policy = make_user_notification_policy(
        user=user,
        step=UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TELEGRAM,
    )
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    mock_send_link_to_channel_message.side_effect = AlertGroupTelegramMessageDoesNotExist(
        f"No alert group message found, probably it is not saved to database yet, alert group: {alert_group.id}"
    )

    with patch.object(send_link_to_channel_message_or_fallback_to_full_alert_group, "apply_async") as mocked_task_call:
        send_link_to_channel_message_or_fallback_to_full_alert_group(
            alert_group.id, user_notification_policy.id, user_connector.id
        )
    # No exception raised, task restarted with `is_first_message_check=False`
    mocked_task_call.assert_called_once_with(
        (alert_group.id, user_notification_policy.id, user_connector.id, False), countdown=3
    )
    # if task started with `is_first_message_check=False` and alert group telegram message was not found,
    # exception will be raised
    with pytest.raises(AlertGroupTelegramMessageDoesNotExist):
        send_link_to_channel_message_or_fallback_to_full_alert_group(
            alert_group.id, user_notification_policy.id, user_connector.id, False
        )
