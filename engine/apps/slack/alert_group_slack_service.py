import logging
import typing

from apps.slack.constants import SLACK_RATE_LIMIT_DELAY
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import (
    SlackAPIChannelArchivedException,
    SlackAPIException,
    SlackAPIRateLimitException,
    SlackAPITokenException,
)

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup
    from apps.slack.models import SlackTeamIdentity

logger = logging.getLogger(__name__)


class AlertGroupSlackService:
    _slack_client: SlackClientWithErrorHandling

    def __init__(
        self,
        slack_team_identity: "SlackTeamIdentity",
        slack_client: typing.Optional[SlackClientWithErrorHandling] = None,
    ):
        self.slack_team_identity = slack_team_identity
        if slack_client is not None:
            self._slack_client = slack_client
        else:
            self._slack_client = SlackClientWithErrorHandling(slack_team_identity.bot_access_token)

    def update_alert_group_slack_message(self, alert_group: "AlertGroup") -> None:
        from apps.alerts.models import AlertReceiveChannel

        logger.info(f"Update message for alert_group {alert_group.pk}")
        try:
            self._slack_client.api_call(
                "chat.update",
                channel=alert_group.slack_message.channel_id,
                ts=alert_group.slack_message.slack_id,
                attachments=alert_group.render_slack_attachments(),
                blocks=alert_group.render_slack_blocks(),
            )
            logger.info(f"Message has been updated for alert_group {alert_group.pk}")
        except SlackAPIRateLimitException as e:
            if alert_group.channel.integration != AlertReceiveChannel.INTEGRATION_MAINTENANCE:
                if not alert_group.channel.is_rate_limited_in_slack:
                    delay = e.response.get("rate_limit_delay") or SLACK_RATE_LIMIT_DELAY
                    alert_group.channel.start_send_rate_limit_message_task(delay)
                    logger.info(
                        f"Message has not been updated for alert_group {alert_group.pk} due to slack rate limit."
                    )
            else:
                raise e

        except SlackAPIException as e:
            if e.response["error"] == "message_not_found":  # message deleted from channel
                logger.info(f"Skip updating slack message for alert_group {alert_group.pk} due message_not_found")
            elif e.response["error"] == "is_inactive":  # deleted channel error
                logger.info(f"Skip updating slack message for alert_group {alert_group.pk} due to is_inactive")
            elif e.response["error"] == "account_inactive":
                logger.info(f"Skip updating slack message for alert_group {alert_group.pk} due to account_inactive")
            elif e.response["error"] == "channel_not_found":
                logger.info(f"Skip updating slack message for alert_group {alert_group.pk} due to channel_not_found")
            else:
                raise e
        logger.info(f"Finished _update_slack_message for alert_group {alert_group.pk}")

    def publish_message_to_alert_group_thread(
        self, alert_group: "AlertGroup", attachments=[], mrkdwn=True, unfurl_links=True, text=None
    ) -> None:
        # TODO: refactor checking the possibility of sending message to slack
        # do not try to post message to slack if integration is rate limited
        if alert_group.channel.is_rate_limited_in_slack:
            return

        try:
            result = self._slack_client.api_call(
                "chat.postMessage",
                channel=alert_group.slack_message.channel_id,
                text=text,
                attachments=attachments,
                thread_ts=alert_group.slack_message.slack_id,
                mrkdwn=mrkdwn,
                unfurl_links=unfurl_links,
            )
        except SlackAPITokenException as e:
            logger.warning(
                f"Unable to post message to thread in slack. "
                f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                f"{e}"
            )
        except SlackAPIChannelArchivedException:
            logger.warning(
                f"Unable to post message to thread in slack. "
                f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                f"Reason: 'is_archived'"
            )
        except SlackAPIException as e:
            if e.response["error"] == "channel_not_found":  # channel was deleted
                logger.warning(
                    f"Unable to post message to thread in slack. "
                    f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                    f"Reason: 'channel_not_found'"
                )
            elif e.response["error"] == "invalid_auth":
                logger.warning(
                    f"Unable to post message to thread in slack. "
                    f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                    f"Reason: 'invalid_auth'"
                )
            else:
                raise e
        else:
            alert_group.slack_messages.create(
                slack_id=result["ts"],
                channel_id=alert_group.slack_message.channel_id,
                organization=alert_group.channel.organization,
                _slack_team_identity=self.slack_team_identity,
            )
