import typing

from apps.slack.scenarios import scenario_step
from apps.slack.types import BlockActionType, EventPayload, PayloadType, ScenarioRoute

if typing.TYPE_CHECKING:
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity


class DeclareIncidentStep(scenario_step.ScenarioStep):
    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        """
        Slack sends a POST request to the backend upon clicking a button with a redirect link to Incident.
        This is a dummy step, that is used to prevent raising 'Step is undefined' exception.
        """


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": DeclareIncidentStep.routing_uid(),
        "step": DeclareIncidentStep,
    },
]
