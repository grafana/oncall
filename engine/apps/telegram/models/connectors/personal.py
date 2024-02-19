from django.db import models
from telegram import error

from apps.alerts.models import AlertGroup
from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord
from apps.telegram.client import TelegramClient
from apps.telegram.decorators import ignore_reply_to_message_deleted
from apps.telegram.models import TelegramMessage, TelegramToOrganizationConnector
from apps.telegram.tasks import send_link_to_channel_message_or_fallback_to_full_alert_group
from apps.user_management.models import User

ONE_MORE_NOTIFICATION = "One more notification about this 👆"
ALERT_CANT_BE_RENDERED = (
    "You have a new alert group, but Telegram can't render its content! Please check it out: {link}"
)


class TelegramToUserConnector(models.Model):
    user = models.OneToOneField("user_management.User", on_delete=models.CASCADE, related_name="telegram_connection")

    telegram_chat_id = models.BigIntegerField()
    telegram_nick_name = models.CharField(max_length=100, null=True, default=None)
    datetime = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("user", "telegram_chat_id"),)

    @classmethod
    def notify_user(cls, user: User, alert_group: AlertGroup, notification_policy: UserNotificationPolicy) -> None:
        try:
            user_connector = user.telegram_connection
            user_connector.notify(alert_group=alert_group, notification_policy=notification_policy)
        except TelegramToUserConnector.DoesNotExist:
            cls.create_telegram_notification_error(
                alert_group=alert_group,
                user=user,
                notification_policy=notification_policy,
                reason="No linked telegram account",
                error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_IS_NOT_LINKED_TO_SLACK_ACC,
            )

    def notify(self, alert_group: AlertGroup, notification_policy: UserNotificationPolicy) -> None:
        telegram_channel = TelegramToOrganizationConnector.get_channel_for_alert_group(alert_group)

        if telegram_channel is not None:
            # Call this task with a countdown to avoid unnecessary retry when alert group telegram message hasn't been
            # created yet
            send_link_to_channel_message_or_fallback_to_full_alert_group.apply_async(
                kwargs={
                    "alert_group_pk": alert_group.pk,
                    "notification_policy_pk": notification_policy.pk,
                    "user_connector_pk": self.pk,
                },
                countdown=3,
            )
        else:
            self.send_full_alert_group(alert_group=alert_group, notification_policy=notification_policy)

    @staticmethod
    def create_telegram_notification_success(
        alert_group: AlertGroup, user: User, notification_policy: UserNotificationPolicy
    ) -> None:
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS,
            notification_policy=notification_policy,
            alert_group=alert_group,
            notification_step=notification_policy.step if notification_policy else None,
            notification_channel=notification_policy.notify_by if notification_policy else None,
        )

    @staticmethod
    def create_telegram_notification_error(
        alert_group: AlertGroup,
        user: User,
        notification_policy: UserNotificationPolicy,
        error_code: int,
        reason: str | None,
    ) -> None:
        UserNotificationPolicyLogRecord.objects.create(
            author=user,
            type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
            notification_policy=notification_policy,
            alert_group=alert_group,
            notification_error_code=error_code,
            reason=reason,
            notification_step=notification_policy.step if notification_policy else None,
            notification_channel=notification_policy.notify_by if notification_policy else None,
        )

    # send the actual alert group and log to user's DM
    def send_full_alert_group(self, alert_group: AlertGroup, notification_policy: UserNotificationPolicy) -> None:
        try:
            telegram_client = TelegramClient()
        except error.InvalidToken:
            TelegramToUserConnector.create_telegram_notification_error(
                alert_group,
                self.user,
                notification_policy,
                UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_TOKEN_ERROR,
                reason="Invalid token",
            )
            return

        old_alert_group_message = alert_group.telegram_messages.filter(
            chat_id=self.telegram_chat_id,
            message_type__in=[
                TelegramMessage.PERSONAL_MESSAGE,
                TelegramMessage.FORMATTING_ERROR,
            ],
        ).first()

        if old_alert_group_message is None:
            try:
                telegram_client.send_message(
                    chat_id=self.telegram_chat_id,
                    message_type=TelegramMessage.PERSONAL_MESSAGE,
                    alert_group=alert_group,
                )
            except error.BadRequest:
                TelegramToUserConnector.create_telegram_notification_error(
                    alert_group,
                    self.user,
                    notification_policy,
                    UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_FORMATTING_ERROR,
                    reason="Notification sent but there was a formatting error in the rendered template",
                )
                telegram_client.send_message(
                    chat_id=self.telegram_chat_id,
                    message_type=TelegramMessage.FORMATTING_ERROR,
                    alert_group=alert_group,
                )
            except error.Unauthorized as e:
                if e.message == "Forbidden: bot was blocked by the user":
                    TelegramToUserConnector.create_telegram_notification_error(
                        alert_group,
                        self.user,
                        notification_policy,
                        UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_BOT_IS_DELETED,
                        reason="Bot was blocked by the user",
                    )
                elif e.message == "Invalid token":
                    TelegramToUserConnector.create_telegram_notification_error(
                        alert_group,
                        self.user,
                        notification_policy,
                        UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_TOKEN_ERROR,
                        reason="Invalid token",
                    )
                elif e.message == "Forbidden: user is deactivated":
                    TelegramToUserConnector.create_telegram_notification_error(
                        alert_group,
                        self.user,
                        notification_policy,
                        UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_USER_IS_DEACTIVATED,
                        reason="Telegram user was disabled",
                    )
                else:
                    raise e
            else:
                TelegramToUserConnector.create_telegram_notification_success(
                    alert_group, self.user, notification_policy
                )
        else:
            self._nudge_about_alert_group_message(telegram_client, old_alert_group_message)
            TelegramToUserConnector.create_telegram_notification_success(alert_group, self.user, notification_policy)

    # send DM message with the link to the alert group post in channel
    def send_link_to_channel_message(self, alert_group: AlertGroup, notification_policy: UserNotificationPolicy):
        try:
            telegram_client = TelegramClient()
        except error.InvalidToken:
            TelegramToUserConnector.create_telegram_notification_error(
                alert_group,
                self.user,
                notification_policy,
                UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_TOKEN_ERROR,
                reason="Invalid token",
            )
            return

        try:
            telegram_client.send_message(
                chat_id=self.telegram_chat_id,
                message_type=TelegramMessage.LINK_TO_CHANNEL_MESSAGE,
                alert_group=alert_group,
            )
        except error.BadRequest:
            # incorrect format of the title, so do not include it to the link to channel message
            telegram_client.send_message(
                chat_id=self.telegram_chat_id,
                message_type=TelegramMessage.LINK_TO_CHANNEL_MESSAGE_WITHOUT_TITLE,
                alert_group=alert_group,
            )
        except error.Unauthorized as e:
            if e.message == "Forbidden: bot was blocked by the user":
                TelegramToUserConnector.create_telegram_notification_error(
                    alert_group,
                    self.user,
                    notification_policy,
                    UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_BOT_IS_DELETED,
                    reason="Bot was blocked by the user",
                )
            elif e.message == "Invalid token":
                TelegramToUserConnector.create_telegram_notification_error(
                    alert_group,
                    self.user,
                    notification_policy,
                    UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_TOKEN_ERROR,
                    reason="Invalid token",
                )
            elif e.message == "Forbidden: user is deactivated":
                TelegramToUserConnector.create_telegram_notification_error(
                    alert_group,
                    self.user,
                    notification_policy,
                    UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_USER_IS_DEACTIVATED,
                    reason="Telegram user was disabled",
                )
            else:
                raise e
        else:
            TelegramToUserConnector.create_telegram_notification_success(alert_group, self.user, notification_policy)

    @staticmethod
    @ignore_reply_to_message_deleted
    def _nudge_about_alert_group_message(telegram_client: TelegramClient, message: TelegramMessage) -> None:
        """Nudge the user about existing alert group message, without sending the full alert group content again."""
        telegram_client.send_raw_message(
            chat_id=message.chat_id, reply_to_message_id=message.message_id, text=ONE_MORE_NOTIFICATION
        )
