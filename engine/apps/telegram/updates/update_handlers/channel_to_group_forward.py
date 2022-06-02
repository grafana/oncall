import logging
import re

from apps.telegram.client import TelegramClient
from apps.telegram.models import TelegramToOrganizationConnector
from apps.telegram.tasks import send_log_and_actions_message
from apps.telegram.updates.update_handlers import UpdateHandler
from apps.telegram.updates.update_handlers.verification.channel import (
    CHANNEL_CONNECTED_TEXT,
    RELINK_CHANNEL_TEXT,
    WRONG_VERIFICATION_CODE,
)
from apps.telegram.utils import is_verification_message

logger = logging.getLogger(__name__)

TELEGRAM_ID = 777000
SIGN_MESSAGES_NOT_ENABLED = """Please enable "Sign messages" in channel settings!
Otherwise Grafana OnCall bot will not be able to operate properly!"""


class ChannelToGroupForwardHandler(UpdateHandler):
    def matches(self) -> bool:
        is_message = self.update.message is not None and self.update.message.text is not None

        if not is_message:
            return False

        is_from_discussion_group = self.update.message.chat.type == "supergroup"
        is_forwarded_by_telegram = self.update.effective_user.id == TELEGRAM_ID

        # Make sure that only alert group messages are processed with this handler
        is_verification_successful_message = bool(
            re.match(CHANNEL_CONNECTED_TEXT.format(organization_title=".*"), self.update.message.text_html)
        )
        is_relink_channel_message = bool(
            re.match(RELINK_CHANNEL_TEXT.format(organization_title=".*"), self.update.message.text_html)
        )
        is_verification_failed_message = self.update.message.text == WRONG_VERIFICATION_CODE

        return (
            is_from_discussion_group
            and is_forwarded_by_telegram
            and not is_verification_message(self.update.message.text)
            and not (is_verification_successful_message or is_relink_channel_message or is_verification_failed_message)
        )

    def process_update(self) -> None:
        telegram_client = TelegramClient()

        if self.update.message.forward_signature is None:
            telegram_client.send_raw_message(
                chat_id=self.update.message.chat.id,
                text=SIGN_MESSAGES_NOT_ENABLED,
                reply_to_message_id=self.update.message.message_id,
            )
            return

        channel_chat_id = self.update.message.forward_from_chat.id
        channel_message_id = self.update.message.forward_from_message_id
        group_message_id = self.update.message.message_id

        if self.update.message.forward_signature != telegram_client.api_client.first_name:
            return

        try:
            connector = TelegramToOrganizationConnector.objects.get(channel_chat_id=channel_chat_id)
            send_log_and_actions_message.delay(
                channel_chat_id=connector.channel_chat_id,
                group_chat_id=connector.discussion_group_chat_id,
                channel_message_id=channel_message_id,
                reply_to_message_id=group_message_id,
            )

        except TelegramToOrganizationConnector.DoesNotExist:
            logger.warning(
                f"Tried to send log and action message to comments, but organization deleted the channel connector. "
                f"Channel chat id: {channel_chat_id}. "
                f"Channel message id: {channel_message_id}. "
                f"Group message id: {group_message_id}."
            )
