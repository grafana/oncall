import logging

from apps.api.permissions import user_is_authorized
from apps.slack.models import SlackMessage

logger = logging.getLogger(__name__)


class AlertGroupActionsAccessControlMixin:
    """
    Mixin for alert group actions (ack, resolve, etc.). Intended to be used as a mixin along with ScenarioStep.
    It serves two purposes:
        1. Check that user has required permissions to perform an action. Otherwise, send a message to a user ???
        2. Provide utility method to get AlertGroup instance from Slack message payload.
    """

    REQUIRED_PERMISSIONS = []
    ACTION_VERBOSE = ""

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        if self._check_membership():
            return super().process_scenario(slack_user_identity, slack_team_identity, payload)
        else:
            self._send_denied_message(payload)

    def get_alert_group_from_slack_message_payload(self, slack_team_identity, payload):

        message_ts = payload.get("message_ts") or payload["container"]["message_ts"]  # interactive message or block
        channel_id = payload["channel"]["id"]

        try:
            slack_message = SlackMessage.objects.get(
                slack_id=message_ts,
                _slack_team_identity=slack_team_identity,
                channel_id=channel_id,
            )
            alert_group = slack_message.get_alert_group()
        except SlackMessage.DoesNotExist as e:
            logger.error(
                f"Tried to get SlackMessage from message_ts:"
                f"slack_team_identity_id={slack_team_identity.pk},"
                f"message_ts={message_ts}"
            )
            raise e
        except SlackMessage.alert_group.RelatedObjectDoesNotExist as e:
            logger.error(
                f"Tried to get AlertGroup from SlackMessage:"
                f"slack_team_identity_id={slack_team_identity.pk},"
                f"message_ts={message_ts}"
            )
            raise e
        return alert_group

    def _check_membership(self):
        return user_is_authorized(self.user, self.REQUIRED_PERMISSIONS)

    def _send_denied_message(self, payload):
        try:
            thread_ts = payload["message_ts"]
        except KeyError:
            thread_ts = payload["message"]["ts"]

        text = "Attempted to {} by {}, but failed due to a lack of permissions.".format(
            self.ACTION_VERBOSE,
            self.user.get_username_with_slack_verbal(),
        )

        self._slack_client.api_call(
            "chat.postMessage",
            channel=payload["channel"]["id"],
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
            thread_ts=thread_ts,
            unfurl_links=True,
        )


class CheckAlertIsUnarchivedMixin(object):
    REQUIRED_PERMISSIONS = []
    ACTION_VERBOSE = ""

    def check_alert_is_unarchived(self, slack_team_identity, payload, alert_group, warning=True):
        alert_group_is_unarchived = alert_group.started_at.date() > self.organization.archive_alerts_from
        if not alert_group_is_unarchived:
            if warning:
                warning_text = "Action is impossible: the Alert is archived."
                self.open_warning_window(payload, warning_text)
            if not alert_group.resolved or not alert_group.is_archived:
                alert_group.resolve_by_archivation()
        return alert_group_is_unarchived
