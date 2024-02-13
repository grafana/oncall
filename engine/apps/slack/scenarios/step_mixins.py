import json
import logging

from apps.alerts.models import AlertGroup
from apps.api.permissions import user_is_authorized
from apps.slack.models import SlackMessage, SlackTeamIdentity
from apps.slack.types import EventPayload

logger = logging.getLogger(__name__)


class AlertGroupActionsMixin:
    """
    Mixin for alert group actions (ack, resolve, etc.). Intended to be used as a mixin along with ScenarioStep.
    """

    def get_alert_group(self, slack_team_identity: SlackTeamIdentity, payload: EventPayload) -> AlertGroup:
        """
        Get AlertGroup instance on Slack message button click or select menu change.
        """

        alert_group = (
            self._get_alert_group_from_action(payload)  # Try to get alert_group_pk from PRESSED button
            or self._get_alert_group_from_message(payload)  # Try to use alert_group_pk from ANY button in message
            or self._get_alert_group_from_slack_message_in_db(slack_team_identity, payload)  # Fetch message from DB
        )
        assert alert_group is not None, "AlertGroup not found"

        # Repair alert group if Slack message is orphaned
        if alert_group.slack_message is None:
            self._repair_alert_group(slack_team_identity, alert_group, payload)

        return alert_group

    def is_authorized(self, alert_group: AlertGroup) -> bool:
        """
        Customize ScenarioStep.is_authorized method to check for alert group permissions.
        """

        return (
            self.user is not None
            and self.user.organization == alert_group.channel.organization
            and user_is_authorized(self.user, self.REQUIRED_PERMISSIONS)
        )

    def _repair_alert_group(
        self, slack_team_identity: SlackTeamIdentity, alert_group: AlertGroup, payload: EventPayload
    ) -> None:
        """
        There's a possibility that OnCall failed to create a SlackMessage instance for an AlertGroup, but the message
        was sent to Slack. This method creates SlackMessage instance for such orphaned messages.
        """

        channel_id = payload["channel"]["id"]
        try:
            message_id = payload["message"]["ts"]
        except KeyError:
            message_id = payload["original_message"]["ts"]

        SlackMessage.objects.create(
            slack_id=message_id,
            organization=alert_group.channel.organization,
            _slack_team_identity=slack_team_identity,
            channel_id=channel_id,
            alert_group=alert_group,
        )

    def _get_alert_group_from_action(self, payload: EventPayload) -> AlertGroup | None:
        """
        Get AlertGroup instance from action data in payload. Action data is data encoded into buttons and select
        menus in apps.alerts.incident_appearance.renderers.slack_renderer.AlertGroupSlackRenderer._get_buttons_blocks.
        """

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
            return None

        # New slack messages from OnCall contain alert group primary key
        try:
            alert_group_ppk = value["alert_group_ppk"]
            return AlertGroup.objects.get(public_primary_key=alert_group_ppk)
        except (KeyError, TypeError):
            pass

        try:
            alert_group_pk = value["alert_group_pk"]
            organization_pk = value["organization_id"]
        except (KeyError, TypeError):
            return None

        try:
            # check organization as well for cases when the organization was migrated from "us" cluster to "eu" and
            # slack message has an outdated payload with incorrect alert group id
            alert_group = AlertGroup.objects.get(pk=alert_group_pk, channel__organization_id=organization_pk)
        except AlertGroup.DoesNotExist:
            return None

        return alert_group

    def _get_alert_group_from_message(self, payload: EventPayload) -> AlertGroup | None:
        """
        Get AlertGroup instance from message data in payload. It's similar to _get_alert_group_from_action,
        but it tries to get alert_group_pk from ANY button in the message, not just the one that was clicked.
        """

        try:
            # sometimes message is in "original_message" field, not "message"
            message = payload.get("message") or payload["original_message"]
            elements = message["attachments"][0]["blocks"][0]["elements"]
        except (KeyError, IndexError):
            return None

        for element in elements:
            value_string = element.get("value")
            if not value_string:
                continue

            try:
                value = json.loads(value_string)
            except (TypeError, json.JSONDecodeError):
                continue

            # New slack messages from OnCall contain alert group primary key
            try:
                alert_group_ppk = value["alert_group_ppk"]
                return AlertGroup.objects.get(public_primary_key=alert_group_ppk)
            except (KeyError, TypeError):
                pass

            try:
                alert_group_pk = value["alert_group_pk"]
                organization_pk = value["organization_id"]
            except (KeyError, TypeError):
                continue

            try:
                # check the organization as well for cases organization was migrated from "us" cluster to "eu" and
                # the slack message has an outdated payload with incorrect alert group id
                alert_group = AlertGroup.objects.get(pk=alert_group_pk, channel__organization_id=organization_pk)
            except AlertGroup.DoesNotExist:
                return None

            return alert_group
        return None

    def _get_alert_group_from_slack_message_in_db(
        self, slack_team_identity: SlackTeamIdentity, payload: EventPayload
    ) -> AlertGroup | None:
        """
        Get AlertGroup instance from SlackMessage instance.
        Old messages may not have alert_group_pk encoded into buttons, so we need to query SlackMessage to figure out
        the AlertGroup.
        """

        message_ts = payload.get("message_ts") or payload["container"]["message_ts"]  # interactive message or block
        channel_id = payload["channel"]["id"]

        # All Slack messages from OnCall should have alert_group_pk encoded into buttons, so reaching this point means
        # something probably went wrong.
        logger.warning(f"alert_group_pk not found in payload, fetching SlackMessage from DB. message_ts: {message_ts}")

        # Get SlackMessage from DB
        slack_message = SlackMessage.objects.get(
            slack_id=message_ts,
            _slack_team_identity=slack_team_identity,
            channel_id=channel_id,
        )
        return slack_message.alert_group
