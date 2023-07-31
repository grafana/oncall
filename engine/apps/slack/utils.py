import typing
from datetime import datetime

from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import SlackAPIException

if typing.TYPE_CHECKING:
    from apps.user_management.models import Organization


def post_message_to_channel(organization: "Organization", channel_id: str, text: str) -> None:
    if organization.slack_team_identity:
        slack_client = SlackClientWithErrorHandling(organization.slack_team_identity.bot_access_token)
        try:
            slack_client.api_call("chat.postMessage", channel=channel_id, text=text)
        except SlackAPIException as e:
            if e.response["error"] == "channel_not_found":
                pass
            else:
                raise e


def format_datetime_to_slack(timestamp: float, format="date_short") -> str:
    fallback = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M (UTC)")
    return f"<!date^{timestamp}^{{{format}}} {{time}}|{fallback}>"


def get_cache_key_update_incident_slack_message(alert_group_pk: str) -> str:
    CACHE_KEY_PREFIX = "update_incident_slack_message"
    return f"{CACHE_KEY_PREFIX}_{alert_group_pk}"


def get_populate_slack_channel_task_id_key(slack_team_identity_id: str) -> str:
    return f"SLACK_CHANNELS_TASK_ID_TEAM_{slack_team_identity_id}"
