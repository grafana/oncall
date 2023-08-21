import logging
import typing

from apps.slack.scenarios import scenario_step
from apps.slack.types import BlockActionType, EventPayload, PayloadType, ScenarioRoute

if typing.TYPE_CHECKING:
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity

logger = logging.getLogger(__name__)


class NotifiedUserNotInChannelStep(scenario_step.ScenarioStep):
    """
    NotifiedUserNotInChannelStep handles a button press when user notified in slack, not in the channel.
    Message, which sends this button is created in SlackUserIdentity.send_link_to_slack_message method.
    """

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        logger.info("Gracefully handle NotifiedUserNotInChannelStep. Do nothing.")
        pass


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": NotifiedUserNotInChannelStep.routing_uid(),
        "step": NotifiedUserNotInChannelStep,
    },
]
