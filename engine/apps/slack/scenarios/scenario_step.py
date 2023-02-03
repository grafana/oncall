import importlib
import json
import logging

from django.apps import apps
from django.core.cache import cache

from apps.slack.constants import SLACK_RATE_LIMIT_DELAY
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import (
    SlackAPIChannelArchivedException,
    SlackAPIException,
    SlackAPIRateLimitException,
    SlackAPITokenException,
)

logger = logging.getLogger(__name__)


PAYLOAD_TYPE_INTERACTIVE_MESSAGE = "interactive_message"
ACTION_TYPE_BUTTON = "button"
ACTION_TYPE_SELECT = "select"

PAYLOAD_TYPE_SLASH_COMMAND = "slash_command"

PAYLOAD_TYPE_EVENT_CALLBACK = "event_callback"
EVENT_TYPE_MESSAGE = "message"
EVENT_TYPE_MESSAGE_CHANNEL = "channel"
EVENT_TYPE_MESSAGE_IM = "im"
EVENT_TYPE_USER_CHANGE = "user_change"
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

MAX_STATIC_SELECT_OPTIONS = 100


class ScenarioStep(object):

    # Is a delay to prevent intermediate activity by system in case user is doing some multi-step action.
    # For example if user wants to unack and ack we don't need to launch escalation right after unack.
    CROSS_ACTION_DELAY = 10
    SELECT_ORGANIZATION_AND_ROUTE_BLOCK_ID = "SELECT_ORGANIZATION_AND_ROUTE"

    need_to_be_logged = True
    random_prefix_for_routing = ""

    # Some blocks are sending context via action_id, which is limited by 255 chars

    TAG_ONBOARDING = "onboarding"
    TAG_DASHBOARD = "dashboard"
    TAG_SUBSCRIPTION = "subscription"
    TAG_REPORTING = "reporting"

    TAG_TEAM_SETTINGS = "team_settings"

    TAG_TRIGGERED_BY_SYSTEM = "triggered_by_system"
    TAG_INCIDENT_ROUTINE = "incident_routine"
    TAG_INCIDENT_MANAGEMENT = "incident_management"

    TAG_ON_CALL_SCHEDULES = "on_call_schedules"

    tags = []

    def __init__(self, slack_team_identity, organization=None, user=None):
        self._slack_client = SlackClientWithErrorHandling(slack_team_identity.bot_access_token)
        self.slack_team_identity = slack_team_identity
        self.organization = organization
        self.user = user

        cache_tag = "step_tags_populated_{}".format(self.routing_uid())

        if cache.get(cache_tag) is None:
            cache.set(cache_tag, 1, 180)

    def dispatch(self, user, team, payload, action=None):
        return self.process_scenario(user, team, payload, action)

    def process_scenario(self, user, team, payload, action=None):
        pass

    def ts(self, payload):
        if "message_ts" in payload:
            ts = payload["message_ts"]
        elif (
            "view" in payload
            and "private_metadata" in payload["view"]
            and payload["view"]["private_metadata"]
            and "ts" in json.loads(payload["view"]["private_metadata"])
        ):
            ts = json.loads(payload["view"]["private_metadata"])["ts"]
        elif "container" in payload and "message_ts" in payload["container"]:
            ts = payload["container"]["message_ts"]
        elif "state" in payload and "message_ts" in json.loads(payload["state"]):
            ts = json.loads(payload["state"])["message_ts"]
        else:
            ts = "random"
        return ts

    def channel(self, user, payload):
        if "channel" in payload and "id" in payload["channel"]:
            channel = payload["channel"]["id"]
        else:
            channel = user.im_channel_id
        return channel

    @classmethod
    def routing_uid(cls):
        return cls.random_prefix_for_routing + cls.__name__

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

    def process_scenario_from_other_step(
        self, slack_user_identity, slack_team_identity, payload, step_class, action=None, kwargs={}
    ):
        """
        Allows to trigger other step from current step
        """
        step = step_class(slack_team_identity)
        step.process_scenario(slack_user_identity, slack_team_identity, payload, action=action, **kwargs)

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

    def get_alert_group_from_slack_message(self, payload):
        SlackMessage = apps.get_model("slack", "SlackMessage")

        message_ts = payload.get("message_ts") or payload["container"]["message_ts"]  # interactive message or block
        channel_id = payload["channel"]["id"]

        try:
            slack_message = SlackMessage.objects.get(
                slack_id=message_ts,
                _slack_team_identity=self.slack_team_identity,
                channel_id=channel_id,
            )
            alert_group = slack_message.get_alert_group()
        except SlackMessage.DoesNotExist as e:
            print(
                f"Tried to get SlackMessage from message_ts:"
                f"Slack Team Identity pk: {self.slack_team_identity.pk},"
                f"Message ts: {message_ts}"
            )
            raise e
        except SlackMessage.alert.RelatedObjectDoesNotExist as e:
            print(
                f"Tried to get Alert Group from SlackMessage:"
                f"Slack Team Identity pk: {self.slack_team_identity.pk},"
                f"SlackMessage pk: {slack_message.pk}"
            )
            raise e
        return alert_group

    def _update_slack_message(self, alert_group):
        logger.info(f"Started _update_slack_message for alert_group {alert_group.pk}")
        SlackMessage = apps.get_model("slack", "SlackMessage")
        AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")

        slack_message = alert_group.slack_message
        attachments = alert_group.render_slack_attachments()
        blocks = alert_group.render_slack_blocks()
        logger.info(f"Update message for alert_group {alert_group.pk}")
        try:
            self._slack_client.api_call(
                "chat.update",
                channel=slack_message.channel_id,
                ts=slack_message.slack_id,
                attachments=attachments,
                blocks=blocks,
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
            if e.response["error"] == "message_not_found":
                logger.info(f"message_not_found for alert_group {alert_group.pk}, trying to post new message")
                result = self._slack_client.api_call(
                    "chat.postMessage", channel=slack_message.channel_id, attachments=attachments, blocks=blocks
                )
                slack_message_updated = SlackMessage(
                    slack_id=result["ts"],
                    organization=slack_message.organization,
                    _slack_team_identity=slack_message.slack_team_identity,
                    channel_id=slack_message.channel_id,
                    alert_group=alert_group,
                )
                slack_message_updated.save()
                alert_group.slack_message = slack_message_updated
                alert_group.save(update_fields=["slack_message"])
                logger.info(f"Message has been posted for alert_group {alert_group.pk}")
            elif e.response["error"] == "is_inactive":  # deleted channel error
                logger.info(f"Skip updating slack message for alert_group {alert_group.pk} due to is_inactive")
            elif e.response["error"] == "account_inactive":
                logger.info(f"Skip updating slack message for alert_group {alert_group.pk} due to account_inactive")
            elif e.response["error"] == "channel_not_found":
                logger.info(f"Skip updating slack message for alert_group {alert_group.pk} due to channel_not_found")
            else:
                raise e
        logger.info(f"Finished _update_slack_message for alert_group {alert_group.pk}")

    def publish_message_to_thread(self, alert_group, attachments=[], mrkdwn=True, unfurl_links=True, text=None):
        # TODO: refactor checking the possibility of sending message to slack
        # do not try to post message to slack if integration is rate limited
        if alert_group.channel.is_rate_limited_in_slack:
            return

        SlackMessage = apps.get_model("slack", "SlackMessage")
        slack_message = alert_group.get_slack_message()
        channel_id = slack_message.channel_id
        try:
            result = self._slack_client.api_call(
                "chat.postMessage",
                channel=channel_id,
                text=text,
                attachments=attachments,
                thread_ts=slack_message.slack_id,
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
            SlackMessage(
                slack_id=result["ts"],
                organization=alert_group.channel.organization,
                _slack_team_identity=self.slack_team_identity,
                channel_id=channel_id,
                alert_group=alert_group,
            ).save()

    def get_select_user_element(
        self, action_id, multi_select=False, initial_user=None, initial_users_list=None, text=None
    ):
        if not text:
            text = f"Select User{'' if not multi_select else 's'}"
        element = {
            "action_id": action_id,
            "type": "static_select" if not multi_select else "multi_static_select",
            "placeholder": {
                "type": "plain_text",
                "text": text,
                "emoji": True,
            },
        }

        users = self.organization.users.all().select_related("slack_user_identity")

        users_count = users.count()
        options = []

        for user in users:
            user_verbal = f"{user.get_user_verbal_for_team_for_slack()}"
            if len(user_verbal) > 75:
                user_verbal = user_verbal[:72] + "..."
            option = {"text": {"type": "plain_text", "text": user_verbal}, "value": json.dumps({"user_id": user.pk})}
            options.append(option)

        if users_count > MAX_STATIC_SELECT_OPTIONS:
            option_groups = []
            option_groups_chunks = [
                options[x : x + MAX_STATIC_SELECT_OPTIONS] for x in range(0, len(options), MAX_STATIC_SELECT_OPTIONS)
            ]
            for option_group in option_groups_chunks:
                option_group = {"label": {"type": "plain_text", "text": " "}, "options": option_group}
                option_groups.append(option_group)
            element["option_groups"] = option_groups
        elif users_count == 0:  # strange case when there are no users to select
            option = {
                "text": {"type": "plain_text", "text": "No users to select"},
                "value": json.dumps({"user_id": None}),
            }
            options.append(option)
            element["options"] = options
            return element
        else:
            element["options"] = options

        # add initial option
        if multi_select and initial_users_list:
            if users_count <= MAX_STATIC_SELECT_OPTIONS:
                initial_options = []
                for user in users:
                    user_verbal = f"{user.get_user_verbal_for_team_for_slack()}"
                    option = {
                        "text": {"type": "plain_text", "text": user_verbal},
                        "value": json.dumps({"user_id": user.pk}),
                    }
                    initial_options.append(option)
                element["initial_options"] = initial_options
        elif not multi_select and initial_user:
            user_verbal = f"{initial_user.get_user_verbal_for_team_for_slack()}"
            initial_option = {
                "text": {"type": "plain_text", "text": user_verbal},
                "value": json.dumps({"user_id": initial_user.pk}),
            }
            element["initial_option"] = initial_option

        return element
