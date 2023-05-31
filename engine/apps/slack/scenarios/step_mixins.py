import json
import logging

from django.core.exceptions import ObjectDoesNotExist

from apps.alerts.models import AlertGroup
from apps.api.permissions import user_is_authorized
from apps.slack.models import SlackMessage

logger = logging.getLogger(__name__)


class AlertGroupActionsMixin:
    """
    Mixin for alert group actions (ack, resolve, etc.). Intended to be used as a mixin along with ScenarioStep.
    It serves two purposes:
        1. Check that user has required permissions to perform an action. Otherwise, send open a warning window.
        2. Provide utility method to get AlertGroup instance from Slack message payload.
    """

    REQUIRED_PERMISSIONS = []

    def get_alert_group(self, slack_team_identity, payload):
        # TODO: comment

        action = payload["actions"][0]
        action_type = action["type"]

        if action_type == "button":
            value_string = action["value"]
        elif action_type == "static_select":
            value_string = action["selected_option"]["value"]
        else:
            raise ValueError(f"Unexpected action type: {action_type}")

        try:
            value = json.loads(value_string)
        except (TypeError, json.JSONDecodeError):
            return self._deprecated_get_alert_group(slack_team_identity, payload)

        try:
            alert_group_pk = value["alert_group_pk"]
        except (KeyError, TypeError):
            return self._deprecated_get_alert_group(slack_team_identity, payload)

        return AlertGroup.all_objects.get(pk=alert_group_pk)

    def _deprecated_get_alert_group(self, slack_team_identity, payload):
        # TODO: comment
        message_ts = payload.get("message_ts") or payload["container"]["message_ts"]  # interactive message or block
        channel_id = payload["channel"]["id"]

        # Get SlackMessage from DB
        try:
            slack_message = SlackMessage.objects.get(
                slack_id=message_ts,
                _slack_team_identity=slack_team_identity,
                channel_id=channel_id,
            )
        except SlackMessage.DoesNotExist:
            logger.error(
                f"Tried to get SlackMessage from message_ts:"
                f"slack_team_identity_id={slack_team_identity.pk},"
                f"message_ts={message_ts}"
            )
            raise

        # Get AlertGroup from SlackMessage
        try:
            return slack_message.get_alert_group()
        except ObjectDoesNotExist:
            logger.error(
                f"Tried to get AlertGroup from SlackMessage:"
                f"slack_team_identity_id={slack_team_identity.pk},"
                f"message_ts={message_ts}"
            )
            raise

    def is_authorized(self, alert_group):
        return self.user.organization == alert_group.channel.organization and user_is_authorized(
            self.user, self.REQUIRED_PERMISSIONS
        )

    def open_unauthorized_warning(self, payload):
        self.open_warning_window(
            payload,
            warning_text="You do not have permission to perform this action. Ask an admin to upgrade your permissions.",
            title="Permission denied",
        )


class CheckAlertIsUnarchivedMixin:
    def check_alert_is_unarchived(self, slack_team_identity, payload, alert_group, warning=True):
        alert_group_is_unarchived = alert_group.started_at.date() > self.organization.archive_alerts_from
        if not alert_group_is_unarchived:
            if warning:
                warning_text = "Action is impossible: the Alert is archived."
                self.open_warning_window(payload, warning_text)
            if not alert_group.resolved or not alert_group.is_archived:
                alert_group.resolve_by_archivation()
        return alert_group_is_unarchived
