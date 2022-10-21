from apps.telegram.client import TelegramClient
from apps.telegram.updates.update_handlers.update_handler import UpdateHandler

START_TEXT = """Hi!
This is Grafana OnCall notification bot. You can connect your Grafana OnCall account to Telegram on user settings page.
"""


class StartMessageHandler(UpdateHandler):
    def matches(self) -> bool:
        is_message = self.update.message is not None and self.update.message.text is not None

        if not is_message:
            return False

        is_from_private_chat = self.update.message.chat.type == "private"
        is_start_message = self.update.message.text == "/start"

        return is_from_private_chat and is_start_message

    def process_update(self) -> None:
        telegram_client = TelegramClient()
        telegram_client.send_raw_message(chat_id=self.update.effective_user.id, text=START_TEXT)
