import json

from apps.api.permissions import RBACPermission
from apps.slack.scenarios import scenario_step

from .step_mixins import AlertGroupActionsMixin


class OpenAlertAppearanceDialogStep(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.CHATOPS_WRITE]

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        alert_group = self.get_alert_group(slack_team_identity, payload)
        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        private_metadata = {
            "organization_id": self.organization.pk if self.organization else alert_group.organization.pk,
            "alert_group_pk": alert_group.pk,
            "message_ts": payload.get("message_ts") or payload["container"]["message_ts"],
        }

        alert_receive_channel = alert_group.channel
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f":point_right: Click <{alert_receive_channel.web_link}|here> to open Integrations settings, edit Slack templates and return here",
                },
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": "Once changed Refresh the alert group"}},
        ]

        view = {
            "callback_id": UpdateAppearanceStep.routing_uid(),
            "blocks": blocks,
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Alert group template",
            },
            "submit": {
                "type": "plain_text",
                "text": "Refresh alert group",
            },
            "private_metadata": json.dumps(private_metadata),
        }

        self._slack_client.api_call(
            "views.open",
            trigger_id=payload["trigger_id"],
            view=view,
        )


class UpdateAppearanceStep(scenario_step.ScenarioStep):
    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        from apps.alerts.models import AlertGroup

        private_metadata = json.loads(payload["view"]["private_metadata"])
        alert_group_pk = private_metadata["alert_group_pk"]

        alert_group = AlertGroup.objects.get(pk=alert_group_pk)

        attachments = alert_group.render_slack_attachments()
        blocks = alert_group.render_slack_blocks()

        self._slack_client.api_call(
            "chat.update",
            channel=alert_group.slack_message.channel_id,
            ts=alert_group.slack_message.slack_id,
            attachments=attachments,
            blocks=blocks,
        )


STEPS_ROUTING = [
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
        "action_type": scenario_step.ACTION_TYPE_BUTTON,
        "action_name": OpenAlertAppearanceDialogStep.routing_uid(),
        "step": OpenAlertAppearanceDialogStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_BUTTON,
        "block_action_id": OpenAlertAppearanceDialogStep.routing_uid(),
        "step": OpenAlertAppearanceDialogStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_VIEW_SUBMISSION,
        "view_callback_id": UpdateAppearanceStep.routing_uid(),
        "step": UpdateAppearanceStep,
    },
]
