from django.apps import apps

from apps.slack.scenarios import scenario_step
from apps.slack.slack_client.exceptions import SlackAPIException, SlackAPITokenException


class NotificationDeliveryStep(scenario_step.ScenarioStep):
    def process_signal(self, log_record):
        UserNotificationPolicy = apps.get_model("base", "UserNotificationPolicy")
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")

        user = log_record.author
        alert_group = log_record.alert_group

        user_verbal_with_mention = user.get_user_verbal_for_team_for_slack(mention=True)

        # move message generation to UserNotificationPolicyLogRecord
        if log_record.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED:
            if log_record.notification_error_code in UserNotificationPolicyLogRecord.ERRORS_TO_SEND_IN_SLACK_CHANNEL:
                if (
                    log_record.notification_error_code
                    == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_LIMIT_EXCEEDED
                ):
                    self._post_message_to_channel(
                        f"Attempt to send an SMS to {user_verbal_with_mention} has been failed due to a plan limit",
                        alert_group.slack_message.channel_id,
                    )
                elif (
                    log_record.notification_error_code
                    == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALLS_LIMIT_EXCEEDED
                ):
                    self._post_message_to_channel(
                        f"Attempt to call to {user_verbal_with_mention} has been failed due to a plan limit",
                        alert_group.slack_message.channel_id,
                    )
                elif (
                    log_record.notification_error_code
                    == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MAIL_LIMIT_EXCEEDED
                ):
                    self._post_message_to_channel(
                        f"Failed to send email to {user_verbal_with_mention}. Exceeded limit for mails",
                        alert_group.slack_message.channel_id,
                    )
                elif (
                    log_record.notification_error_code
                    == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED
                ):
                    if log_record.notification_channel == UserNotificationPolicy.NotificationChannel.SMS:
                        self._post_message_to_channel(
                            f"Failed to send an SMS to {user_verbal_with_mention}. Phone number is not verified",
                            alert_group.slack_message.channel_id,
                        )
                    elif log_record.notification_channel == UserNotificationPolicy.NotificationChannel.PHONE_CALL:
                        self._post_message_to_channel(
                            f"Failed to call to {user_verbal_with_mention}. Phone number is not verified",
                            alert_group.slack_message.channel_id,
                        )

    def _post_message_to_channel(self, text, channel):
        blocks = [
            {
                "type": "section",
                "block_id": "alert",
                "text": {
                    "type": "mrkdwn",
                    "text": text,
                },
            },
        ]
        try:
            # TODO: slack-onprem, check exceptions
            self._slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                text=text,
                blocks=blocks,
                unfurl_links=True,
            )
        except SlackAPITokenException as e:
            print(e)
        except SlackAPIException as e:
            if e.response["error"] == "channel_not_found":
                pass
            elif e.response["error"] == "is_archived":
                pass
            elif e.response["error"] == "invalid_auth":
                print(e)
            else:
                raise e
