import logging
from functools import wraps

from telegram import error

from apps.telegram.client import TelegramClient

logger = logging.getLogger(__name__)


def handle_missing_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            TelegramClient()
        except error.InvalidToken as e:
            logger.warning(
                "Tried to initialize a Telegram client, but TELEGRAM_TOKEN live setting is invalid or missing. "
                f"Exception: {e}"
            )
            return
        else:
            return f(*args, **kwargs)

    return decorated


def ignore_bot_deleted(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except error.Unauthorized:
            logger.warning(f"Tried to send Telegram message, but user deleted the bot. args: {args}, kwargs: {kwargs}")

    return decorated


def ignore_message_unchanged(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except error.BadRequest as e:
            if "Message is not modified" in e.message:
                logger.warning(
                    f"Tried to change Telegram message, but update is identical to original message. "
                    f"args: {args}, kwargs: {kwargs}"
                )
            else:
                raise e

    return decorated


def ignore_message_to_edit_deleted(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except error.BadRequest as e:
            if "Message to edit not found" in e.message:
                logger.warning(
                    f"Tried to edit Telegram message, but message was deleted. args: {args}, kwargs: {kwargs}"
                )
            else:
                raise e

    return decorated


def ignore_reply_to_message_deleted(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except error.BadRequest as e:
            if "Replied message not found" in e.message:
                logger.warning(
                    f"Tried to reply to Telegram message, but message was deleted. args: {args}, kwargs: {kwargs}"
                )
            else:
                raise e

    return decorated
