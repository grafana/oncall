import logging

from apps.slack.scenarios import scenario_step

logger = logging.getLogger(__name__)


class ImOpenStep(scenario_step.ScenarioStep):
    """
    Empty step to handle event and avoid 500's. In case we need it in the future.
    """

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        logger.info("InOpenStep, doing nothing.")


class AppHomeOpenedStep(scenario_step.ScenarioStep):
    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        pass


STEPS_ROUTING = [
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_EVENT_CALLBACK,
        "event_type": scenario_step.EVENT_TYPE_IM_OPEN,
        "step": ImOpenStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_EVENT_CALLBACK,
        "event_type": scenario_step.EVENT_TYPE_APP_HOME_OPENED,
        "step": AppHomeOpenedStep,
    },
]
