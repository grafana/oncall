from apps.slack.scenarios import scenario_step


class DeclareIncidentStep(scenario_step.ScenarioStep):
    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        """
        Slack sends a POST request to the backend upon clicking a button with a redirect link to Incident.
        This is a dummy step, that is used to prevent raising 'Step is undefined' exception.
        """


STEPS_ROUTING = [
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_BUTTON,
        "block_action_id": DeclareIncidentStep.routing_uid(),
        "step": DeclareIncidentStep,
    },
]
