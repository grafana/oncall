import typing

from apps.api.permissions import RBACPermission
from apps.slack.chatops_proxy_routing import make_private_metadata
from apps.slack.constants import BLOCK_SECTION_TEXT_MAX_SIZE
from apps.slack.scenarios import scenario_step
from apps.slack.scenarios.slack_renderer import AlertGroupLogSlackRenderer
from apps.slack.types import (
    Block,
    BlockActionType,
    EventPayload,
    InteractiveMessageActionType,
    ModalView,
    PayloadType,
    ScenarioRoute,
)
from apps.user_management.models import Organization

from .step_mixins import AlertGroupActionsMixin

if typing.TYPE_CHECKING:
    from apps.slack.models import SlackTeamIdentity, SlackUserIdentity


class OpenAlertGroupTimelineDialogStep(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.CHATOPS_WRITE]

    def process_scenario(
        self,
        slack_user_identity: "SlackUserIdentity",
        slack_team_identity: "SlackTeamIdentity",
        payload: EventPayload,
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        alert_group = self.get_alert_group(slack_team_identity, payload)
        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        private_metadata = {
            "organization_id": self.organization.pk,
            "alert_group_pk": alert_group.pk,
            "message_ts": payload.get("message_ts") or payload["container"]["message_ts"],
        }

        alert_receive_channel = alert_group.channel
        past_log_report = AlertGroupLogSlackRenderer.render_alert_group_past_log_report_text(alert_group)
        future_log_report = AlertGroupLogSlackRenderer.render_alert_group_future_log_report_text(alert_group)
        blocks: typing.List[Block.Section] = []
        if past_log_report:
            blocks.append(
                {"type": "section", "text": {"type": "mrkdwn", "text": past_log_report[:BLOCK_SECTION_TEXT_MAX_SIZE]}}
            )
        if future_log_report:
            blocks.append(
                {"type": "section", "text": {"type": "mrkdwn", "text": future_log_report[:BLOCK_SECTION_TEXT_MAX_SIZE]}}
            )

        view: ModalView = {
            "blocks": blocks,
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Alert group log",
            },
            "private_metadata": make_private_metadata(private_metadata, alert_receive_channel.organization),
        }

        self._slack_client.views_open(trigger_id=payload["trigger_id"], view=view)


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    {
        "payload_type": PayloadType.INTERACTIVE_MESSAGE,
        "action_type": InteractiveMessageActionType.BUTTON,
        "action_name": OpenAlertGroupTimelineDialogStep.routing_uid(),
        "step": OpenAlertGroupTimelineDialogStep,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": OpenAlertGroupTimelineDialogStep.routing_uid(),
        "step": OpenAlertGroupTimelineDialogStep,
    },
]
