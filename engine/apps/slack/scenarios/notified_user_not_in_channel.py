import logging

from apps.slack.scenarios import scenario_step
from apps.slack.types import BlockActionType, PayloadType

logger = logging.getLogger(__name__)


class NotifiedUserNotInChannelStep(scenario_step.ScenarioStep):
    """
    NotifiedUserNotInChannelStep handles a button press when user notified in slack, not in the channel.
    Message, which sends this button is created in SlackUserIdentity.send_link_to_slack_message method.
    """

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        logger.info("Gracefully handle NotifiedUserNotInChannelStep. Do nothing.")
        pass


STEPS_ROUTING = [
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": NotifiedUserNotInChannelStep.routing_uid(),
        "step": NotifiedUserNotInChannelStep,
    },
]
