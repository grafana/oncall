from apps.telegram.client import TelegramClient
from apps.telegram.models import TelegramChannelVerificationCode, TelegramToOrganizationConnector
from apps.telegram.updates.update_handlers import UpdateHandler
from apps.telegram.utils import is_verification_message

TELEGRAM_ID = 777000

VERIFICATION_FAILED_BOT_NOT_IN_CHANNEL = """Verification failed!
Please add the Grafana OnCall bot to the "{channel_name}" channel as admin and allow it to post messages."""
VERIFICATION_FAILED_SIGN_MESSAGES_NOT_ENABLED = """Verification failed!
Please enable "Sign messages" in channel settings, otherwise Grafana OnCall bot will not be able to operate properly."""
VERIFICATION_FAILED_DISCUSSION_GROUP_ALREADY_REGISTERED = """Verification failed!
The associated discussion group has already been registered with a different channel."""

CHANNEL_CONNECTED_TEXT = "Done! This channel is now linked to organization <b>{organization_title} 🎉</b>"
RELINK_CHANNEL_TEXT = """This Telegram channel is already connected to organization <b>{organization_title}</b>.
Please unlink Telegram channel in settings of organization <b>{organization_title}</b> or contact Grafana OnCall support"""
WRONG_VERIFICATION_CODE = "Verification failed: wrong verification code"


class ChannelVerificationCodeHandler(UpdateHandler):
    def matches(self) -> bool:
        is_message = self.update.message is not None and self.update.message.text is not None

        if not is_message:
            return False

        is_from_discussion_group = self.update.message.chat.type == "supergroup"
        is_forwarded_by_telegram = self.update.effective_user.id == TELEGRAM_ID

        return (
            is_verification_message(self.update.message.text) and is_from_discussion_group and is_forwarded_by_telegram
        )

    def process_update(self) -> None:
        telegram_client = TelegramClient()

        channel_chat_id = self.update.message.forward_from_chat.id
        channel_name = self.update.message.forward_from_chat.title
        discussion_group_chat_id = self.update.message.chat.id
        discussion_group_name = self.update.message.chat.title
        verification_code = self.update.message.text

        # check if bot is in channel
        if not telegram_client.is_chat_member(chat_id=channel_chat_id):
            telegram_client.send_raw_message(
                chat_id=self.update.message.chat.id,
                text=VERIFICATION_FAILED_BOT_NOT_IN_CHANNEL.format(channel_name=channel_name),
                reply_to_message_id=self.update.message.message_id,
            )
            return

        # check if "Sign messages" is enabled
        if self.update.message.forward_signature is None:
            telegram_client.send_raw_message(
                chat_id=self.update.message.chat.id,
                text=VERIFICATION_FAILED_SIGN_MESSAGES_NOT_ENABLED,
                reply_to_message_id=self.update.message.message_id,
            )
            return

        # check discussion group chat is not reused
        connector = TelegramToOrganizationConnector.objects.filter(
            discussion_group_chat_id=discussion_group_chat_id
        ).first()
        if connector is not None and connector.channel_chat_id != channel_chat_id:
            # discussion group is already connected to a different channel chat
            telegram_client.send_raw_message(
                chat_id=self.update.message.chat.id,
                text=VERIFICATION_FAILED_DISCUSSION_GROUP_ALREADY_REGISTERED,
                reply_to_message_id=self.update.message.message_id,
            )
            return

        connector, created = TelegramChannelVerificationCode.verify_channel_and_discussion_group(
            verification_code=verification_code,
            channel_chat_id=channel_chat_id,
            channel_name=channel_name,
            discussion_group_chat_id=discussion_group_chat_id,
            discussion_group_name=discussion_group_name,
        )

        if created:
            reply_text = CHANNEL_CONNECTED_TEXT.format(organization_title=connector.organization.org_title)
        else:
            if connector is not None:
                reply_text = RELINK_CHANNEL_TEXT.format(organization_title=connector.organization.org_title)
            else:
                reply_text = WRONG_VERIFICATION_CODE

        telegram_client.send_raw_message(chat_id=channel_chat_id, text=reply_text)
