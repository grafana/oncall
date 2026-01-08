import json
import logging
from typing import Optional

from rest_framework.request import Request
from telegram import Bot, MessageOriginChannel, Update

from apps.base.utils import live_settings
from apps.telegram.models import TelegramToOrganizationConnector, TelegramToUserConnector
from apps.telegram.updates.update_handlers.update_handler import UpdateHandler

logger = logging.getLogger(__name__)

TELEGRAM_ID = 777000


class UpdateManager:
    """
    Manager for Telegram updates
    It selects appropriate UpdateHandler and makes selected handler process the update
    Also UpdateManager updates user, channel and group names on every update to make sure names in database are in sync
    """

    @classmethod
    def process_update(cls, update: Update) -> None:
        cls._update_entity_names(update)

        handler = cls.select_update_handler(update)
        if handler is None:
            logger.info("No update handlers applied for update")
            return

        logger.info(f"Processing update with handler: {handler.__class__.__name__}")
        handler.process_update()

    @staticmethod
    def select_update_handler(update: Update) -> Optional[UpdateHandler]:
        handler_classes = UpdateHandler.__subclasses__()
        for handler_class in handler_classes:
            handler = handler_class(update)
            if handler.matches():
                return handler
        return None

    @classmethod
    def process_request(cls, request: Request) -> None:
        # In v20+, Update.de_json() is replaced
        # Update objects can be constructed from dict directly or use de_json_dict
        # We'll use the dict-based approach which is more compatible
        data_dict = request.data
        if isinstance(request.data, (str, bytes)):
            # handle case data is a json string
            data_dict = json.loads(request.data)

        # In v20+, Update can be constructed from dict
        # The bot parameter is optional for construction
        bot = Bot(live_settings.TELEGRAM_TOKEN) if live_settings.TELEGRAM_TOKEN else None
        update = Update.de_json(data_dict, bot=bot)
        logger.info(f"Update from Telegram: {update}")
        cls.process_update(update)

    @classmethod
    def _update_entity_names(cls, update: Update) -> None:
        if update.effective_user is None:
            return

        if update.effective_user.id == TELEGRAM_ID:
            cls._update_channel_and_group_names(update)
        else:
            cls._update_user_names(update)

    @staticmethod
    def _update_channel_and_group_names(update: Update) -> None:
        """
        some updates may not necessarily come from the channel
        (in which case they would contain the `forward_origin` object with MessageOriginChannel).
        Some updates may come directly from the discussion group, in which case `forward_origin` is not present
        """
        # In v20+, forward_from_chat is replaced with forward_origin
        if update.message.forward_origin is None:
            return

        # Only process messages forwarded from channels
        if not isinstance(update.message.forward_origin, MessageOriginChannel):
            return

        channel_chat_id = update.message.forward_origin.chat.id
        channel_name = update.message.forward_origin.chat.title

        discussion_group_chat_id = update.message.chat.id
        discussion_group_name = update.message.chat.title

        TelegramToOrganizationConnector.objects.filter(
            channel_chat_id=channel_chat_id, discussion_group_chat_id=discussion_group_chat_id
        ).update(channel_name=channel_name, discussion_group_name=discussion_group_name)

    @staticmethod
    def _update_user_names(update: Update) -> None:
        user = update.effective_user
        telegram_nick_name = user.username or user.first_name or user.last_name or "Unknown"

        TelegramToUserConnector.objects.filter(telegram_chat_id=user.id).update(telegram_nick_name=telegram_nick_name)
