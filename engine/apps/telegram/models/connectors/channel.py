import logging
import typing

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q
from telegram import error

from apps.alerts.models import AlertGroup
from apps.telegram.client import TelegramClient
from apps.telegram.models import TelegramMessage
from common.insight_log.chatops_insight_logs import ChatOpsEvent, ChatOpsTypePlug, write_chatops_insight_log
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import ChannelFilter


logger = logging.getLogger(__name__)


def generate_public_primary_key_for_telegram_to_at_connector() -> str:
    prefix = "Z"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while TelegramToOrganizationConnector.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="TelegramToOrganizationConnector"
        )
        failure_counter += 1

    return new_public_primary_key


class TelegramToOrganizationConnector(models.Model):
    channel_filter: "RelatedManager['ChannelFilter']"

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_telegram_to_at_connector,
    )
    organization = models.ForeignKey(
        "user_management.Organization",
        on_delete=models.CASCADE,
        related_name="telegram_channel",
    )

    is_default_channel = models.BooleanField(null=True, default=False)

    channel_chat_id = models.CharField(unique=True, max_length=100)
    channel_name = models.CharField(max_length=100, null=True, default=None)

    discussion_group_chat_id = models.CharField(unique=True, max_length=100)
    discussion_group_name = models.CharField(max_length=100, null=True, default=None)

    datetime = models.DateTimeField(auto_now_add=True)

    NUM_GROUPED_ALERTS_IN_COMMENTS = 10

    @property
    def is_configured(self) -> bool:
        return self.channel_chat_id is not None and self.discussion_group_chat_id is not None

    @classmethod
    def get_channel_for_alert_group(cls, alert_group: AlertGroup) -> typing.Optional["TelegramToOrganizationConnector"]:
        # TODO: add custom queryset
        dm_messages_exist = alert_group.telegram_messages.filter(
            ~Q(chat_id__startswith="-")
            & Q(
                message_type__in=(
                    TelegramMessage.PERSONAL_MESSAGE,
                    TelegramMessage.FORMATTING_ERROR,
                )
            ),
        ).exists()

        if dm_messages_exist:
            return None

        default_channel = cls.objects.filter(
            organization=alert_group.channel.organization, is_default_channel=True
        ).first()

        if alert_group.channel_filter is None:
            return default_channel

        if not alert_group.channel_filter.notify_in_telegram:
            return None

        return alert_group.channel_filter.telegram_channel or default_channel

    def make_channel_default(self, author):
        try:
            old_default_channel = TelegramToOrganizationConnector.objects.get(
                organization=self.organization, is_default_channel=True
            )
            old_default_channel.is_default_channel = False
            old_default_channel.save(update_fields=["is_default_channel"])
        except TelegramToOrganizationConnector.DoesNotExist:
            old_default_channel = None

        self.is_default_channel = True
        self.save(update_fields=["is_default_channel"])
        write_chatops_insight_log(
            author=author,
            event_name=ChatOpsEvent.DEFAULT_CHANNEL_CHANGED,
            chatops_type=ChatOpsTypePlug.TELEGRAM.value,
            prev_channel=old_default_channel.channel_name if old_default_channel else None,
            new_channel=self.channel_name,
        )

    def send_alert_group_message(self, alert_group: AlertGroup) -> None:
        telegram_client = TelegramClient()

        try:
            telegram_client.send_message(
                chat_id=self.channel_chat_id, message_type=TelegramMessage.ALERT_GROUP_MESSAGE, alert_group=alert_group
            )
        except error.BadRequest as e:
            if e.message == "Need administrator rights in the channel chat":
                logger.warning(
                    f"Could not send alert group to Telegram channel with id {self.channel_chat_id} "
                    f"due to lack of admin rights. alert_group {alert_group.pk}"
                )
            elif e.message == "Chat not found":
                logger.warning(
                    f"Could not send alert group to Telegram channel with id {self.channel_chat_id} "
                    f"due to 'Chat not found'. alert_group {alert_group.pk}"
                )
            else:
                telegram_client.send_message(
                    chat_id=self.channel_chat_id, message_type=TelegramMessage.FORMATTING_ERROR, alert_group=alert_group
                )
