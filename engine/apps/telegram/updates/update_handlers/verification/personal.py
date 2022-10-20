from apps.telegram.client import TelegramClient
from apps.telegram.models import TelegramVerificationCode
from apps.telegram.updates.update_handlers import UpdateHandler
from apps.telegram.utils import is_verification_message

USER_CONNECTED_TEXT = "Done! This Telegram account is now linked to <b>{username}</b> 🎉"
RELINK_ACCOUNT_TEXT = """This user is already connected to a Telegram account.
Please unlink Telegram account in profile settings of user <b>{username}</b> or contact Grafana OnCall support."""
WRONG_VERIFICATION_CODE = "Verification failed: wrong verification code"


class PersonalVerificationCodeHandler(UpdateHandler):
    def matches(self) -> bool:
        is_message = self.update.message is not None and self.update.message.text is not None

        if not is_message:
            return False

        is_from_private_chat = self.update.message.chat.type == "private"

        split_entries = self.update.message.text.split()
        is_deeplink_start = (
            len(split_entries) == 2 and split_entries[0] == "/start" and is_verification_message(split_entries[1])
        )

        return is_from_private_chat and (is_deeplink_start or is_verification_message(self.update.message.text))

    def process_update(self) -> None:
        user = self.update.effective_user
        nickname = user.username or user.first_name or user.last_name or "Unknown"

        text = self.update.message.text
        verification_code = text if is_verification_message(text) else text.split()[1]

        connector, created = TelegramVerificationCode.verify_user(
            verification_code=verification_code, telegram_chat_id=user.id, telegram_nick_name=nickname
        )

        if created:
            reply_text = USER_CONNECTED_TEXT.format(username=connector.user.username)
        elif connector is not None:
            reply_text = RELINK_ACCOUNT_TEXT.format(username=connector.user.username)
        else:
            reply_text = WRONG_VERIFICATION_CODE

        telegram_client = TelegramClient()
        telegram_client.send_raw_message(chat_id=user.id, text=reply_text)
