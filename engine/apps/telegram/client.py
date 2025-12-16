import logging
from typing import Optional, Tuple, Union

from django.conf import settings
from telegram import Bot, InlineKeyboardMarkup, Message
from telegram.constants import ParseMode
from telegram.error import BadRequest, Forbidden, InvalidToken, TelegramError

from apps.alerts.models import AlertGroup
from apps.base.utils import live_settings
from apps.telegram.exceptions import AlertGroupTelegramMessageDoesNotExist
from apps.telegram.models import TelegramMessage
from apps.telegram.renderers.keyboard import TelegramKeyboardRenderer
from apps.telegram.renderers.message import TelegramMessageRenderer
from apps.telegram.utils import run_async
from common.api_helpers.utils import create_engine_url

logger = logging.getLogger(__name__)


class TelegramClient:
    ALLOWED_UPDATES = ("message", "callback_query")
    PARSE_MODE = ParseMode.HTML

    def __init__(self, token: Optional[str] = None):
        self.token = token or live_settings.TELEGRAM_TOKEN

        if self.token is None:
            raise InvalidToken()

        # In v20+, Bot initialization is simpler, no Request needed
        # Connection pooling and timeouts are handled internally
        self.api_client = Bot(self.token)

    class BadRequestMessage:
        CHAT_NOT_FOUND = "Chat not found"
        MESSAGE_IS_NOT_MODIFIED = "Message is not modified"
        MESSAGE_TO_EDIT_NOT_FOUND = "Message to edit not found"
        NEED_ADMIN_RIGHTS_IN_THE_CHANNEL = "Need administrator rights in the channel chat"
        MESSAGE_TO_BE_REPLIED_NOT_FOUND = "Message to be replied not found"

    class UnauthorizedMessage:
        BOT_WAS_BLOCKED_BY_USER = "Forbidden: bot was blocked by the user"
        INVALID_TOKEN = "Invalid token"
        USER_IS_DEACTIVATED = "Forbidden: user is deactivated"

    def get_bot_info(self):
        """
        Get bot information (name, username, etc.)
        In v20+, bot properties require async get_me() call
        """
        return run_async(self.api_client.get_me())

    def get_bot_username(self):
        return run_async(self.api_client.get_me()).username

    def is_chat_member(self, chat_id: Union[int, str]) -> bool:
        try:
            # Bot methods are now async in v20+
            run_async(self.api_client.get_chat(chat_id=chat_id))
            return True
        except Forbidden:
            return False

    def register_webhook(self, webhook_url: Optional[str] = None) -> None:
        if settings.IS_OPEN_SOURCE:
            webhook_url = webhook_url or create_engine_url(
                "/telegram/", override_base=live_settings.TELEGRAM_WEBHOOK_HOST
            )
        else:
            webhook_url = webhook_url or create_engine_url(
                "api/v3/webhook/telegram/", override_base=live_settings.TELEGRAM_WEBHOOK_HOST
            )
        # avoid unnecessary set_webhook calls to make sure Telegram rate limits are not exceeded
        webhook_info = run_async(self.api_client.get_webhook_info())
        if webhook_info.url == webhook_url:
            return

        run_async(self.api_client.set_webhook(webhook_url, allowed_updates=self.ALLOWED_UPDATES))

    def delete_webhook(self):
        webhook_info = run_async(self.api_client.get_webhook_info())
        if webhook_info.url == "":
            return

        run_async(self.api_client.delete_webhook())

    def send_message(
        self,
        chat_id: Union[int, str],
        message_type: int,
        alert_group: AlertGroup,
        reply_to_message_id: Optional[int] = None,
    ) -> TelegramMessage:
        text, keyboard = self._get_message_and_keyboard(message_type=message_type, alert_group=alert_group)

        raw_message = self.send_raw_message(
            chat_id=chat_id, text=text, keyboard=keyboard, reply_to_message_id=reply_to_message_id
        )
        message = TelegramMessage.create_from_message(
            message=raw_message, alert_group=alert_group, message_type=message_type
        )

        return message

    def send_raw_message(
        self,
        chat_id: Union[int, str],
        text: str,
        keyboard: Optional[InlineKeyboardMarkup] = None,
        reply_to_message_id: Optional[int] = None,
    ) -> Message:
        try:
            # Bot methods are now async in v20+
            message = run_async(
                self.api_client.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=keyboard,
                    reply_to_message_id=reply_to_message_id,
                    parse_mode=self.PARSE_MODE,
                    # Note: disable_web_page_preview removed in v20+,
                    # link previews are controlled via LinkPreviewOptions if needed
                )
            )
        except BadRequest as e:
            # Error message access may have changed - try common patterns
            error_msg = getattr(e, "message", str(e))
            logger.warning(f"Telegram BadRequest: {error_msg}")
            raise

        return message

    def edit_message(self, message: TelegramMessage) -> TelegramMessage:
        text, keyboard = self._get_message_and_keyboard(
            message_type=message.message_type, alert_group=message.alert_group
        )

        self.edit_raw_message(chat_id=message.chat_id, message_id=message.message_id, text=text, keyboard=keyboard)
        return message

    def edit_raw_message(
        self,
        chat_id: Union[int, str],
        message_id: Union[int, str],
        text: str,
        keyboard: Optional[InlineKeyboardMarkup] = None,
    ) -> Union[Message, bool]:
        # Bot methods are now async in v20+
        return run_async(
            self.api_client.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=self.PARSE_MODE,
            )
        )

    @staticmethod
    def _get_message_and_keyboard(
        message_type: int, alert_group: AlertGroup
    ) -> Tuple[str, Optional[InlineKeyboardMarkup]]:
        message_renderer = TelegramMessageRenderer(alert_group=alert_group)
        keyboard_renderer = TelegramKeyboardRenderer(alert_group=alert_group)

        if message_type == TelegramMessage.ALERT_GROUP_MESSAGE:
            text = message_renderer.render_alert_group_message()
            keyboard = None
        elif message_type == TelegramMessage.LOG_MESSAGE:
            text = message_renderer.render_log_message()
            keyboard = None
        elif message_type == TelegramMessage.ACTIONS_MESSAGE:
            text = message_renderer.render_actions_message()
            keyboard = keyboard_renderer.render_actions_keyboard()
        elif message_type == TelegramMessage.PERSONAL_MESSAGE:
            text = message_renderer.render_personal_message()
            keyboard = keyboard_renderer.render_actions_keyboard()
        elif message_type == TelegramMessage.FORMATTING_ERROR:
            text = message_renderer.render_formatting_error_message()
            keyboard = None
        elif message_type in (
            TelegramMessage.LINK_TO_CHANNEL_MESSAGE,
            TelegramMessage.LINK_TO_CHANNEL_MESSAGE_WITHOUT_TITLE,
        ):
            alert_group_message = alert_group.telegram_messages.filter(
                chat_id__startswith="-",
                message_type__in=[TelegramMessage.ALERT_GROUP_MESSAGE, TelegramMessage.FORMATTING_ERROR],
            ).first()

            if alert_group_message is None:
                raise AlertGroupTelegramMessageDoesNotExist(
                    f"No alert group message found, probably it is not saved to database yet, "
                    f"alert group: {alert_group.id}"
                )

            include_title = message_type == TelegramMessage.LINK_TO_CHANNEL_MESSAGE
            link = alert_group_message.link

            text = message_renderer.render_link_to_channel_message(include_title=include_title)
            keyboard = keyboard_renderer.render_link_to_channel_keyboard(link=link)
        else:
            raise Exception(f"_get_message_and_keyboard with type {message_type} is not implemented")

        return text, keyboard

    @staticmethod
    def error_message_is(error: TelegramError, messages: list[str]) -> bool:
        # Error message access may have changed in v20+
        # Try common patterns: .message, .args[0], str()
        error_msg = getattr(error, "message", None) or (error.args[0] if error.args else str(error))
        return error_msg.lower() in (m.lower() for m in messages)
