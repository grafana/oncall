from unittest.mock import patch

import pytest
from telegram import error

from apps.base.models import UserNotificationPolicy
from apps.telegram.client import TelegramClient
from apps.telegram.models import TelegramMessage


@patch.object(TelegramClient, "send_raw_message", side_effect=error.BadRequest("Replied message not found"))
@pytest.mark.django_db
def test_personal_connector_replied_message_not_found(
    mock_send_message,
    make_organization_and_user,
    make_telegram_user_connector,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_telegram_message,
):
    # set up a user with Telegram account connected
    organization, user = make_organization_and_user()
    make_telegram_user_connector(user)
    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TELEGRAM,
        important=False,
    )

    # create an alert group with an existing Telegram message in user's DM
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    telegram_message = make_telegram_message(
        alert_group=alert_group,
        message_type=TelegramMessage.PERSONAL_MESSAGE,
        chat_id=str(user.telegram_connection.telegram_chat_id),
    )

    # make sure no exception is raised when replying to the message that has been deleted
    user.telegram_connection.notify(alert_group=alert_group, notification_policy=notification_policy)
    mock_send_message.assert_called_once_with(
        chat_id=telegram_message.chat_id,
        text="One more notification about this 👆",
        reply_to_message_id=telegram_message.message_id,
    )
