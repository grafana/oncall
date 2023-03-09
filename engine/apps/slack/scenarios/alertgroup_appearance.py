import json

from django.apps import apps
from django.db import transaction
from jinja2 import TemplateSyntaxError
from rest_framework.response import Response

from apps.api.permissions import RBACPermission
from apps.slack.scenarios import scenario_step
from common.insight_log import EntityEvent, write_resource_insight_log
from common.jinja_templater import jinja_template_env

from .step_mixins import CheckAlertIsUnarchivedMixin, IncidentActionsAccessControlMixin


class OpenAlertAppearanceDialogStep(
    CheckAlertIsUnarchivedMixin, IncidentActionsAccessControlMixin, scenario_step.ScenarioStep
):
    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.CHATOPS_WRITE]
    ACTION_VERBOSE = "open Alert Appearance"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload):
        AlertGroup = apps.get_model("alerts", "AlertGroup")
        AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")

        try:
            message_ts = payload["message_ts"]
        except KeyError:
            message_ts = payload["container"]["message_ts"]

        try:
            alert_group_pk = payload["actions"][0]["action_id"].split("_")[1]
        except (KeyError, IndexError):
            value = json.loads(payload["actions"][0]["value"])
            alert_group_pk = value["alert_group_pk"]

        alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)
        if not self.check_alert_is_unarchived(slack_team_identity, payload, alert_group):
            return
        blocks = []

        private_metadata = {
            "organization_id": self.organization.pk if self.organization else alert_group.organization.pk,
            "alert_group_pk": alert_group_pk,
            "message_ts": message_ts,
        }

        integration = alert_group.channel.integration

        PAYLOAD_TEXT_SIZE = 3000
        raw_request_data = json.dumps(alert_group.alerts.first().raw_request_data, sort_keys=True, indent=4)

        # This is a special case for amazon sns notifications in str format CHEKED
        if (
            hasattr(AlertReceiveChannel, "INTEGRATION_AMAZON_SNS")
            and alert_group.channel.integration == AlertReceiveChannel.INTEGRATION_AMAZON_SNS
            and raw_request_data == "{}"
        ):
            raw_request_data = alert_group.alerts.first().message

        raw_request_data_chunks = [
            raw_request_data[i : i + PAYLOAD_TEXT_SIZE] for i in range(0, len(raw_request_data), PAYLOAD_TEXT_SIZE)
        ]
        for idx, chunk in enumerate(raw_request_data_chunks):
            block = {
                "type": "input",
                "block_id": f"payload_{idx}",
                "label": {
                    "type": "plain_text",
                    "text": f"Payload (Part {idx + 1}):" if len(raw_request_data_chunks) > 1 else "Payload (Readonly)",
                },
                "element": {
                    "type": "plain_text_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Payload of the current alert",
                    },
                    "action_id": UpdateAppearanceStep.routing_uid(),
                    "multiline": True,
                },
                "optional": True,
                "hint": {"type": "plain_text", "text": "This is example payload of the first alert of the group"},
            }
            block["element"]["initial_value"] = chunk
            blocks.append(block)
        blocks.append({"type": "divider"})

        for notification_channel in ["slack", "web", "sms", "phone_call", "telegram"]:
            blocks.append(
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"{notification_channel.replace('_', ' ').title()} Templates",
                        "emoji": True,
                    },
                }
            )
            for templatizable_attr in ["title", "message", "image_url"]:
                try:
                    attr = getattr(alert_group.channel, f"{notification_channel}_{templatizable_attr}_template")
                except AttributeError:
                    continue
                block = {
                    "type": "input",
                    "block_id": f"{notification_channel}_{templatizable_attr}_template",
                    "label": {
                        "type": "plain_text",
                        "text": f"{notification_channel.capitalize()} {templatizable_attr}:",
                    },
                    "element": {
                        "type": "plain_text_input",
                        "placeholder": {"type": "plain_text", "text": f"{{{{ payload.{templatizable_attr} }}}}"},
                        "action_id": UpdateAppearanceStep.routing_uid(),
                        "multiline": True,
                    },
                    "optional": True,
                    "hint": {
                        "type": "plain_text",
                        "text": "Jinja2 template",
                    },
                }
                if attr is not None:
                    block["element"]["initial_value"] = attr
                else:
                    default_values = getattr(
                        AlertReceiveChannel,
                        f"INTEGRATION_TO_DEFAULT_{notification_channel.upper()}_{templatizable_attr.upper()}_TEMPLATE",
                        None,
                    )
                    if default_values is not None:
                        default_value = default_values.get(integration)
                        if default_value is not None:
                            block["element"]["initial_value"] = default_value
                blocks.append(block)
            blocks.append({"type": "divider"})

        common_templates_meta_data = {
            "source_link": {"placeholder": "{{ payload.link_to_upstream_details }}", "hint": "Jinja2 template."},
            "grouping_id": {"placeholder": "{{ payload.uid }}", "hint": "Jinja2 template"},
            "resolve_condition": {
                "placeholder": '{{ 1 if payload.state == "OK" else 0 }}',
                "hint": "This Jinja2 template should output one of the following values: ok, true, 1 (case insensitive)",
            },
            "acknowledge_condition": {
                "placeholder": '{{ 1 if payload.state == "OK" else 0 }}',
                "hint": "This Jinja2 template should output one of the following values: ok, true, 1 (case insensitive)",
            },
        }

        for common_template in common_templates_meta_data.keys():
            try:
                attr = getattr(alert_group.channel, f"{common_template}_template")
            except AttributeError:
                continue

            block = {
                "type": "input",
                "block_id": f"{common_template}_template",
                "label": {
                    "type": "plain_text",
                    "text": f"{common_template.capitalize().replace('_', ' ')}:",
                },
                "element": {
                    "type": "plain_text_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": common_templates_meta_data[common_template]["placeholder"],
                    },
                    "action_id": UpdateAppearanceStep.routing_uid(),
                    "multiline": True,
                },
                "optional": True,
                "hint": {
                    "type": "plain_text",
                    "text": common_templates_meta_data[common_template]["hint"],
                },
            }
            if attr is not None:
                block["element"]["initial_value"] = attr
            else:
                default_values = getattr(
                    AlertReceiveChannel, f"INTEGRATION_TO_DEFAULT_{common_template.upper()}_TEMPLATE", None
                )
                if default_values is not None:
                    default_value = default_values.get(integration)
                    if default_value:
                        block["element"]["initial_value"] = default_value
            blocks.append(block)

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
                "text": "Submit",
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
        AlertGroup = apps.get_model("alerts", "AlertGroup")
        AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")

        private_metadata = json.loads(payload["view"]["private_metadata"])
        alert_group_pk = private_metadata["alert_group_pk"]
        payload_values = payload["view"]["state"]["values"]

        with transaction.atomic():
            alert_group = AlertGroup.all_objects.filter(pk=alert_group_pk).select_for_update().get()
            integration = alert_group.channel.integration
            alert_receive_channel = alert_group.channel
            prev_state = alert_receive_channel.insight_logs_serialized

            for templatizable_attr in ["title", "message", "image_url"]:
                for notification_channel in ["slack", "web", "sms", "phone_call", "telegram"]:
                    attr_name = f"{notification_channel}_{templatizable_attr}_template"
                    try:
                        old_value = getattr(alert_receive_channel, attr_name)
                    except AttributeError:
                        continue
                    new_value = payload_values[attr_name][self.routing_uid()].get("value")

                    if new_value is None and old_value is not None:
                        setattr(alert_receive_channel, attr_name, None)
                        alert_receive_channel.save()
                    elif new_value is not None:
                        default_values = getattr(
                            AlertReceiveChannel,
                            f"INTEGRATION_TO_DEFAULT_{notification_channel.upper()}_{templatizable_attr.upper()}_TEMPLATE",
                            None,
                        )
                        if default_values is not None:
                            default_value = default_values.get(integration)

                        try:
                            if default_value is None or new_value.strip() != default_value.strip():
                                jinja_template_env.from_string(new_value)
                                setattr(alert_receive_channel, attr_name, new_value)
                                alert_receive_channel.save()
                            elif default_value is not None and new_value.strip() == default_value.strip():
                                new_value = None
                                setattr(alert_receive_channel, attr_name, new_value)
                                alert_receive_channel.save()
                        except TemplateSyntaxError:
                            return Response(
                                {"response_action": "errors", "errors": {attr_name: "Template has incorrect format"}},
                                headers={"content-type": "application/json"},
                            )

            common_templates = ["source_link", "grouping_id", "resolve_condition", "acknowledge_condition"]
            for common_template in common_templates:
                attr_name = f"{common_template}_template"
                try:
                    old_value = getattr(alert_receive_channel, attr_name)
                except AttributeError:
                    continue
                new_value = payload_values[attr_name][self.routing_uid()].get("value")

                if new_value is None and old_value is not None:
                    setattr(alert_receive_channel, attr_name, None)
                    alert_receive_channel.save()
                    alert_group.save()
                elif new_value is not None:
                    default_values = getattr(
                        AlertReceiveChannel, f"INTEGRATION_TO_DEFAULT_{common_template.upper()}_TEMPLATE", None
                    )
                    if default_values is not None:
                        default_value = default_values.get(integration)

                    try:
                        if default_value is None or new_value.strip() != default_value.strip():
                            jinja_template_env.from_string(new_value)
                            setattr(alert_receive_channel, attr_name, new_value)
                            alert_receive_channel.save()
                            alert_group.save()
                        elif default_value is not None and new_value.strip() == default_value.strip():
                            new_value = None
                            setattr(alert_receive_channel, attr_name, new_value)
                            alert_receive_channel.save()
                            alert_group.save()
                    except TemplateSyntaxError:
                        return Response(
                            {"response_action": "errors", "errors": {common_template: "Template has incorrect format"}},
                            headers={"content-type": "application/json"},
                        )

        new_state = alert_receive_channel.insight_logs_serialized

        if new_state != prev_state:
            write_resource_insight_log(
                instance=alert_receive_channel,
                author=slack_user_identity.get_user(alert_receive_channel.organization),
                event=EntityEvent.UPDATED,
                prev_state=prev_state,
                new_state=new_state,
            )

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
