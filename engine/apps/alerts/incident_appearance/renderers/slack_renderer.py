import json
import typing

from django.utils.text import Truncator

from apps.alerts.incident_appearance.renderers.base_renderer import AlertBaseRenderer, AlertGroupBaseRenderer
from apps.alerts.incident_appearance.templaters import AlertSlackTemplater
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
        BLOCK_SECTION_TEXT_MAX_SIZE = 2800
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

        if self.alert_group.root_alert_group is not None:
            slack_message = self.alert_group.root_alert_group.slack_message
            root_ag_name = self.alert_group.root_alert_group.long_verbose_name_without_formatting
            if slack_message:
                footer_text = f"Attached to *<{slack_message.permalink}|{root_ag_name}>*"
            else:
                footer_text = (f"Attached to *{root_ag_name}*",)
            attachments.extend(
                [
                    {
                        "fallback": "Subscription...",
                        "footer": footer_text,
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
            if self.alert_group.root_alert_group.acknowledged:
                attachments[0]["color"] = "warning"
            if self.alert_group.root_alert_group.resolved:
                attachments[0]["color"] = "good"
                attachments[0]["actions"] = []
            return attachments

        # Attaching buttons
        if self.alert_group.wiped_at is None:
            attachment_alert_buttons = self._get_buttons_attachments()
            if len(attachment_alert_buttons["blocks"][0]["elements"]) > 0:
                attachments.append(attachment_alert_buttons)

        # Attaching resolve information
        if self.alert_group.resolved:
            resolve_attachment = {
                "fallback": "Resolved...",
                "text": self.alert_group.get_resolve_text(mention_user=True),
                "callback_id": "alert",
            }
            attachments.append(resolve_attachment)
        else:
            if self.alert_group.acknowledged:
                ack_attachment = {
                    "fallback": "Acknowledged...",
                    "text": self.alert_group.get_acknowledge_text(mention_user=True),
                    "callback_id": "alert",
                }
                attachments.append(ack_attachment)

        # Attaching invitation info
        if not self.alert_group.resolved:
            attachments += self._get_invitation_attachment()

        attachments = self._set_attachments_color(attachments)
        return attachments

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

        buttons = []
        if not self.alert_group.is_maintenance_incident:
            if not self.alert_group.resolved:
                if not self.alert_group.acknowledged:
                    buttons.append(
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Acknowledge",
                                "emoji": True,
                            },
                            "type": "button",
                            "value": self._alert_group_action_value(),
                            "action_id": ScenarioStep.get_step(
                                "distribute_alerts",
                                "AcknowledgeGroupStep",
                            ).routing_uid(),
                        },
                    )
                else:
                    buttons.append(
                        {
                            "text": {
                                "type": "plain_text",
                                "text": "Unacknowledge",
                                "emoji": True,
                            },
                            "type": "button",
                            "value": self._alert_group_action_value(),
                            "action_id": ScenarioStep.get_step(
                                "distribute_alerts",
                                "UnAcknowledgeGroupStep",
                            ).routing_uid(),
                        },
                    )
                buttons.append(
                    {
                        "text": {"type": "plain_text", "text": "Resolve", "emoji": True},
                        "type": "button",
                        "style": "primary",
                        "value": self._alert_group_action_value(),
                        "action_id": ScenarioStep.get_step("distribute_alerts", "ResolveGroupStep").routing_uid(),
                    },
                )

                if not self.alert_group.silenced:
                    silence_options = [
                        {
                            "text": {"type": "plain_text", "text": text, "emoji": True},
                            "value": self._alert_group_action_value(delay=value),
                        }
                        for value, text in AlertGroup.SILENCE_DELAY_OPTIONS
                    ]
                    buttons.append(
                        {
                            "placeholder": {"type": "plain_text", "text": "Silence", "emoji": True},
                            "type": "static_select",
                            "options": silence_options,
                            "action_id": ScenarioStep.get_step("distribute_alerts", "SilenceGroupStep").routing_uid(),
                        }
                    )
                else:
                    buttons.append(
                        {
                            "text": {"type": "plain_text", "text": "Unsilence", "emoji": True},
                            "type": "button",
                            "value": self._alert_group_action_value(),
                            "action_id": ScenarioStep.get_step("distribute_alerts", "UnSilenceGroupStep").routing_uid(),
                        },
                    )

                buttons.append(
                    {
                        "text": {"type": "plain_text", "text": "Responders", "emoji": True},
                        "type": "button",
                        "value": self._alert_group_action_value(),
                        "action_id": ScenarioStep.get_step("manage_responders", "StartManageResponders").routing_uid(),
                    },
                )

                attach_button = {
                    "text": {"type": "plain_text", "text": "Attach to ...", "emoji": True},
                    "type": "button",
                    "action_id": ScenarioStep.get_step("distribute_alerts", "SelectAttachGroupStep").routing_uid(),
                    "value": self._alert_group_action_value(),
                }
                buttons.append(attach_button)
            else:
                buttons.append(
                    {
                        "text": {"type": "plain_text", "text": "Unresolve", "emoji": True},
                        "type": "button",
                        "value": self._alert_group_action_value(),
                        "action_id": ScenarioStep.get_step("distribute_alerts", "UnResolveGroupStep").routing_uid(),
                    },
                )

            if self.alert_group.channel.is_available_for_custom_templates:
                buttons.append(
                    {
                        "text": {"type": "plain_text", "text": ":mag: Format Alert", "emoji": True},
                        "type": "button",
                        "value": self._alert_group_action_value(),
                        "action_id": ScenarioStep.get_step(
                            "alertgroup_appearance", "OpenAlertAppearanceDialogStep"
                        ).routing_uid(),
                    },
                )

            # Resolution notes button
            resolution_notes_count = self.alert_group.resolution_notes.count()
            resolution_notes_button = {
                "text": {
                    "type": "plain_text",
                    "text": "Resolution notes [{}]".format(resolution_notes_count),
                    "emoji": True,
                },
                "type": "button",
                "action_id": ScenarioStep.get_step("resolution_note", "ResolutionNoteModalStep").routing_uid(),
                "value": self._alert_group_action_value(resolution_note_window_action="edit"),
            }
            if resolution_notes_count == 0:
                resolution_notes_button["style"] = "primary"
                resolution_notes_button["text"]["text"] = "Add Resolution notes"
            buttons.append(resolution_notes_button)

            # Declare Incident button
            if self.alert_group.channel.organization.is_grafana_incident_enabled:
                incident_button = {
                    "type": "button",
                    "text": {"type": "plain_text", "text": ":fire: Declare Incident", "emoji": True},
                    "value": "declare_incident",
                    "url": self.alert_group.declare_incident_link,
                    "action_id": ScenarioStep.get_step("declare_incident", "DeclareIncidentStep").routing_uid(),
                }
                buttons.append(incident_button)
        else:
            if not self.alert_group.resolved:
                buttons.append(
                    {
                        "text": {"type": "plain_text", "text": "Resolve", "emoji": True},
                        "type": "button",
                        "style": "primary",
                        "value": self._alert_group_action_value(),
                        "action_id": ScenarioStep.get_step("distribute_alerts", "ResolveGroupStep").routing_uid(),
                    },
                )
        blocks = [{"type": "actions", "elements": buttons}]
        return blocks

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
            "alert_group_pk": self.alert_group.pk,
            **kwargs,
        }
        return json.dumps(data)  # Slack block elements allow to pass value as string only (max 2000 chars)
