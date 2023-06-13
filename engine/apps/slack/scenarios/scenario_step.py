import importlib
import logging

from apps.slack.alert_group_slack_service import AlertGroupSlackService
from apps.slack.slack_client import SlackClientWithErrorHandling

logger = logging.getLogger(__name__)


PAYLOAD_TYPE_INTERACTIVE_MESSAGE = "interactive_message"
ACTION_TYPE_BUTTON = "button"
ACTION_TYPE_SELECT = "select"

PAYLOAD_TYPE_SLASH_COMMAND = "slash_command"

PAYLOAD_TYPE_EVENT_CALLBACK = "event_callback"
EVENT_TYPE_MESSAGE = "message"
EVENT_TYPE_MESSAGE_CHANNEL = "channel"
EVENT_TYPE_MESSAGE_IM = "im"
# Slack event "user_change" is deprecated in favor of "user_profile_changed".
# Handler for "user_change" is kept for backward compatibility.
EVENT_TYPE_USER_CHANGE = "user_change"
EVENT_TYPE_USER_PROFILE_CHANGED = "user_profile_changed"
EVENT_TYPE_APP_MENTION = "app_mention"
EVENT_TYPE_MEMBER_JOINED_CHANNEL = "member_joined_channel"
EVENT_TYPE_IM_OPEN = "im_open"
EVENT_TYPE_APP_HOME_OPENED = "app_home_opened"
EVENT_TYPE_SUBTEAM_CREATED = "subteam_created"
EVENT_TYPE_SUBTEAM_UPDATED = "subteam_updated"
EVENT_TYPE_SUBTEAM_MEMBERS_CHANGED = "subteam_members_changed"
EVENT_SUBTYPE_MESSAGE_CHANGED = "message_changed"
EVENT_SUBTYPE_MESSAGE_DELETED = "message_deleted"
EVENT_SUBTYPE_BOT_MESSAGE = "bot_message"
EVENT_SUBTYPE_THREAD_BROADCAST = "thread_broadcast"
EVENT_SUBTYPE_FILE_SHARE = "file_share"
EVENT_TYPE_CHANNEL_DELETED = "channel_deleted"
EVENT_TYPE_CHANNEL_CREATED = "channel_created"
EVENT_TYPE_CHANNEL_RENAMED = "channel_rename"
EVENT_TYPE_CHANNEL_ARCHIVED = "channel_archive"
EVENT_TYPE_CHANNEL_UNARCHIVED = "channel_unarchive"

PAYLOAD_TYPE_BLOCK_ACTIONS = "block_actions"
BLOCK_ACTION_TYPE_USERS_SELECT = "users_select"
BLOCK_ACTION_TYPE_BUTTON = "button"
BLOCK_ACTION_TYPE_STATIC_SELECT = "static_select"
BLOCK_ACTION_TYPE_CONVERSATIONS_SELECT = "conversations_select"
BLOCK_ACTION_TYPE_CHANNELS_SELECT = "channels_select"
BLOCK_ACTION_TYPE_OVERFLOW = "overflow"
BLOCK_ACTION_TYPE_DATEPICKER = "datepicker"

PAYLOAD_TYPE_DIALOG_SUBMISSION = "dialog_submission"
PAYLOAD_TYPE_VIEW_SUBMISSION = "view_submission"

PAYLOAD_TYPE_MESSAGE_ACTION = "message_action"

THREAD_MESSAGE_SUBTYPE = "bot_message"


class ScenarioStep(object):
    def __init__(self, slack_team_identity, organization=None, user=None):
        self._slack_client = SlackClientWithErrorHandling(slack_team_identity.bot_access_token)
        self.slack_team_identity = slack_team_identity
        self.organization = organization
        self.user = user

        self.alert_group_slack_service = AlertGroupSlackService(slack_team_identity, self._slack_client)

    def process_scenario(self, user, team, payload):
        pass

    @classmethod
    def routing_uid(cls):
        return cls.__name__

    @classmethod
    def get_step(cls, scenario, step):
        """
        This is a dynamic Step loader to avoid circular dependencies in scenario files
        """
        # Just in case circular dependencies will be an issue again, this may help:
        # https://stackoverflow.com/posts/36442015/revisions
        try:
            module = importlib.import_module("apps.slack.scenarios." + scenario)
            step = getattr(module, step)
            return step
        except ImportError as e:
            raise Exception("Check import spelling! Scenario: {}, Step:{}, Error: {}".format(scenario, step, e))

    def open_warning_window(self, payload, warning_text, title=None):
        if title is None:
            title = ":warning: Warning"
        view = {
            "type": "modal",
            "callback_id": "warning",
            "title": {
                "type": "plain_text",
                "text": title,
            },
            "close": {
                "type": "plain_text",
                "text": "Ok",
                "emoji": True,
            },
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": warning_text,
                    },
                },
            ],
        }
        self._slack_client.api_call(
            "views.open",
            trigger_id=payload["trigger_id"],
            view=view,
        )
