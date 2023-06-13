import telegram
from django.db import models

from apps.alerts.models import AlertGroup


class TelegramMessage(models.Model):
    (
        ALERT_GROUP_MESSAGE,
        ACTIONS_MESSAGE,
        LOG_MESSAGE,
        FORMATTING_ERROR,
        PERSONAL_MESSAGE,
        LINK_TO_CHANNEL_MESSAGE,
        LINK_TO_CHANNEL_MESSAGE_WITHOUT_TITLE,
    ) = range(7)

    TELEGRAM_MESSAGE_CHOICES = (
        (ALERT_GROUP_MESSAGE, "Alert group message"),
        (ACTIONS_MESSAGE, "Actions message"),
        (LOG_MESSAGE, "Log message"),
        (FORMATTING_ERROR, "Alert can not be rendered"),
        (PERSONAL_MESSAGE, "Alert group message with action buttons and alert group log"),
        (LINK_TO_CHANNEL_MESSAGE, "Link to channel message"),
        (LINK_TO_CHANNEL_MESSAGE_WITHOUT_TITLE, "Link to channel message without title"),
    )

    message_id = models.IntegerField()
    chat_id = models.CharField(max_length=100)

    message_type = models.IntegerField(choices=TELEGRAM_MESSAGE_CHOICES)

    discussion_group_message_id = models.IntegerField(null=True, default=None)

    alert_group = models.ForeignKey(
        "alerts.AlertGroup",
        on_delete=models.CASCADE,
        related_name="telegram_messages",
    )

    # field for task debouncing for apps.telegram.tasks.edit_message
    edit_task_id = models.CharField(max_length=100, null=True, default=None)

    @property
    def link(self) -> str:
        chat_slug = self.chat_id[-10:]
        return f"https://t.me/c/{chat_slug}/{self.message_id}?thread={self.message_id}"

    @staticmethod
    def create_from_message(message: telegram.Message, message_type: int, alert_group: AlertGroup) -> "TelegramMessage":
        return TelegramMessage.objects.create(
            message_id=message.message_id, chat_id=message.chat.id, message_type=message_type, alert_group=alert_group
        )
