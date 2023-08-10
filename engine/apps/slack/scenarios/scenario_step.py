import importlib
import logging
import typing

from apps.slack.alert_group_slack_service import AlertGroupSlackService
from apps.slack.slack_client import SlackClientWithErrorHandling

if typing.TYPE_CHECKING:
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity
    from apps.slack.types import EventPayload
    from apps.user_management.models import Organization, User

logger = logging.getLogger(__name__)


class ScenarioStep(object):
    def __init__(
        self,
        slack_team_identity: "SlackTeamIdentity",
        organization: typing.Optional["Organization"] = None,
        user: typing.Optional["User"] = None,
    ):
        self._slack_client = SlackClientWithErrorHandling(slack_team_identity.bot_access_token)
        self.slack_team_identity = slack_team_identity
        self.organization = organization
        self.user = user

        self.alert_group_slack_service = AlertGroupSlackService(slack_team_identity, self._slack_client)

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
        self._slack_client.api_call(
            "views.open",
            trigger_id=payload["trigger_id"],
            view=view,
        )
