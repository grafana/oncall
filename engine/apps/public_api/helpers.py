from apps.public_api.constants import VALID_DATE_FOR_DELETE_INCIDENT
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import SlackAPITokenException


def team_has_slack_token_for_deleting(alert_group):
    if alert_group.slack_message and alert_group.slack_message.slack_team_identity:
        sc = SlackClientWithErrorHandling(alert_group.slack_message.slack_team_identity.bot_access_token)
        try:
            sc.api_call(
                "auth.test",
            )
        except SlackAPITokenException:
            return False
    return True


def is_valid_group_creation_date(alert_group):
    return alert_group.started_at.date() > VALID_DATE_FOR_DELETE_INCIDENT
