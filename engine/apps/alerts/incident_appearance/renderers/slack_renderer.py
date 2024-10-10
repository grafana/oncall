import json
import typing

from django.utils.text import Truncator

from apps.alerts.incident_appearance.renderers.base_renderer import AlertBaseRenderer, AlertGroupBaseRenderer
from apps.alerts.incident_appearance.templaters import AlertSlackTemplater
from apps.slack.chatops_proxy_routing import make_value
from apps.slack.constants import BLOCK_SECTION_TEXT_MAX_SIZE
from apps.slack.scenarios.scenario_step import ScenarioStep
from apps.slack.types import Block
from common.utils import is_string_with_visible_characters, str_or_backup

if typing.TYPE_CHECKING:
    from apps.alerts.models import Alert, AlertGroup


class AlertSlackRenderer(AlertBaseRenderer):
    def __init__(self, alert: "Alert"):
        super().__init__(alert)
        self.channel = alert.group.channel

    @property
    def templater_class(self):
        return AlertSlackTemplater

    def render_alert_blocks(self) -> Block.AnyBlocks:
        blocks: Block.AnyBlocks = []

        title = Truncator(str_or_backup(self.templated_alert.title, "Alert"))
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": title.chars(BLOCK_SECTION_TEXT_MAX_SIZE),
                },
            }
        )
        if is_string_with_visible_characters(self.templated_alert.message):
            message = Truncator(self.templated_alert.message)
            truncate_wording = "... Message has been trimmed. Check the whole content in Web"
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message.chars(BLOCK_SECTION_TEXT_MAX_SIZE, truncate=truncate_wording),
                    },
                }
            )
        return blocks

    def render_alert_attachments(self):
        attachments = []
        if is_string_with_visible_characters(self.templated_alert.image_url):
            attachments.append(
                {
                    "fallback": "{}: {}".format(self.channel.get_integration_display(), self.alert.title),
                    "title": "{} via Grafana OnCall".format(self.channel.get_integration_display()),
                    "title_link": self.templated_alert.source_link,
                    "callback_id": "alert",
                    "text": "",
                    "image_url": self.templated_alert.image_url,
                }
            )
        return attachments


