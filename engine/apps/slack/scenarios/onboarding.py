import logging
import typing

from apps.slack.scenarios import scenario_step
from apps.slack.types import EventPayload, EventType, PayloadType, ScenarioRoute

if typing.TYPE_CHECKING:
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity

logger = logging.getLogger(__name__)


class ImOpenStep(scenario_step.ScenarioStep):
    """
    Empty step to handle event and avoid 500's. In case we need it in the future.
    """

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        logger.info("InOpenStep, doing nothing.")


class AppHomeOpenedStep(scenario_step.ScenarioStep):
    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
    ) -> None:
        pass


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    {
        "payload_type": PayloadType.EVENT_CALLBACK,
        "event_type": EventType.IM_OPEN,
        "step": ImOpenStep,
    },
    {
        "payload_type": PayloadType.EVENT_CALLBACK,
        "event_type": EventType.APP_HOME_OPENED,
        "step": AppHomeOpenedStep,
    },
]
