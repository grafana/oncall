import logging

from apps.api.permissions import user_is_authorized

logger = logging.getLogger(__name__)


class AlertGroupActionsAccessControlMixin:
    """
    Mixin for alert group actions intended to use a mixin along with ScenarioStep
    """

    REQUIRED_PERMISSIONS = []
    ACTION_VERBOSE = ""

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        if self.check_membership():
            return super().process_scenario(slack_user_identity, slack_team_identity, payload)
        else:
            self.send_denied_message(payload)

    def check_membership(self):
        return user_is_authorized(self.user, self.REQUIRED_PERMISSIONS)

    def send_denied_message(self, payload):
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
