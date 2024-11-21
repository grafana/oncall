import logging
import typing

from django.core.cache import cache

from apps.slack.client import SlackClient
from apps.slack.errors import (
    SlackAPICantUpdateMessageError,
    SlackAPIChannelArchivedError,
    SlackAPIChannelInactiveError,
    SlackAPIChannelNotFoundError,
    SlackAPIInvalidAuthError,
    SlackAPIMessageNotFoundError,
    SlackAPIRatelimitError,
    SlackAPITokenError,
)

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup
    from apps.slack.models import SlackTeamIdentity

logger = logging.getLogger(__name__)


class AlertGroupSlackService:
    _slack_client: SlackClient

    UPDATE_ALERT_GROUP_DEBOUNCE_INTERVAL_SECONDS = 30
    """
    Time in seconds to wait before allowing the next update to the Alert Group slack message
    """

    def __init__(
        self,
        slack_team_identity: "SlackTeamIdentity",
        slack_client: typing.Optional[SlackClient] = None,
    ):
        self.slack_team_identity = slack_team_identity
        if slack_client is not None:
            self._slack_client = slack_client
        else:
            self._slack_client = SlackClient(slack_team_identity)

    def update_alert_group_slack_message(self, alert_group: "AlertGroup") -> None:
        alert_group_pk = alert_group.pk
        debounce_alert_group_update_cache_key = f"debounce_update_alert_group_slack_message_{alert_group_pk}"

        logger.info(f"Update message for alert_group {alert_group_pk}")

        # Check if the method has been called recently for this alert_group, if so skip to avoid approaching rate limits
        if cache.get(debounce_alert_group_update_cache_key):
            logger.info(f"Skipping update for alert_group {alert_group_pk} due to debounce interval")
            return

        try:
            self._slack_client.chat_update(
                channel=alert_group.slack_message.channel_id,
                ts=alert_group.slack_message.slack_id,
                attachments=alert_group.render_slack_attachments(),
                blocks=alert_group.render_slack_blocks(),
            )

            logger.info(f"Message has been updated for alert_group {alert_group_pk}")
        except SlackAPIRatelimitError as e:
            if not alert_group.channel.is_maintenace_integration:
                if not alert_group.channel.is_rate_limited_in_slack:
                    alert_group.channel.start_send_rate_limit_message_task("Updating", e.retry_after)
                    logger.info(
                        f"Message has not been updated for alert_group {alert_group_pk} due to slack rate limit."
                    )
            else:
                raise
        except (
            SlackAPIMessageNotFoundError,
            SlackAPICantUpdateMessageError,
            SlackAPIChannelInactiveError,
            SlackAPITokenError,
            SlackAPIChannelNotFoundError,
        ):
            pass
        finally:
            # Set the cache key to enforce debounce interval
            cache.set(debounce_alert_group_update_cache_key, True, self.UPDATE_ALERT_GROUP_DEBOUNCE_INTERVAL_SECONDS)

    def publish_message_to_alert_group_thread(
        self, alert_group: "AlertGroup", attachments=None, mrkdwn=True, unfurl_links=True, text=None
    ) -> None:
        # TODO: refactor checking the possibility of sending message to slack
        # do not try to post message to slack if integration is rate limited
        if alert_group.channel.is_rate_limited_in_slack:
            return

        if attachments is None:
            attachments = []

        try:
            result = self._slack_client.chat_postMessage(
                channel=alert_group.slack_message.channel_id,
                text=text,
                attachments=attachments,
                thread_ts=alert_group.slack_message.slack_id,
                mrkdwn=mrkdwn,
                unfurl_links=unfurl_links,
            )
        except (
            SlackAPITokenError,
            SlackAPIChannelArchivedError,
            SlackAPIChannelNotFoundError,
            SlackAPIInvalidAuthError,
        ):
            return

        alert_group.slack_messages.create(
            slack_id=result["ts"],
            organization=alert_group.channel.organization,
            _slack_team_identity=self.slack_team_identity,
            channel_id=alert_group.slack_message.channel_id,
        )
