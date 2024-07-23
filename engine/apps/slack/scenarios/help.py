import typing

from apps.slack.scenarios.scenario_step import ScenarioStep
from apps.slack.slash_command import SlashCommand
from apps.slack.types import EventPayload, PayloadType, ScenarioRoute

if typing.TYPE_CHECKING:
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity
    from apps.user_management.models import Organization


class HelpCommand(ScenarioStep):
    @staticmethod
    def matcher(slash_command: SlashCommand) -> bool:
        return (
            slash_command.command == "grafana" and slash_command.service == "oncall" and slash_command.action == "help"
        )

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        help_message = "It's a help command"

        self._slack_client.chat_postEphemeral(
            channel=payload["event"]["channel"],
            user=slack_user_identity.slack_id,
            text=help_message,
        )
        return


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    {
        "payload_type": PayloadType.SLASH_COMMAND,
        "step": HelpCommand,
        "matcher": HelpCommand.matcher,
    },
]
