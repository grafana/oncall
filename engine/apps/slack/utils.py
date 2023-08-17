import enum
import typing
from datetime import datetime

from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import SlackAPIException

if typing.TYPE_CHECKING:
    from apps.user_management.models import Organization


class SlackDateFormat(enum.StrEnum):
    """
    https://api.slack.com/reference/surfaces/formatting#date-formatting
    """

    DATE_NUM = "date_num"
    """
    Displayed as `2014-02-18`. It will include leading zeros before the month and date and is
    probably best for more technical integrations that require a developer-friendly date format.
    """

    DATE = "date"
    """
    Displayed as `February 18th, 2014`. The year will be omitted if the date is less than six months in the past or future.
    """

    DATE_SHORT = "date_short"
    """
    Displayed as `Feb 18, 2014`. The year will be omitted if the date is less than six months in the past or future.
    """

    DATE_LONG = "date_long"
    """
    Displayed as `Tuesday, February 18th, 2014`. The year will be omitted if the date is less than six months in the past or future.
    """

    DATE_PRETTY = "date_pretty"
    """
    Displays the same as `{date}` but uses "yesterday", "today", or "tomorrow" where appropriate.
    """

    DATE_SHORT_PRETTY = "date_short_pretty"
    """
    Displays the same as `{date_short}` but uses "yesterday", "today", or "tomorrow" where appropriate.
    """

    DATE_LONG_PRETTY = "date_long_pretty"
    """
    Displays the same as `{date_long}` but uses "yesterday", "today", or "tomorrow" where appropriate.
    """

    TIME = "time"
    """
    Displayed as `6:39 AM` or `6:39 PM` in 12-hour format. If the client is set to show 24-hour format, it is displayed as `06:39` or `18:39`.
    """

    TIME_SECS = "time_secs"
    """
    Displayed as `6:39:45 AM` `6:39:42 PM` in 12-hour format. In 24-hour format it is displayed as `06:39:45` or `18:39:42`.
    """


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


def _format_datetime_to_slack(timestamp: float, format: str) -> str:
    fallback = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M (UTC)")
    return f"<!date^{int(timestamp)}^{format}|{fallback}>"


def format_datetime_to_slack(timestamp: float, format: SlackDateFormat = SlackDateFormat.DATE_SHORT) -> str:
    """
    See the docs [here](https://api.slack.com/reference/surfaces/formatting#date-formatting) for
    more information
    """
    return _format_datetime_to_slack(timestamp, f"{{{format}}}")


def format_datetime_to_slack_with_time(timestamp: float, format: SlackDateFormat = SlackDateFormat.DATE_SHORT) -> str:
    """
    See the docs [here](https://api.slack.com/reference/surfaces/formatting#date-formatting) for
    more information
    """
    return _format_datetime_to_slack(timestamp, f"{{{format}}} {{time}}")


def get_cache_key_update_incident_slack_message(alert_group_pk: str) -> str:
    CACHE_KEY_PREFIX = "update_incident_slack_message"
    return f"{CACHE_KEY_PREFIX}_{alert_group_pk}"


def get_populate_slack_channel_task_id_key(slack_team_identity_id: str) -> str:
    return f"SLACK_CHANNELS_TASK_ID_TEAM_{slack_team_identity_id}"
