import typing

from apps.slack.errors import (
    SlackAPIChannelArchivedError,
    SlackAPIChannelNotFoundError,
    SlackAPIInvalidAuthError,
    SlackAPITokenError,
)
from apps.slack.scenarios import scenario_step

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroupLogRecord


class NotificationDeliveryStep(scenario_step.ScenarioStep):
    def process_signal(self, log_record: "AlertGroupLogRecord") -> None:
        from apps.base.models import UserNotificationPolicy, UserNotificationPolicyLogRecord

        user = log_record.author
        alert_group = log_record.alert_group
        slack_channel_id = alert_group.slack_message.channel.slack_id

        user_verbal_with_mention = user.get_username_with_slack_verbal(mention=True)

        # move message generation to UserNotificationPolicyLogRecord
        if log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED:
            if log_record.notification_error_code in UserNotificationPolicyLogRecord.ERRORS_TO_SEND_IN_SLACK_CHANNEL:
                if (
                    log_record.notification_error_code
                    == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_LIMIT_EXCEEDED
                ):
                    self._post_message_to_channel(
                        f"Attempt to send an SMS to {user_verbal_with_mention} has been failed due to a plan limit",
                        slack_channel_id,
                    )
                elif (
                    log_record.notification_error_code
                    == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALLS_LIMIT_EXCEEDED
                ):
                    self._post_message_to_channel(
                        f"Attempt to call to {user_verbal_with_mention} has been failed due to a plan limit",
                        slack_channel_id,
                    )
                elif (
                    log_record.notification_error_code
                    == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MAIL_LIMIT_EXCEEDED
                ):
                    self._post_message_to_channel(
                        f"Failed to send email to {user_verbal_with_mention}. Exceeded limit for mails",
                        slack_channel_id,
                    )
                elif (
                    log_record.notification_error_code
                    == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED
                ):
                    if log_record.notification_channel == UserNotificationPolicy.NotificationChannel.SMS:
                        self._post_message_to_channel(
                            f"Failed to send an SMS to {user_verbal_with_mention}. Phone number is not verified",
                            slack_channel_id,
                        )
                    elif log_record.notification_channel == UserNotificationPolicy.NotificationChannel.PHONE_CALL:
                        self._post_message_to_channel(
                            f"Failed to call to {user_verbal_with_mention}. Phone number is not verified",
                            slack_channel_id,
                        )

    def _post_message_to_channel(self, text: str, channel_id: str) -> None:
        try:
            self._slack_client.chat_postMessage(
                channel=channel_id,
                text=text,
                blocks=[
                    {
                        "type": "section",
                        "block_id": "alert",
                        "text": {
                            "type": "mrkdwn",
                            "text": text,
                        },
                    },
                ],
                unfurl_links=True,
            )
        except (
            SlackAPITokenError,
            SlackAPIChannelNotFoundError,
            SlackAPIChannelArchivedError,
            SlackAPIInvalidAuthError,
        ):
            pass
