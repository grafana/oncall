from unittest.mock import call, patch

import pytest
from telegram import error

from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.telegram.client import TelegramClient
from apps.telegram.models import TelegramMessage, TelegramToUserConnector


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


@pytest.mark.parametrize(
    "side_effect,notification_error_code,reason",
    [
        (
            error.Unauthorized("Forbidden: bot was blocked by the user"),
            UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_BOT_IS_DELETED,
            "Bot was blocked by the user",
        ),
        (
            error.Unauthorized("Invalid token"),
            UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_TOKEN_ERROR,
            "Invalid token",
        ),
        (
            error.Unauthorized("Forbidden: user is deactivated"),
            UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_USER_IS_DEACTIVATED,
            "Telegram user was disabled",
        ),
    ],
)
@pytest.mark.django_db
def test_personal_connector_send_link_to_channel_message_handle_exceptions(
    side_effect,
    notification_error_code,
    reason,
    make_organization_and_user,
    make_telegram_user_connector,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
):
    # set up a user with Telegram account connected
    organization, user = make_organization_and_user()
    user_connector = make_telegram_user_connector(user)
    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TELEGRAM,
        important=False,
    )

    # create an alert group with an existing Telegram message in user's DM
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)

    assert not user.personal_log_records.exists()

    with patch.object(TelegramClient, "send_message", side_effect=side_effect) as mock_send_message:
        user_connector.send_link_to_channel_message(alert_group, notification_policy)

    mock_send_message.assert_called_once()
    log_records = user.personal_log_records.filter(alert_group=alert_group)
    assert log_records.count() == 1
    assert log_records.first().notification_error_code == notification_error_code
    assert log_records.first().reason == reason


@patch.object(TelegramClient, "send_message")
@pytest.mark.django_db
def test_personal_connector_send_link_to_channel_message(
    mock_send_message,
    make_organization_and_user,
    make_telegram_user_connector,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
    make_telegram_channel,
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

    # create an alert group with an existing Telegram message in channel
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    telegram_channel = make_telegram_channel(organization, is_default_channel=True)
    make_telegram_message(
        alert_group=alert_group,
        message_type=TelegramMessage.ALERT_GROUP_MESSAGE,
        chat_id=str(telegram_channel.channel_chat_id),
    )

    user.telegram_connection.send_link_to_channel_message(alert_group, notification_policy)
    mock_send_message.assert_called_once_with(
        chat_id=user.telegram_connection.telegram_chat_id,
        message_type=TelegramMessage.LINK_TO_CHANNEL_MESSAGE,
        alert_group=alert_group,
    )

    log_record = notification_policy.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS


@patch.object(TelegramClient, "send_message")
@pytest.mark.django_db
def test_personal_connector_send_full_alert_group(
    mock_send_message,
    make_organization_and_user,
    make_telegram_user_connector,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
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

    # create an alert group with an existing Telegram message in channel
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    user.telegram_connection.send_full_alert_group(alert_group, notification_policy)
    mock_send_message.assert_called_once_with(
        chat_id=user.telegram_connection.telegram_chat_id,
        message_type=TelegramMessage.PERSONAL_MESSAGE,
        alert_group=alert_group,
    )

    log_record = notification_policy.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS


@patch.object(TelegramToUserConnector, "_nudge_about_alert_group_message")
@pytest.mark.django_db
def test_personal_connector_send_full_alert_group_second_time(
    mock_nudge_about_alert_group_message,
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
    connector = make_telegram_user_connector(user)
    notification_policy = make_user_notification_policy(
        user,
        UserNotificationPolicy.Step.NOTIFY,
        notify_by=UserNotificationPolicy.NotificationChannel.TELEGRAM,
        important=False,
    )

    # create an alert group with an existing Telegram message in channel
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)
    make_telegram_message(
        alert_group=alert_group,
        message_type=TelegramMessage.PERSONAL_MESSAGE,
        chat_id=connector.telegram_chat_id,
    )
    user.telegram_connection.send_full_alert_group(alert_group, notification_policy)
    mock_nudge_about_alert_group_message.assert_called_once()
    log_record = notification_policy.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS


@patch.object(TelegramClient, "send_message", side_effect=[error.BadRequest("error"), None])
@pytest.mark.django_db
def test_personal_connector_send_full_alert_group_formatting_error(
    mock_send_message,
    make_organization_and_user,
    make_telegram_user_connector,
    make_user_notification_policy,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
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

    # create an alert group with an existing Telegram message in channel
    alert_receive_channel = make_alert_receive_channel(organization)
    alert_group = make_alert_group(alert_receive_channel)
    make_alert(alert_group=alert_group, raw_request_data=alert_receive_channel.config.example_payload)

    user.telegram_connection.send_full_alert_group(alert_group, notification_policy)

    failed_call, notification_call = mock_send_message.mock_calls
    assert failed_call == call(
        chat_id=user.telegram_connection.telegram_chat_id,
        message_type=TelegramMessage.PERSONAL_MESSAGE,
        alert_group=alert_group,
    )
    assert notification_call == call(
        chat_id=user.telegram_connection.telegram_chat_id,
        message_type=TelegramMessage.FORMATTING_ERROR,
        alert_group=alert_group,
    )

    log_record = notification_policy.personal_log_records.last()
    assert log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED
