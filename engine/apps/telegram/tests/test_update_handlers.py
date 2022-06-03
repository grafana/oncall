from datetime import datetime
from unittest.mock import patch

import pytest
from telegram import CallbackQuery, Chat, Message, Update, User

from apps.telegram.client import TelegramClient
from apps.telegram.renderers.keyboard import Action
from apps.telegram.updates.update_handlers import ChannelVerificationCodeHandler, StartMessageHandler
from apps.telegram.updates.update_handlers.button_press import ButtonPressHandler
from apps.telegram.updates.update_handlers.start_message import START_TEXT
from apps.telegram.updates.update_handlers.verification.channel import (
    VERIFICATION_FAILED_DISCUSSION_GROUP_ALREADY_REGISTERED,
)
from apps.telegram.utils import CallbackQueryFactory


def generate_update(message_text: str) -> Update:
    user = User(id=0, first_name="Test", is_bot=False)
    chat = Chat(id=0, type=Chat.PRIVATE)
    message = Message(message_id=0, text=message_text, chat=chat, from_user=user, date=datetime.now())
    update = Update(update_id=0, message=message)
    return update


def generate_channel_verification_code_message(verification_code: str, discussion_group_chat_id: str) -> Update:
    user = User(id=0, first_name="Test", is_bot=False)
    chat = Chat(id=discussion_group_chat_id, type=Chat.PRIVATE)
    channel = Chat(id=0, type=Chat.CHANNEL)
    message = Message(
        message_id=0,
        text=verification_code,
        chat=chat,
        from_user=user,
        date=datetime.now(),
        forward_from_chat=channel,
        forward_signature="the-signature",
    )
    update = Update(update_id=0, message=message)
    return update


def generate_button_press_ack_message(chat_id, alert_group) -> Update:
    user = User(id=chat_id, first_name="Test", is_bot=False)
    callback_query = CallbackQuery(
        id=0,
        from_user=user,
        chat_instance=Chat(id=chat_id, type=Chat.PRIVATE),
        data=CallbackQueryFactory.encode_data(alert_group.pk, Action.ACKNOWLEDGE.value),
    )
    update = Update(update_id=0, callback_query=callback_query)
    return update


@pytest.mark.parametrize(
    "text, matches", (("/start", True), ("start", False), ("/startx", False), ("/start smth", False))
)
def test_start_message_handler_matches(text, matches):
    update = generate_update(message_text=text)
    handler = StartMessageHandler(update=update)
    assert handler.matches() is matches


@pytest.mark.django_db
def test_start_message_handler_process_update():
    update = generate_update(message_text="/start")
    handler = StartMessageHandler(update=update)

    with patch.object(TelegramClient, "send_raw_message") as mock:
        handler.process_update()
        mock.assert_called_with(chat_id=update.message.from_user.id, text=START_TEXT)


@pytest.mark.django_db
def test_channel_verification_handler_process_update_duplicated_discussion_group_id(
    make_organization, make_telegram_channel
):
    organization = make_organization()
    existing_channel = make_telegram_channel(organization=organization)
    chat_id = existing_channel.discussion_group_chat_id

    update = generate_channel_verification_code_message(verification_code="123", discussion_group_chat_id=chat_id)
    handler = ChannelVerificationCodeHandler(update=update)

    with patch.object(TelegramClient, "is_chat_member") as mock_is_member:
        mock_is_member.return_value = True
        with patch.object(TelegramClient, "send_raw_message") as mock:
            handler.process_update()
            mock.assert_called_with(
                chat_id=update.message.chat.id,
                text=VERIFICATION_FAILED_DISCUSSION_GROUP_ALREADY_REGISTERED,
                reply_to_message_id=update.message.message_id,
            )


@pytest.mark.django_db
def test_button_press_handler_gets_user(
    make_organization,
    make_user_for_organization,
    make_telegram_user_connector,
    make_alert_receive_channel,
    make_alert_group,
    make_alert,
):
    organization = make_organization()

    chat_id = 123
    user_1 = make_user_for_organization(organization)
    make_telegram_user_connector(user_1, telegram_chat_id=chat_id)
    user_2 = make_user_for_organization(organization)
    make_telegram_user_connector(user_2, telegram_chat_id=chat_id)

    alert_receive_channel = make_alert_receive_channel(organization=organization)
    alert_group = make_alert_group(alert_receive_channel=alert_receive_channel)
    make_alert(alert_group, "")

    update = generate_button_press_ack_message(chat_id, alert_group)
    handler = ButtonPressHandler(update=update)
    handler.process_update()

    alert_group.refresh_from_db()
    assert alert_group.acknowledged
    assert alert_group.acknowledged_by_user == user_2
