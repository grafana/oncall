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
                    self.post_message_to_channel(
                        f"Attempt to send an SMS to {user_verbal_with_mention} has been failed due to a plan limit",
                        alert_group.slack_message.channel_id,
                        color="red",
                    )
                elif (
                    log_record.notification_error_code
                    == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALLS_LIMIT_EXCEEDED
                ):
                    self.post_message_to_channel(
                        f"Attempt to call to {user_verbal_with_mention} has been failed due to a plan limit",
                        alert_group.slack_message.channel_id,
                        color="red",
                    )
                elif (
                    log_record.notification_error_code
                    == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MAIL_LIMIT_EXCEEDED
                ):
                    self.post_message_to_channel(
                        f"Failed to send email to {user_verbal_with_mention}. Exceeded limit for mails",
                        alert_group.slack_message.channel_id,
                        color="red",
                    )
                elif (
                    log_record.notification_error_code
                    == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED
                ):
                    if log_record.notification_channel == UserNotificationPolicy.NotificationChannel.SMS:
                        self.post_message_to_channel(
                            f"Failed to send an SMS to {user_verbal_with_mention}. Phone number is not verified",
                            alert_group.slack_message.channel_id,
                            color="red",
                        )
                    elif log_record.notification_channel == UserNotificationPolicy.NotificationChannel.PHONE_CALL:
                        self.post_message_to_channel(
                            f"Failed to call to {user_verbal_with_mention}. Phone number is not verified",
                            alert_group.slack_message.channel_id,
                            color="red",
                        )

    def post_message_to_channel(self, text, channel, color=None, footer=None):
        color_id = self.get_color_id(color)
        attachments = [
            {"color": color_id, "callback_id": "alert", "footer": footer, "text": text},
        ]
        try:
            # TODO: slack-onprem, check exceptions
            self._slack_client.api_call(
                "chat.postMessage",
                channel=channel,
                attachments=attachments,
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

    def get_color_id(self, color):
        if color == "red":
            color_id = "#FF0000"
        elif color == "yellow":
            color_id = "#c6c000"
        else:
            color_id = color
        return color_id
