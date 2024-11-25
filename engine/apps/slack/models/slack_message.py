import logging
import time
import typing
import uuid

from django.db import models

from apps.slack.client import SlackClient
from apps.slack.constants import BLOCK_SECTION_TEXT_MAX_SIZE
from apps.slack.errors import (
    SlackAPIChannelArchivedError,
    SlackAPIError,
    SlackAPIFetchMembersFailedError,
    SlackAPIMethodNotSupportedForChannelTypeError,
    SlackAPIRatelimitError,
    SlackAPITokenError,
)

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup
    from apps.base.models import UserNotificationPolicy
    from apps.slack.models import SlackChannel
    from apps.user_management.models import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SlackMessage(models.Model):
    alert_group: typing.Optional["AlertGroup"]
    channel: "SlackChannel"

    id = models.CharField(primary_key=True, default=uuid.uuid4, editable=False, max_length=36)
    slack_id = models.CharField(max_length=100)

    _channel_id = models.CharField(max_length=100, null=True, default=None)
    """
    DEPRECATED/TODO: this is no longer being referenced/set, drop in a separate PR/release
    """

    channel = models.ForeignKey(
        "slack.SlackChannel", on_delete=models.CASCADE, null=True, default=None, related_name="slack_messages"
    )
    """
    TODO: once we've migrated the data in `_channel_id` to this field, set `null=False`
    as we should always have a `channel` associated with a message
    """

    organization = models.ForeignKey(
        "user_management.Organization",
        on_delete=models.CASCADE,
        null=True,
        default=None,
        related_name="slack_message",
    )

    _slack_team_identity = models.ForeignKey(
        "slack.SlackTeamIdentity",
        on_delete=models.PROTECT,
        null=True,
        default=None,
        related_name="slack_message",
        db_column="slack_team_identity",
    )
    """
    DEPRECATED/TODO: drop this field in a separate PR/release

    Instead of using this column we can simply do self.slack_team_identity.organization
    """

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
        return self.organization.slack_team_identity

    @property
    def permalink(self) -> typing.Optional[str]:
        # Don't send request for permalink if slack token has been revoked
        if self.cached_permalink or self.slack_team_identity.detected_token_revoked:
            return self.cached_permalink

        try:
            result = SlackClient(self.slack_team_identity).chat_getPermalink(
                channel=self.channel.slack_id, message_ts=self.slack_id
            )
        except SlackAPIError:
            return None

        self.cached_permalink = result["permalink"]
        self.save(update_fields=["cached_permalink"])

        return self.cached_permalink

    @property
    def deep_link(self) -> str:
        return f"https://slack.com/app_redirect?channel={self.channel.slack_id}&team={self.slack_team_identity.slack_id}&message={self.slack_id}"

    @classmethod
    def send_slack_notification(
        cls, alert_group: "AlertGroup", user: "User", notification_policy: "UserNotificationPolicy"
    ) -> None:
        """
        NOTE: the reason why we pass in `alert_group` as an argument here, as opposed to just doing
        `self.alert_group`, is that it "looks like" we may have a race condition occuring between two celery tasks:
        - one which sends out the initial slack message
        - one which notifies the user (this method) inside of the above slack message's thread

        Still some more investigation needed to confirm this, but for now, we'll pass in the `alert_group` as an argument
        """

        from apps.base.models import UserNotificationPolicyLogRecord

        slack_message = alert_group.slack_message
        slack_channel = slack_message.channel
        organization = alert_group.channel.organization
        channel_id = slack_channel.slack_id

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

        text = text[:BLOCK_SECTION_TEXT_MAX_SIZE]

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

        sc = SlackClient(organization.slack_team_identity, enable_ratelimit_retry=True)

        try:
            result = sc.chat_postMessage(
                channel=channel_id,
                text=text,
                blocks=blocks,
                thread_ts=slack_message.slack_id,
                unfurl_links=True,
            )
        except SlackAPIRatelimitError:
            UserNotificationPolicyLogRecord(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_FAILED,
                notification_policy=notification_policy,
                alert_group=alert_group,
                reason="Slack API rate limit error",
                notification_step=notification_policy.step,
                notification_channel=notification_policy.notify_by,
                notification_error_code=UserNotificationPolicyLogRecord.ERROR_NOTIFICATION_IN_SLACK_RATELIMIT,
            ).save()
            return
        except SlackAPITokenError:
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
        except SlackAPIChannelArchivedError:
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
            # TODO: once _channel_id has been fully migrated to channel, remove _channel_id
            # see https://raintank-corp.slack.com/archives/C06K1MQ07GS/p1732555465144099
            alert_group.slack_messages.create(
                slack_id=result["ts"],
                organization=organization,
                _channel_id=slack_channel.slack_id,
                channel=slack_channel,
            )

            # create success record
            UserNotificationPolicyLogRecord.objects.create(
                author=user,
                type=UserNotificationPolicyLogRecord.TYPE_PERSONAL_NOTIFICATION_SUCCESS,
                notification_policy=notification_policy,
                alert_group=alert_group,
                notification_step=notification_policy.step,
                notification_channel=notification_policy.notify_by,
            )

        # Check if escalated user is in channel. Otherwise send notification and request to invite him.
        try:
            if slack_user_identity:
                channel_members = []
                try:
                    channel_members = sc.conversations_members(channel=channel_id)["members"]
                except SlackAPIFetchMembersFailedError:
                    pass

                if slack_user_identity.slack_id not in channel_members:
                    time.sleep(5)  # 2 messages in the same moment are ratelimited by Slack. Dirty hack.
                    slack_user_identity.send_link_to_slack_message(slack_message)
        except (SlackAPITokenError, SlackAPIMethodNotSupportedForChannelTypeError):
            pass
