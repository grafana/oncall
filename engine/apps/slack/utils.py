from datetime import datetime
from textwrap import wrap

from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import SlackAPIException


def create_message_blocks(text):
    """This function checks text and return blocks

    Maximum length for the text in section is 3000 characters and
    we can include up to 50 blocks in each message.
    https://api.slack.com/reference/block-kit/blocks#section

    :param str text: Text for message blocks
    :return list blocks: Blocks list
    """

    if len(text) <= 3000:
        blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": text}}]
    else:
        splitted_text_list = text.split("```\n")

        if len(splitted_text_list) > 1:
            splitted_text_list.pop()

        blocks = []

        for splitted_text in splitted_text_list:
            if len(splitted_text) > 2996:
                # too long text case
                text_list = wrap(
                    splitted_text, 2994, expand_tabs=False, replace_whitespace=False, break_long_words=False
                )

                blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"{text_list[0]}```"}})

                for text_item in text_list[1:]:
                    blocks.append(
                        {"type": "section", "text": {"type": "mrkdwn", "text": f'```{text_item.strip("```")}```'}}
                    )
            else:
                blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": splitted_text + "```\n"}})

    return blocks


def post_message_to_channel(organization, channel_id, text):
    if organization.slack_team_identity:
        slack_client = SlackClientWithErrorHandling(organization.slack_team_identity.bot_access_token)
        try:
            slack_client.api_call("chat.postMessage", channel=channel_id, text=text)
        except SlackAPIException as e:
            if e.response["error"] == "channel_not_found":
                pass
            else:
                raise e


def format_datetime_to_slack(timestamp, format="date_short"):
    fallback = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M (UTC)")
    return f"<!date^{timestamp}^{{{format}}} {{time}}|{fallback}>"


def get_cache_key_update_incident_slack_message(alert_group_pk):
    CACHE_KEY_PREFIX = "update_incident_slack_message"
    return f"{CACHE_KEY_PREFIX}_{alert_group_pk}"


def get_populate_slack_channel_task_id_key(slack_team_identity_id):
    return f"SLACK_CHANNELS_TASK_ID_TEAM_{slack_team_identity_id}"
