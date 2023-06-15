import logging
from typing import Optional, Tuple, Union

from telegram import Bot, InlineKeyboardMarkup, Message, ParseMode
from telegram.error import BadRequest, InvalidToken, Unauthorized
from telegram.utils.request import Request

from apps.alerts.models import AlertGroup
from apps.base.utils import live_settings
from apps.telegram.models import TelegramMessage
from apps.telegram.renderers.keyboard import TelegramKeyboardRenderer
from apps.telegram.renderers.message import TelegramMessageRenderer
from common.api_helpers.utils import create_engine_url

logger = logging.getLogger(__name__)


class TelegramClient:
    ALLOWED_UPDATES = ("message", "callback_query")
    PARSE_MODE = ParseMode.HTML

    def __init__(self, token: Optional[str] = None):
        self.token = token or live_settings.TELEGRAM_TOKEN

        if self.token is None:
            raise InvalidToken()

    @property
    def api_client(self) -> Bot:
        return Bot(self.token, request=Request(read_timeout=15))

    def is_chat_member(self, chat_id: Union[int, str]) -> bool:
        try:
            self.api_client.get_chat(chat_id=chat_id)
            return True
        except Unauthorized:
            return False

    def register_webhook(self, webhook_url: Optional[str] = None) -> None:
        webhook_url = webhook_url or create_engine_url("/telegram/", override_base=live_settings.TELEGRAM_WEBHOOK_HOST)

        # avoid unnecessary set_webhook calls to make sure Telegram rate limits are not exceeded
        webhook_info = self.api_client.get_webhook_info()
        if webhook_info.url == webhook_url:
            return

        self.api_client.set_webhook(webhook_url, allowed_updates=self.ALLOWED_UPDATES)

    def delete_webhook(self):
        webhook_info = self.api_client.get_webhook_info()
        if webhook_info.url == "":
            return

        self.api_client.delete_webhook()

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
            message = self.api_client.send_message(
                chat_id=chat_id,
                text=text,
                reply_markup=keyboard,
                reply_to_message_id=reply_to_message_id,
                parse_mode=self.PARSE_MODE,
                disable_web_page_preview=False,
            )
        except BadRequest as e:
            logger.warning("Telegram BadRequest: {}".format(e.message))
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
        return self.api_client.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=self.PARSE_MODE,
            disable_web_page_preview=False,
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
                raise Exception("No alert group message found, probably it is not saved to database yet")

            include_title = message_type == TelegramMessage.LINK_TO_CHANNEL_MESSAGE
            link = alert_group_message.link

            text = message_renderer.render_link_to_channel_message(include_title=include_title)
            keyboard = keyboard_renderer.render_link_to_channel_keyboard(link=link)
        else:
            raise Exception(f"_get_message_and_keyboard with type {message_type} is not implemented")

        return text, keyboard
