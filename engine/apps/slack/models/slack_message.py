import logging
import time
import typing
import uuid

from celery import uuid as celery_uuid
from django.core.cache import cache
from django.db import models
from django.utils import timezone

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
from apps.slack.tasks import update_alert_group_slack_message

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup
    from apps.base.models import UserNotificationPolicy
    from apps.slack.models import SlackChannel, SlackTeamIdentity
    from apps.user_management.models import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SlackMessage(models.Model):
    alert_group: typing.Optional["AlertGroup"]
    channel: "SlackChannel"

    ALERT_GROUP_UPDATE_DEBOUNCE_INTERVAL_SECONDS = 45

    id = models.CharField(primary_key=True, default=uuid.uuid4, editable=False, max_length=36)
    slack_id = models.CharField(max_length=100)

    channel = models.ForeignKey(
        "slack.SlackChannel", on_delete=models.CASCADE, null=True, default=None, related_name="slack_messages"
    )
    """
    TODO: set null=False + remove default=None in a subsequent PR/release.
    (a slack message always needs to have a slack channel associated with it)
    """

    _slack_team_identity = models.ForeignKey(
        "slack.SlackTeamIdentity",
        on_delete=models.PROTECT,
        null=True,
        default=None,
        related_name="slack_message",
        db_column="slack_team_identity",
    )
    """
    TODO: rename this from _slack_team_identity to slack_team_identity in a subsequent PR/release

    This involves also updating the Meta.constraints to use the new field name, this may involve
    migrations.RemoveConstraint and migrations.AddConstraint operations, which we need to investigate further...

    Also, set null=False + remove default in a subsequent PR/release (a slack message always needs to have
    a slack team identity associated with it)
    """

    ack_reminder_message_ts = models.CharField(max_length=100, null=True, default=None)

    cached_permalink = models.URLField(max_length=250, null=True, default=None)

    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(null=True, default=None)

    alert_group = models.ForeignKey(
        "alerts.AlertGroup",
        on_delete=models.CASCADE,
        null=True,
        default=None,
        related_name="slack_messages",
    )

    class Meta:
        # slack_id is unique within the context of a channel or conversation
        constraints = [
            models.UniqueConstraint(fields=["slack_id", "channel_id", "_slack_team_identity"], name="unique slack_id")
        ]

    @property
    def slack_team_identity(self) -> "SlackTeamIdentity":
        """
        See TODO note under _slack_team_identity field
        """
        return self._slack_team_identity

    @property
    def permalink(self) -> typing.Optional[str]:
        # Don't send request for permalink if slack token has been revoked
        if self.cached_permalink or self.slack_team_identity.detected_token_revoked:
            return self.cached_permalink

        try:
            result = SlackClient(self.slack_team_identity).chat_getPermalink(
                channel=self.channel.slack_id,
                message_ts=self.slack_id,
            )
        except SlackAPIError:
            return None

        self.cached_permalink = result["permalink"]
        self.save(update_fields=["cached_permalink"])

        return self.cached_permalink

    @property
    def deep_link(self) -> str:
        return f"https://slack.com/app_redirect?channel={self.channel.slack_id}&team={self.slack_team_identity.slack_id}&message={self.slack_id}"

    def send_slack_notification(
        self, user: "User", alert_group: "AlertGroup", notification_policy: "UserNotificationPolicy"
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
        slack_team_identity = self.slack_team_identity
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

        sc = SlackClient(slack_team_identity, enable_ratelimit_retry=True)

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
            alert_group.slack_messages.create(
                slack_id=result["ts"],
                _slack_team_identity=slack_team_identity,
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

    def _get_update_message_cache_key(self) -> str:
        return f"update_alert_group_slack_message_{self.alert_group.pk}"

    def get_active_update_task_id(self) -> typing.Optional[str]:
        return cache.get(self._get_update_message_cache_key(), default=None)

    def set_active_update_task_id(self, task_id: str) -> None:
        """
        NOTE: we store the task ID in the cache for twice the debounce interval to ensure that the task ID is
        EVENTUALLY removed. The background task which updates the message will remove the task ID from the cache, but
        this is a safety measure in case the task fails to run or complete. The task ID would be removed from the cache
        which would then allow the message to be updated again in a subsequent call to this method.
        """
        cache.set(
            self._get_update_message_cache_key(),
            task_id,
            timeout=self.ALERT_GROUP_UPDATE_DEBOUNCE_INTERVAL_SECONDS * 2,
        )

    def mark_active_update_task_as_complete(self) -> None:
        self.last_updated = timezone.now()
        self.save(update_fields=["last_updated"])

        cache.delete(self._get_update_message_cache_key())

    def update_alert_groups_message(self, debounce: bool) -> None:
        """
        Schedule an update task for the associated alert group's Slack message, respecting the debounce interval.

        This method ensures that updates to the Slack message related to an alert group are not performed
        too frequently, adhering to the `ALERT_GROUP_UPDATE_DEBOUNCE_INTERVAL_SECONDS` debounce interval.
        It schedules a background task to update the message after the appropriate countdown.

        The method performs the following steps:
        - Checks if there's already an active update task ID set in the cache. If so, exits to prevent
        duplicate scheduling.
        - Calculates the time since the last update (`last_updated` field) and determines the remaining time needed
        to respect the debounce interval.
        - Schedules the `update_alert_group_slack_message` task with the calculated countdown.
        - Stores the task ID in the cache to prevent multiple tasks from being scheduled.

        debounce: bool - this is intended to be used when we want to debounce updates to the message. Examples:
          - when set to True, we will skip scheduling an update task if there's an active update task (eg. debounce it)
          - when set to False, we will immediately schedule an update task
        """
        if not self.alert_group:
            logger.warning(
                f"skipping update_alert_groups_message as SlackMessage {self.pk} has no alert_group associated with it"
            )
            return

        active_update_task_id = self.get_active_update_task_id()
        if debounce and active_update_task_id is not None:
            logger.info(
                f"skipping update_alert_groups_message as SlackMessage {self.pk} has an active update task "
                f"{active_update_task_id} and debounce is set to True"
            )
            return

        now = timezone.now()

        # we previously weren't updating the last_updated field for messages, so there will be cases
        # where the last_updated field is None
        last_updated = self.last_updated or now

        time_since_last_update = (now - last_updated).total_seconds()
        remaining_time = self.ALERT_GROUP_UPDATE_DEBOUNCE_INTERVAL_SECONDS - int(time_since_last_update)
        countdown = max(remaining_time, 10) if debounce else 0

        logger.info(
            f"updating message for alert_group {self.alert_group.pk} in {countdown} seconds "
            f"(debounce interval: {self.ALERT_GROUP_UPDATE_DEBOUNCE_INTERVAL_SECONDS})"
        )

        task_id = celery_uuid()

        # NOTE: we need to persist the task ID in the cache before scheduling the task to prevent
        # a race condition where the task starts before the task ID is stored in the cache as the task
        # does a check to verify that the celery task id matches the one stored in the cache
        #
        # (see update_alert_group_slack_message task for more details)
        self.set_active_update_task_id(task_id)
        update_alert_group_slack_message.apply_async((self.pk,), countdown=countdown, task_id=task_id)
