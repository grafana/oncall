import logging

import telegram.error
from django.core.management.base import BaseCommand
from telegram.ext import CallbackQueryHandler, Filters, MessageHandler, Updater

from apps.telegram.client import TelegramClient
from apps.telegram.updates.update_manager import UpdateManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def start_telegram_polling():
    telegram_client = TelegramClient()

    telegram_client.delete_webhook()

    updater = Updater(token=telegram_client.token, use_context=True)

    # Register the error handler function with the dispatcher
    updater.dispatcher.add_error_handler(error_handler)

    callback_handler = CallbackQueryHandler(handle_message)

    # register the message handler function with the dispatcher
    updater.dispatcher.add_handler(MessageHandler(Filters.text, handle_message))
    updater.dispatcher.add_handler(callback_handler)

    # start the long polling loop
    updater.start_polling()


def error_handler(update, context):
    try:
        raise context.error
    except telegram.error.Conflict as e:
        logger.warning(f"Tried to getUpdates() using telegram long polling, but conflict exists, got error: {e}")


def handle_message(update, context):
    logger.debug(f"Update from Telegram: {update}")

    UpdateManager.process_update(update)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Starting telegram polling...")
        start_telegram_polling()
