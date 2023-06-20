import logging

import humanize
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.functional import cached_property
from rest_framework.fields import DateTimeField

from apps.alerts.tasks import send_update_log_report_signal
from apps.alerts.utils import render_relative_timeline
from apps.base.messaging import get_messaging_backend_from_id
from apps.base.models import UserNotificationPolicy
from apps.base.models.user_notification_policy import validate_channel_choice
from apps.slack.slack_formatter import SlackFormatter
from common.utils import clean_markup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class UserNotificationPolicyLogRecord(models.Model):
    (
        TYPE_PERSONAL_NOTIFICATION_TRIGGERED,
        TYPE_PERSONAL_NOTIFICATION_FINISHED,
        TYPE_PERSONAL_NOTIFICATION_SUCCESS,
        TYPE_PERSONAL_NOTIFICATION_FAILED,
    ) = range(4)

    TYPE_TO_HANDLERS_MAP = {
        TYPE_PERSONAL_NOTIFICATION_TRIGGERED: "triggered",
        TYPE_PERSONAL_NOTIFICATION_FINISHED: "finished",
        TYPE_PERSONAL_NOTIFICATION_SUCCESS: "success",
        TYPE_PERSONAL_NOTIFICATION_FAILED: "failed",
    }

    TYPE_CHOICES = (
        (TYPE_PERSONAL_NOTIFICATION_TRIGGERED, "Personal notification triggered"),
        (TYPE_PERSONAL_NOTIFICATION_FINISHED, "Personal notification finished"),
        (TYPE_PERSONAL_NOTIFICATION_SUCCESS, "Personal notification success"),
        (TYPE_PERSONAL_NOTIFICATION_FAILED, "Personal notification failed"),
    )

    (
        ERROR_NOTIFICATION_NOT_ABLE_TO_SEND_SMS,
        ERROR_NOTIFICATION_SMS_LIMIT_EXCEEDED,
        ERROR_NOTIFICATION_NOT_ABLE_TO_CALL,
        ERROR_NOTIFICATION_PHONE_CALLS_LIMIT_EXCEEDED,
        ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED,
        ERROR_NOTIFICATION_NOT_ABLE_TO_SEND_MAIL,
        ERROR_NOTIFICATION_MAIL_LIMIT_EXCEEDED,  # todo: manage backend specific limits in messaging backend
        ERROR_NOTIFICATION_EMAIL_IS_NOT_VERIFIED,  # deprecated
        ERROR_NOTIFICATION_TELEGRAM_IS_NOT_LINKED_TO_SLACK_ACC,
        ERROR_NOTIFICATION_PHONE_CALL_LINE_BUSY,
        ERROR_NOTIFICATION_PHONE_CALL_FAILED,
        ERROR_NOTIFICATION_PHONE_CALL_NO_ANSWER,
        ERROR_NOTIFICATION_SMS_DELIVERY_FAILED,
        ERROR_NOTIFICATION_MAIL_DELIVERY_FAILED,  # deprecated
        ERROR_NOTIFICATION_TELEGRAM_BOT_IS_DELETED,
        ERROR_NOTIFICATION_POSTING_TO_SLACK_IS_DISABLED,
        ERROR_NOTIFICATION_POSTING_TO_TELEGRAM_IS_DISABLED,  # deprecated
        ERROR_NOTIFICATION_IN_SLACK,
        ERROR_NOTIFICATION_IN_SLACK_TOKEN_ERROR,
        ERROR_NOTIFICATION_IN_SLACK_USER_NOT_IN_SLACK,
        ERROR_NOTIFICATION_IN_SLACK_USER_NOT_IN_CHANNEL,
        ERROR_NOTIFICATION_TELEGRAM_TOKEN_ERROR,
        ERROR_NOTIFICATION_IN_SLACK_CHANNEL_IS_ARCHIVED,
        ERROR_NOTIFICATION_IN_SLACK_RATELIMIT,
        ERROR_NOTIFICATION_MESSAGING_BACKEND_ERROR,
        ERROR_NOTIFICATION_FORBIDDEN,
        ERROR_NOTIFICATION_TELEGRAM_USER_IS_DEACTIVATED,
    ) = range(27)

    # for this errors we want to send message to general log channel
    ERRORS_TO_SEND_IN_SLACK_CHANNEL = [
        ERROR_NOTIFICATION_SMS_LIMIT_EXCEEDED,
        ERROR_NOTIFICATION_PHONE_CALLS_LIMIT_EXCEEDED,
        ERROR_NOTIFICATION_MAIL_LIMIT_EXCEEDED,
        ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED,
    ]

    type = models.IntegerField(choices=TYPE_CHOICES)
    author = models.ForeignKey(
        "user_management.User",
        on_delete=models.SET_NULL,
        related_name="personal_log_records",
        default=None,
        null=True,
    )

    # TODO: soft delete notifications_policies -> change SET_NULL to Protect

    notification_policy = models.ForeignKey(
        "base.UserNotificationPolicy", on_delete=models.SET_NULL, related_name="personal_log_records", null=True
    )

    alert_group = models.ForeignKey(
        "alerts.AlertGroup",
        on_delete=models.CASCADE,
        related_name="personal_log_records",
    )

    slack_prevent_posting = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    reason = models.TextField(null=True, default=None)

    notification_error_code = models.PositiveIntegerField(null=True, default=None)
    notification_step = models.IntegerField(choices=UserNotificationPolicy.Step.choices, null=True, default=None)
    notification_channel = models.IntegerField(validators=[validate_channel_choice], null=True, default=None)

    def rendered_notification_log_line(self, for_slack=False, html=False):
        timeline = render_relative_timeline(self.created_at, self.alert_group.started_at)

        if html:
            result = f"<b>{timeline}:</b> "
        else:
            result = f"*{timeline}:* "

        result += self.render_log_line_action(for_slack=for_slack)
        return result

    @cached_property
    def rendered_notification_log_line_json(self):
        time = humanize.naturaldelta(self.alert_group.started_at - self.created_at)
        created_at = DateTimeField().to_representation(self.created_at)
        author = self.author.short() if self.author is not None else None

        sf = SlackFormatter(self.alert_group.channel.organization)
        action = sf.format(self.render_log_line_action(substitute_author_with_tag=True))
        action = clean_markup(action)

        result = {
            "time": time,
            "action": action,
            "realm": "user_notification",
            "type": self.type,
            "created_at": created_at,
            "author": author,
        }
        return result

    def render_log_line_action(self, for_slack=False, substitute_author_with_tag=False):
        result = ""

        if self.notification_step is not None:
            notification_step = self.notification_step
        elif self.notification_policy is not None:
            notification_step = self.notification_policy.step
        else:
            notification_step = None

        if self.notification_channel is not None:
            notification_channel = self.notification_channel
        elif self.notification_policy is not None:
            notification_channel = self.notification_policy.notify_by
        else:
            notification_channel = None

        if substitute_author_with_tag:
            user_verbal = "{{author}}"
        elif for_slack:
            user_verbal = self.author.get_username_with_slack_verbal()
        else:
            user_verbal = self.author.username

        if self.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS:
            if notification_channel == UserNotificationPolicy.NotificationChannel.SMS:
                result += f"SMS to {user_verbal} was delivered successfully"
            elif notification_channel == UserNotificationPolicy.NotificationChannel.PHONE_CALL:
                result += f"phone call to {user_verbal} was successful"
            elif notification_channel is None:
                result += f"notification to {user_verbal} was delivered successfully"
        elif self.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED:
            if self.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_LIMIT_EXCEEDED:
                result += f"attempt to send an SMS to {user_verbal} has been failed due to a plan limit"
            elif (
                self.notification_error_code
                == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALLS_LIMIT_EXCEEDED
            ):
                result += f"attempt to call to {user_verbal} has been failed due to a plan limit"
            # todo: manage backend specific limits in messaging backend
            elif self.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_MAIL_LIMIT_EXCEEDED:
                result += f"failed to send email to {user_verbal}. Exceeded limit for mails"
            elif (
                self.notification_error_code
                == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_NUMBER_IS_NOT_VERIFIED
            ):
                if notification_channel == UserNotificationPolicy.NotificationChannel.SMS:
                    result += f"failed to send an SMS to {user_verbal}. Phone number is not verified"
                elif notification_channel == UserNotificationPolicy.NotificationChannel.PHONE_CALL:
                    result += f"failed to call to {user_verbal}. Phone number is not verified"
                elif notification_channel is None:
                    result += f"failed to notify {user_verbal}. Phone number is not verified"
            if self.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_SEND_SMS:
                result += f"OnCall was not able to send an SMS to {user_verbal}"
            elif self.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_NOT_ABLE_TO_CALL:
                result += f"OnCall was not able to call to {user_verbal}"
            elif (
                self.notification_error_code
                == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_POSTING_TO_SLACK_IS_DISABLED
            ):
                result += f"failed to notify {user_verbal} in Slack, because the incident is not posted to Slack (reason: Slack is disabled for the route)"
            elif (
                self.notification_error_code
                == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_POSTING_TO_TELEGRAM_IS_DISABLED
            ):
                # deprecated
                result += f"failed to notify {user_verbal} in Telegram, because the incident is not posted to Telegram (reason: Telegram is disabled for the route)"
            elif (
                self.notification_error_code
                == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_IS_NOT_LINKED_TO_SLACK_ACC
            ):
                result += f"failed to send telegram message to {user_verbal}, because user doesn't have a Telegram account linked"
            elif (
                self.notification_error_code
                == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_BOT_IS_DELETED
            ):
                result += f"failed to send telegram message to {user_verbal}, because user deleted/stopped the bot"
            elif (
                self.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_TOKEN_ERROR
            ):
                result += f"failed to send telegram message to {user_verbal} due to invalid Telegram token"
            elif (
                self.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALL_LINE_BUSY
            ):
                result += f"phone call to {user_verbal} failed, because the line was busy"
            elif self.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALL_FAILED:
                result += f"phone call to {user_verbal} failed, most likely because the phone number was non-existent"
            elif (
                self.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_PHONE_CALL_NO_ANSWER
            ):
                result += f"phone call to {user_verbal} ended without being answered"
            elif self.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_SMS_DELIVERY_FAILED:
                result += f"SMS {user_verbal} was not delivered"
            elif self.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK:
                result += f"failed to notify {user_verbal} in Slack"
            elif (
                self.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_TOKEN_ERROR
            ):
                result += f"failed to notify {user_verbal} in Slack, because Slack Integration is not installed"
            elif (
                self.notification_error_code
                == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_USER_NOT_IN_SLACK
            ):
                result += f"failed to notify {user_verbal} in Slack, because {user_verbal} is not in Slack"
            elif (
                self.notification_error_code
                == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_USER_NOT_IN_CHANNEL
            ):
                result += f"failed to notify {user_verbal} in Slack, because {user_verbal} is not in channel"
            elif (
                self.notification_error_code
                == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_CHANNEL_IS_ARCHIVED
            ):
                result += f"failed to notify {user_verbal} in Slack, because channel is archived"
            elif self.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_RATELIMIT:
                result += f"failed to notify {user_verbal} in Slack due to Slack rate limit"
            elif self.notification_error_code == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_FORBIDDEN:
                result += f"failed to notify {user_verbal}, not allowed"
            elif (
                self.notification_error_code
                == UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_TELEGRAM_USER_IS_DEACTIVATED
            ):
                result += f"failed to send telegram message to {user_verbal} because user has been deactivated"
            else:
                # TODO: handle specific backend errors
                try:
                    backend_id = UserNotificationPolicy.NotificationChannel(notification_channel).name
                    backend = get_messaging_backend_from_id(backend_id)
                except ValueError:
                    backend = None
                result += (
                    f"failed to notify {user_verbal} by {backend.label.lower() if backend else 'disabled backend'}"
                )
        elif self.type == UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_TRIGGERED:
            if notification_step == UserNotificationPolicy.Step.NOTIFY:
                if notification_channel == UserNotificationPolicy.NotificationChannel.SLACK:
                    result += f"invited {user_verbal} in Slack"
                elif notification_channel == UserNotificationPolicy.NotificationChannel.SMS:
                    result += f"sent sms to {user_verbal}"
                elif notification_channel == UserNotificationPolicy.NotificationChannel.PHONE_CALL:
                    result += f"called {user_verbal} by phone"
                elif notification_channel == UserNotificationPolicy.NotificationChannel.TELEGRAM:
                    result += f"sent telegram message to {user_verbal}"
                elif notification_channel is None:
                    result += f"invited {user_verbal} but notification channel is unspecified"
                else:
                    try:
                        backend_id = UserNotificationPolicy.NotificationChannel(notification_channel).name
                        backend = get_messaging_backend_from_id(backend_id)
                    except ValueError:
                        backend = None
                    result += f"sent {backend.label.lower() if backend else ''} message to {user_verbal}"
            elif notification_step is None:
                result += f"escalation triggered for {user_verbal}"
        return result


@receiver(post_save, sender=UserNotificationPolicyLogRecord)
def listen_for_usernotificationpolicylogrecord_model_save(sender, instance, created, *args, **kwargs):
    alert_group_pk = instance.alert_group.pk
    if instance.type != UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FINISHED:
        logger.debug(
            f"send_update_log_report_signal for alert_group {alert_group_pk}, "
            f"user notification event: {instance.get_type_display()}"
        )
        send_update_log_report_signal.apply_async(kwargs={"alert_group_pk": alert_group_pk}, countdown=10)
