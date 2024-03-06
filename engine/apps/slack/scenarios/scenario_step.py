import importlib
import logging
import typing

from apps.api.permissions import LegacyAccessControlCompatiblePermissions, user_is_authorized
from apps.slack.alert_group_slack_service import AlertGroupSlackService
from apps.slack.client import SlackClient
from apps.slack.types import EventPayload

if typing.TYPE_CHECKING:
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity
    from apps.user_management.models import Organization, User

logger = logging.getLogger(__name__)


class ScenarioStep(object):
    REQUIRED_PERMISSIONS: LegacyAccessControlCompatiblePermissions = []

    def __init__(
        self,
        slack_team_identity: "SlackTeamIdentity",
        organization: typing.Optional["Organization"] = None,
        user: typing.Optional["User"] = None,
    ):
        self._slack_client = SlackClient(slack_team_identity)
        self.slack_team_identity = slack_team_identity
        self.organization = organization
        self.user = user

        self.alert_group_slack_service = AlertGroupSlackService(slack_team_identity, self._slack_client)

    def is_authorized(self) -> bool:
        """
        Check that user has required permissions to perform an action.
        """
        return self.user is not None and user_is_authorized(self.user, self.REQUIRED_PERMISSIONS)

    def open_unauthorized_warning(self, payload: EventPayload) -> None:
        self.open_warning_window(
            payload,
            warning_text="You do not have permission to perform this action. Ask an admin to upgrade your permissions.",
            title="Permission denied",
        )

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: "EventPayload",
    ) -> None:
        pass

    @classmethod
    def routing_uid(cls) -> str:
        return cls.__name__

    @classmethod
    def get_step(cls, scenario: str, step: str) -> "ScenarioStep":
        """
        This is a dynamic Step loader to avoid circular dependencies in scenario files
        """
        # Just in case circular dependencies will be an issue again, this may help:
        # https://stackoverflow.com/posts/36442015/revisions
        try:
            module = importlib.import_module("apps.slack.scenarios." + scenario)
            return getattr(module, step)
        except ImportError as e:
            raise Exception("Check import spelling! Scenario: {}, Step:{}, Error: {}".format(scenario, step, e))

    def open_warning_window(self, payload: "EventPayload", warning_text: str, title: str | None = None) -> None:
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
        self._slack_client.views_open(trigger_id=payload["trigger_id"], view=view)