class AlertGroupSlackRenderer(AlertGroupBaseRenderer):
    def __init__(self, alert_group: "AlertGroup"):
        super().__init__(alert_group)

        # render the last alert content as Slack message, so Slack message is updated when a new alert comes
        self.alert_renderer = self.alert_renderer_class(self.alert_group.alerts.last())

    @property
    def alert_renderer_class(self):
        return AlertSlackRenderer

    def render_alert_group_blocks(self) -> Block.AnyBlocks:
        blocks: Block.AnyBlocks = self.alert_renderer.render_alert_blocks()
        alerts_count = self.alert_group.alerts.count()
        if alerts_count > 1:
            text = (
                f":package: Showing the last alert only out of {alerts_count} total. "
                f"Visit <{self.alert_group.web_link}|the plugin page> to see them all."
            )
            blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": text}]})
        return blocks

    def render_alert_group_attachments(self):
        attachments = self.alert_renderer.render_alert_attachments()
        alert_group = self.alert_group
        root_alert_group = alert_group.root_alert_group

        if root_alert_group is not None:
            slack_message = root_alert_group.slack_message
            root_ag_name = root_alert_group.long_verbose_name_without_formatting

            attachments.extend(
                [
                    {
                        "fallback": "Subscription...",
                        "footer": (
                            f"Attached to *<{slack_message.permalink}|{root_ag_name}>*"
                            if slack_message
                            else f"Attached to *{root_ag_name}*"
                        ),
                        "color": "danger",
                        "mrkdwn": True,
                        "callback_id": "subscription notification",
                        "actions": [
                            {
                                "name": ScenarioStep.get_step("distribute_alerts", "UnAttachGroupStep").routing_uid(),
                                "text": "Unattach",
                                "type": "button",
                                "value": self._alert_group_action_value(),
                            }
                        ],
                    }
                ]
            )

            if root_alert_group.acknowledged:
                attachments[0]["color"] = "warning"
            if root_alert_group.resolved:
                attachments[0]["color"] = "good"
                attachments[0]["actions"] = []

            return attachments

        # Attaching resolve information
        if alert_group.resolved:
            attachments.append(
                {
                    "fallback": "Resolved...",
                    "text": alert_group.get_resolve_text(mention_user=False),
                    "callback_id": "alert",
                }
            )
        elif alert_group.acknowledged:
            attachments.append(
                {
                    "fallback": "Acknowledged...",
                    "text": alert_group.get_acknowledge_text(mention_user=False),
                    "callback_id": "alert",
                }
            )

        # Attaching buttons
        if alert_group.wiped_at is None:
            attachment_alert_buttons = self._get_buttons_attachments()
            if len(attachment_alert_buttons["blocks"][0]["elements"]) > 0:
                attachments.append(attachment_alert_buttons)

        # Attaching invitation info
        if not alert_group.resolved:
            attachments += self._get_invitation_attachment()

        return self._set_attachments_color(attachments)

    def _set_attachments_color(self, attachments):
        color = "#a30200"  # danger
        if self.alert_group.silenced:
            color = "#dddddd"  # slack-grey
        if self.alert_group.acknowledged:
            color = "#daa038"  # warning
        if self.alert_group.resolved:
            color = "#2eb886"  # good
        for attachment in attachments:
            attachment["color"] = color
        return attachments

    def _get_buttons_attachments(self):
        attachment = {"blocks": self._get_buttons_blocks()}
        return attachment

    def _get_buttons_blocks(self):
        from apps.alerts.models import AlertGroup

        alert_group = self.alert_group
        integration = alert_group.channel
        grafana_incident_enabled = integration.organization.is_grafana_incident_enabled

        def _make_button(text, action_id_step_class_name, action_id_scenario_step="distribute_alerts"):
            return {
                "text": {
                    "type": "plain_text",
                    "text": text,
                    "emoji": True,
                },
                "type": "button",
                "value": self._alert_group_action_value(),
                "action_id": ScenarioStep.get_step(action_id_scenario_step, action_id_step_class_name).routing_uid(),
            }

        acknowledge_button = _make_button("Acknowledge", "AcknowledgeGroupStep")
        unacknowledge_button = _make_button("Unacknowledge", "UnAcknowledgeGroupStep")
        resolve_button = _make_button("Resolve", "ResolveGroupStep")
        unresolve_button = _make_button("Unresolve", "UnResolveGroupStep")
        unsilence_button = _make_button("Unsilence", "UnSilenceGroupStep")
        responders_button = _make_button("Responders", "StartManageResponders", "manage_responders")
        attach_button = _make_button("Attach to ...", "SelectAttachGroupStep")

        resolution_notes_count = alert_group.resolution_notes.count()
        resolution_notes_button = {
            "text": {
                "type": "plain_text",
                "text": f"Resolution notes [{resolution_notes_count}]",
                "emoji": True,
            },
            "type": "button",
            "action_id": ScenarioStep.get_step("resolution_note", "ResolutionNoteModalStep").routing_uid(),
            "value": self._alert_group_action_value(resolution_note_window_action="edit"),
        }
        if resolution_notes_count == 0:
            resolution_notes_button["style"] = "primary"
            resolution_notes_button["text"]["text"] = "Add Resolution notes"

        silence_button = {
            "placeholder": {
                "type": "plain_text",
                "text": "Silence",
                "emoji": True,
            },
            "type": "static_select",
            "options": [
                {
                    "text": {"type": "plain_text", "text": text, "emoji": True},
                    "value": self._alert_group_action_value(delay=value),
                }
                for value, text in AlertGroup.SILENCE_DELAY_OPTIONS
            ],
            "action_id": ScenarioStep.get_step("distribute_alerts", "SilenceGroupStep").routing_uid(),
        }

        declare_incident_button = {
            "type": "button",
            "text": {
                "type": "plain_text",
                "text": ":fire: Declare incident",
                "emoji": True,
            },
            "value": "declare_incident",
            "url": self.alert_group.declare_incident_link,
            "action_id": ScenarioStep.get_step("declare_incident", "DeclareIncidentStep").routing_uid(),
        }

        show_timeline_button = _make_button(
            ":blue_book: Show Timeline", "OpenAlertGroupTimelineDialogStep", "alertgroup_timeline"
        )

        buttons = []
        if not alert_group.is_maintenance_incident:
            if not alert_group.resolved:
                if not alert_group.acknowledged:
                    buttons.append(acknowledge_button)
                else:
                    if grafana_incident_enabled:
                        buttons.append(declare_incident_button)
                    buttons.append(unacknowledge_button)

                buttons.extend(
                    [
                        resolve_button,
                        unsilence_button if alert_group.silenced else silence_button,
                        responders_button,
                        attach_button,
                    ]
                )
            else:
                buttons.append(unresolve_button)

            buttons.append(resolution_notes_button)

            if grafana_incident_enabled and not alert_group.acknowledged:
                buttons.append(declare_incident_button)
        else:
            if not alert_group.resolved:
                buttons.append(resolve_button)

        buttons.append(show_timeline_button)

        return [{"type": "actions", "elements": buttons}]

    def _get_invitation_attachment(self):
        from apps.alerts.models import Invitation

        invitations = Invitation.objects.filter(is_active=True, alert_group=self.alert_group).all()
        if len(invitations) == 0:
            return []
        buttons = []
        for invitation in invitations:
            invitee_name = invitation.invitee.get_username_with_slack_verbal()
            buttons.append(
                {
                    "name": ScenarioStep.get_step("distribute_alerts", "StopInvitationProcess").routing_uid(),
                    "text": "Stop inviting {}".format(invitee_name),
                    "type": "button",
                    "style": "primary",
                    "value": self._alert_group_action_value(invitation_id=invitation.pk),
                },
            )
        return [
            {
                "fallback": "Invitations...",
                "callback_id": "invitations",
                "actions": buttons,
            }
        ]

    def _get_select_user_element(
        self, action_id, multi_select=False, initial_user=None, initial_users_list=None, text=None
    ):
        def get_action_value(user_id):
            """
            In contrast to other buttons and select menus, self._alert_group_action_value is not used here.
            It's because there could be a lot of users, and we don't want to increase the payload size too much.
            """
            return json.dumps({"user_id": user_id})

        MAX_STATIC_SELECT_OPTIONS = 100

        if not text:
            text = f"Select User{'s' if multi_select else ''}"
        element = {
            "action_id": action_id,
            "type": "multi_static_select" if multi_select else "static_select",
            "placeholder": {
                "type": "plain_text",
                "text": text,
                "emoji": True,
            },
        }

        users = self.alert_group.channel.organization.users.all().select_related("slack_user_identity")

        users_count = users.count()
        options = []

        for user in users:
            user_verbal = f"{user.get_username_with_slack_verbal()}"
            if len(user_verbal) > 75:
                user_verbal = user_verbal[:72] + "..."
            option = {"text": {"type": "plain_text", "text": user_verbal}, "value": get_action_value(user.pk)}
            options.append(option)

        if users_count > MAX_STATIC_SELECT_OPTIONS:
            option_groups = []
            option_groups_chunks = [
                options[x : x + MAX_STATIC_SELECT_OPTIONS] for x in range(0, len(options), MAX_STATIC_SELECT_OPTIONS)
            ]
            for option_group in option_groups_chunks:
                option_group = {"label": {"type": "plain_text", "text": " "}, "options": option_group}
                option_groups.append(option_group)
            element["option_groups"] = option_groups
        elif users_count == 0:  # strange case when there are no users to select
            option = {
                "text": {"type": "plain_text", "text": "No users to select"},
                "value": get_action_value(None),
            }
            options.append(option)
            element["options"] = options
            return element
        else:
            element["options"] = options

        # add initial option
        if multi_select and initial_users_list:
            if users_count <= MAX_STATIC_SELECT_OPTIONS:
                initial_options = []
                for user in users:
                    user_verbal = f"{user.get_username_with_slack_verbal()}"
                    option = {
                        "text": {"type": "plain_text", "text": user_verbal},
                        "value": get_action_value(user.pk),
                    }
                    initial_options.append(option)
                element["initial_options"] = initial_options
        elif not multi_select and initial_user:
            user_verbal = f"{initial_user.get_username_with_slack_verbal()}"
            initial_option = {
                "text": {"type": "plain_text", "text": user_verbal},
                "value": get_action_value(initial_user.pk),
            }
            element["initial_option"] = initial_option

        return element

    def _alert_group_action_value(self, **kwargs):
        """
        Store organization and alert group IDs in Slack button or select menu values.
        alert_group_pk is used in apps.slack.scenarios.step_mixins.AlertGroupActionsMixin to get the right alert group
        when handling AG actions in Slack.
        """

        data = {
            "organization_id": self.alert_group.channel.organization_id,
            "alert_group_ppk": self.alert_group.public_primary_key,
            **kwargs,
        }

        return make_value(data, self.alert_group.channel.organization)
