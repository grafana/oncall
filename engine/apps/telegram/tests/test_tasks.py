from unittest.mock import patch

import pytest
from telegram import error

from apps.telegram.client import TelegramClient
from apps.telegram.models import TelegramMessage
from apps.telegram.tasks import send_log_and_actions_message

bad_request_error_msg = TelegramClient.BadRequestMessage.MESSAGE_TO_BE_REPLIED_NOT_FOUND


@patch.object(TelegramClient, "send_raw_message", side_effect=error.BadRequest(bad_request_error_msg))
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
        f"due to '{bad_request_error_msg}'. alert_group {alert_group.pk}"
    )
    assert expected_msg in caplog.text
