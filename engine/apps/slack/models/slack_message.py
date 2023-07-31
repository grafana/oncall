import logging
import time
import typing
import uuid

from django.db import models

from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import (
    SlackAPIChannelArchivedException,
    SlackAPIException,
    SlackAPITokenException,
)

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SlackMessage(models.Model):
    alert_group: typing.Optional["AlertGroup"]

    id = models.CharField(primary_key=True, default=uuid.uuid4, editable=False, max_length=36)

    slack_id = models.CharField(max_length=100)
    channel_id = models.CharField(max_length=100, null=True, default=None)

    organization = models.ForeignKey(
        "user_management.Organization", on_delete=models.CASCADE, null=True, default=None, related_name="slack_message"
    )
    _slack_team_identity = models.ForeignKey(
        "slack.SlackTeamIdentity",
        on_delete=models.PROTECT,
        null=True,
        default=None,
        related_name="slack_message",
        db_column="slack_team_identity",
    )

    ack_reminder_message_ts = models.CharField(max_length=100, null=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)

    cached_permalink = models.URLField(max_length=250, null=True, default=None)

    last_updated = models.DateTimeField(null=True, default=None)

    alert_group = models.ForeignKey(
        "alerts.AlertGroup",
        on_delete=models.CASCADE,
        null=True,
        default=None,
        related_name="slack_messages",
    )

    # ID of a latest celery task to update the message
    active_update_task_id = models.CharField(max_length=100, null=True, default=None)

    class Meta:
        # slack_id is unique within the context of a channel or conversation
        constraints = [
            models.UniqueConstraint(fields=["slack_id", "channel_id", "_slack_team_identity"], name="unique slack_id")
        ]

    @property
    def slack_team_identity(self):
        if self._slack_team_identity is None:
            if self.organization is None:  # strange case when organization is None
                logger.warning(
                    f"SlackMessage (pk: {self.pk}) fields _slack_team_identity and organization is None. "
                    f"It is strange!"
                )
                return None
            self._slack_team_identity = self.organization.slack_team_identity
            self.save()
        return self._slack_team_identity

    def get_alert_group(self) -> "AlertGroup":
        try:
            return self._alert_group
        except SlackMessage._alert_group.RelatedObjectDoesNotExist:
            if self.alert_group:
                self.alert_group.slack_message = self
                self.alert_group.save(update_fields=["slack_message"])
                return self.alert_group
            else:
                raise

    @property
    def permalink(self):
        if self.slack_team_identity is not None and self.cached_permalink is None:
            sc = SlackClientWithErrorHandling(self.slack_team_identity.bot_access_token)
            result = None
            try:
                result = sc.api_call(
                    "chat.getPermalink",
                    channel=self.channel_id,
                    message_ts=self.slack_id,
                )
            except SlackAPIException as e:
                if e.response["error"] == "message_not_found":
                    return "https://slack.com/resources/using-slack/page/404"
                elif e.response["error"] == "channel_not_found":
                    return "https://slack.com/resources/using-slack/page/404"

            if result is not None and result["permalink"] is not None:
                # Reconnect to DB in case we use read-only DB here.
                _self = SlackMessage.objects.get(pk=self.pk)
                _self.cached_permalink = result["permalink"]
                _self.save()
                self.cached_permalink = _self.cached_permalink

        if self.cached_permalink is not None:
            return self.cached_permalink

    def send_slack_notification(self, user, alert_group, notification_policy):
        from apps.base.models import UserNotificationPolicyLogRecord

        slack_message = alert_group.get_slack_message()
        user_verbal = user.get_username_with_slack_verbal(mention=True)

        slack_user_identity = user.slack_user_identity
        if slack_user_identity is None:
            text = "{}\nTried to invite {} to look at the alert group. Unfortunately {} is not in slack.".format(
                alert_group.long_verbose_name, user_verbal, user_verbal
            )

            UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                reason="User is not in Slack",
                notification_step=notification_policy.step,
                notification_channel=notification_policy.notify_by,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_USER_NOT_IN_SLACK,
            ).save()
        else:
            text = "{}\nInviting {} to look at the alert group.".format(alert_group.long_verbose_name, user_verbal)

        blocks = [
            {
                "type": "section",
                "block_id": "alert",
                "text": {
                    "type": "mrkdwn",
                    "text": text,
                },
            }
        ]
        sc = SlackClientWithErrorHandling(self.slack_team_identity.bot_access_token)
        channel_id = slack_message.channel_id

        try:
            result = sc.api_call(
                "chat.postMessage",
                channel=channel_id,
                text=text,
                blocks=blocks,
                thread_ts=slack_message.slack_id,
                unfurl_links=True,
            )
        except SlackAPITokenException as e:
            print(e)
            UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                reason="Slack token error",
                notification_step=notification_policy.step,
                notification_channel=notification_policy.notify_by,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_TOKEN_ERROR,
            ).save()
            return
        except SlackAPIChannelArchivedException as e:
            print(e)
            UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                reason="channel is archived",
                notification_step=notification_policy.step,
                notification_channel=notification_policy.notify_by,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_CHANNEL_IS_ARCHIVED,
            ).save()
            return
        else:
            SlackMessage(
                slack_id=result["ts"],
                organization=self.organization,
                _slack_team_identity=self.slack_team_identity,
                channel_id=channel_id,
                alert_group=alert_group,
            ).save()

        # Check if escalated user is in channel. Otherwise send notification and request to invite him.
        try:
            if slack_user_identity:
                channel_members = []
                try:
                    channel_members = sc.api_call("conversations.members", channel=channel_id)["members"]
                except SlackAPIException as e:
                    if e.response["error"] == "fetch_members_failed":
                        logger.warning(
                            f"Unable to get members from slack conversation: 'fetch_members_failed'. "
                            f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                            f"{e}"
                        )
                    else:
                        raise e

                if slack_user_identity.slack_id not in channel_members:
                    time.sleep(5)  # 2 messages in the same moment are ratelimited by Slack. Dirty hack.
                    slack_user_identity.send_link_to_slack_message(slack_message)
        except SlackAPITokenException as e:
            print(e)
        except SlackAPIException as e:
            if e.response["error"] == "method_not_supported_for_channel_type":
                # It's ok, just a private channel. Passing
                pass
            else:
                raise e
