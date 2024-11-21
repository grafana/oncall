import logging
import time
import typing
import uuid

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
    from apps.user_management.models import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class SlackMessage(models.Model):
    alert_group: typing.Optional["AlertGroup"]

    ALERT_GROUP_UPDATE_DEBOUNCE_INTERVAL_SECONDS = 45

    id = models.CharField(primary_key=True, default=uuid.uuid4, editable=False, max_length=36)

    slack_id = models.CharField(max_length=100)

    # TODO: convert this to a foreign key field to SlackChannel
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

    active_update_task_id = models.CharField(max_length=100, null=True, default=None)
    """
    ID of the latest celery task to update the message
    """

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

    @property
    def permalink(self) -> typing.Optional[str]:
        # Don't send request for permalink if there is no slack_team_identity or slack token has been revoked
        if self.cached_permalink or not self.slack_team_identity or self.slack_team_identity.detected_token_revoked:
            return self.cached_permalink

        try:
            result = SlackClient(self.slack_team_identity).chat_getPermalink(
                channel=self.channel_id, message_ts=self.slack_id
            )
        except SlackAPIError:
            return None

        self.cached_permalink = result["permalink"]
        self.save(update_fields=["cached_permalink"])

        return self.cached_permalink

    @property
    def deep_link(self) -> str:
        return f"https://slack.com/app_redirect?channel={self.channel_id}&team={self.slack_team_identity.slack_id}&message={self.slack_id}"

    def send_slack_notification(
        self,
        user: "User",
        alert_group: "AlertGroup",
        notification_policy: "UserNotificationPolicy",
    ) -> None:
        from apps.base.models import UserNotificationPolicyLogRecord

        slack_message = alert_group.slack_message
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
        sc = SlackClient(self.slack_team_identity, enable_ratelimit_retry=True)
        channel_id = slack_message.channel_id

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
                organization=self.organization,
                _slack_team_identity=self.slack_team_identity,
                channel_id=channel_id,
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

    def update_alert_groups_message(self) -> None:
        """
        Schedule an update task for the associated alert group's Slack message, respecting the debounce interval.

        This method ensures that updates to the Slack message related to an alert group are not performed
        too frequently, adhering to the `ALERT_GROUP_UPDATE_DEBOUNCE_INTERVAL_SECONDS` debounce interval.
        It schedules a background task to update the message after the appropriate countdown.

        The method performs the following steps:
        - Checks if there's already an active update task (`active_update_task_id` is set). If so, exits to prevent
        duplicate scheduling.
        - Calculates the time since the last update (`last_updated` field) and determines the remaining time needed
        to respect the debounce interval.
        - Schedules the `update_alert_group_slack_message` task with the calculated countdown.
        - Stores the task ID in `active_update_task_id` to prevent multiple tasks from being scheduled.
        """

        if not self.alert_group:
            logger.warning(
                f"skipping update_alert_groups_message as SlackMessage {self.pk} has no alert_group associated with it"
            )
            return
        elif self.active_update_task_id:
            logger.info(
                f"skipping update_alert_groups_message as SlackMessage {self.pk} has an active update task {self.active_update_task_id}"
            )
            return

        now = timezone.now()

        # we previously weren't updating the last_updated field for messages, so there will be cases
        # where the last_updated field is None
        last_updated = self.last_updated or now

        time_since_last_update = (now - last_updated).total_seconds()
        remaining_time = self.ALERT_GROUP_UPDATE_DEBOUNCE_INTERVAL_SECONDS - time_since_last_update
        countdown = max(remaining_time, 10)

        logger.info(
            f"updating message for alert_group {self.alert_group.pk} in {countdown} seconds "
            f"(debounce interval: {self.ALERT_GROUP_UPDATE_DEBOUNCE_INTERVAL_SECONDS})"
        )

        active_update_task_id = update_alert_group_slack_message.apply_async((self.pk,), countdown=countdown)
        self.active_update_task_id = active_update_task_id
        self.save(update_fields=["active_update_task_id"])
