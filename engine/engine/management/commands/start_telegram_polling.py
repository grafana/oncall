import logging

import telegram.error
from asgiref.sync import sync_to_async
from django.core.management.base import BaseCommand
from telegram.ext import ApplicationBuilder, CallbackQueryHandler, MessageHandler, filters

from apps.telegram.client import TelegramClient
from apps.telegram.updates.update_manager import UpdateManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def start_telegram_polling():
    telegram_client = TelegramClient()

    telegram_client.delete_webhook()

    application = ApplicationBuilder().token(telegram_client.token).build()

    # Register the error handler function
    application.add_error_handler(error_handler)

    callback_handler = CallbackQueryHandler(handle_message)

    # register the message handler function with the application
    application.add_handler(MessageHandler(filters.TEXT, handle_message))
    application.add_handler(callback_handler)

    # start the long polling loop
    application.run_polling()


def error_handler(update, context):
    try:
        raise context.error
    except telegram.error.Conflict as e:
        logger.warning(f"Tried to getUpdates() using telegram long polling, but conflict exists, got error: {e}")


async def handle_message(update, context):
    logger.debug(f"Update from Telegram: {update}")

    # Django ORM is sync-only; run it in a thread from async context
    await sync_to_async(UpdateManager.process_update)(update)


class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info("Starting telegram polling...")
        start_telegram_polling()

