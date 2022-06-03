import json

from django.apps import apps

from apps.alerts.incident_appearance.renderers.base_renderer import AlertBaseRenderer, AlertGroupBaseRenderer
from apps.alerts.incident_appearance.templaters import AlertSlackTemplater
from apps.slack.scenarios.scenario_step import ScenarioStep
from common.utils import is_string_with_visible_characters, str_or_backup


class AlertSlackRenderer(AlertBaseRenderer):
    def __init__(self, alert):
        super().__init__(alert)
        self.channel = alert.group.channel

    @property
    def templater_class(self):
        return AlertSlackTemplater

    def render_alert_blocks(self):
        blocks = []

        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": str_or_backup(self.templated_alert.title, "Alert"),
                },
            }
        )
        if is_string_with_visible_characters(self.templated_alert.message):
            message = self.templated_alert.message
            BLOCK_SECTION_TEXT_MAX_SIZE = 2800
            if len(message) > BLOCK_SECTION_TEXT_MAX_SIZE:
                message = (
                    message[: BLOCK_SECTION_TEXT_MAX_SIZE - 3] + "... Message has been trimmed. "
                    "Check the whole content in Web"
                )
            blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": message}})
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
    def __init__(self, alert_group):
        super().__init__(alert_group)

        # render the last alert content as Slack message, so Slack message is updated when a new alert comes
        self.alert_renderer = self.alert_renderer_class(self.alert_group.alerts.last())

    @property
    def alert_renderer_class(self):
        return AlertSlackRenderer

    def render_alert_group_blocks(self):
        non_resolve_alerts_queryset = self.alert_group.alerts.filter(is_resolve_signal=False)
        if not self.alert_group.channel.organization.slack_team_identity.installed_via_granular_permissions:
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": ":warning: *Action required - reinstall  app*\n"
                        "Slack is deprecating current permission model. We will support it till DATE\n"  # TODO: deprecation date
                        "Don't worry - we migrate OnCall to new one, but it required to reinstall app."
                        'Press "Upgrade" button to see more detailed instruction and upgrade.',
                    },
                },
                {"type": "divider"},
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "Upgrade",
                            },
                            "value": "click_me_123",
                            "url": self.alert_group.channel.organization.web_slack_page_link,
                        },
                    ],
                },
            ]
        else:
            blocks = []
        if non_resolve_alerts_queryset.count() <= 1:
            blocks.extend(self.alert_renderer.render_alert_blocks())
        else:
            blocks.extend(self._get_alert_group_base_blocks_if_grouped())
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
                                "value": json.dumps({"organization_id": self.alert_group.channel.organization_id}),
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

    def _get_text_alert_grouped(self):
        alert_count = self.alert_group.alerts.count()
        link = self.alert_group.web_link

        text = (
            f":package: Showing the last alert only out of {alert_count} total. "
            f"Visit <{link}|the plugin page> to see them all."
        )

        return text

    def _get_alert_group_base_blocks_if_grouped(self):
        text = self._get_text_alert_grouped()
        blocks = self.alert_renderer.render_alert_blocks()
        blocks.append({"type": "context", "elements": [{"type": "mrkdwn", "text": text}]})
        return blocks

    def _get_buttons_attachments(self):
        attachment = {"blocks": self._get_buttons_blocks()}
        return attachment

    def _get_buttons_blocks(self):
        AlertGroup = apps.get_model("alerts", "AlertGroup")
        buttons = []
        if self.alert_group.maintenance_uuid is None:
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
                            "value": json.dumps({"organization_id": self.alert_group.channel.organization_id}),
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
                            "value": json.dumps({"organization_id": self.alert_group.channel.organization_id}),
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
                        "value": json.dumps({"organization_id": self.alert_group.channel.organization_id}),
                        "action_id": ScenarioStep.get_step("distribute_alerts", "ResolveGroupStep").routing_uid(),
                    },
                )

                if self.alert_group.invitations.filter(is_active=True).count() < 5:
                    slack_team_identity = self.alert_group.channel.organization.slack_team_identity
                    action_id = ScenarioStep.get_step("distribute_alerts", "InviteOtherPersonToIncident").routing_uid()
                    text = "Invite..."
                    invitation_element = ScenarioStep(
                        slack_team_identity,
                        self.alert_group.channel.organization,
                    ).get_select_user_element(action_id, text=text)
                    buttons.append(invitation_element)
                if not self.alert_group.acknowledged:
                    if not self.alert_group.silenced:
                        silence_options = [
                            {"text": {"type": "plain_text", "text": text, "emoji": True}, "value": str(value)}
                            for value, text in AlertGroup.SILENCE_DELAY_OPTIONS
                        ]
                        buttons.append(
                            {
                                "placeholder": {"type": "plain_text", "text": "Silence", "emoji": True},
                                "type": "static_select",
                                "options": silence_options,
                                "action_id": ScenarioStep.get_step(
                                    "distribute_alerts", "SilenceGroupStep"
                                ).routing_uid(),
                                # "value": json.dumps({"organization_id": self.alert_group.channel.organization_id}),
                            }
                        )
                    else:
                        buttons.append(
                            {
                                "text": {"type": "plain_text", "text": "Unsilence", "emoji": True},
                                "type": "button",
                                "value": json.dumps({"organization_id": self.alert_group.channel.organization_id}),
                                "action_id": ScenarioStep.get_step(
                                    "distribute_alerts", "UnSilenceGroupStep"
                                ).routing_uid(),
                            },
                        )
                attach_button = {
                    "text": {"type": "plain_text", "text": "Attach to ...", "emoji": True},
                    "type": "button",
                    "action_id": ScenarioStep.get_step("distribute_alerts", "SelectAttachGroupStep").routing_uid(),
                    "value": json.dumps(
                        {
                            "alert_group_pk": self.alert_group.pk,
                            "organization_id": self.alert_group.channel.organization_id,
                        }
                    ),
                }
                buttons.append(attach_button)
            else:
                buttons.append(
                    {
                        "text": {"type": "plain_text", "text": "Unresolve", "emoji": True},
                        "type": "button",
                        "value": json.dumps({"organization_id": self.alert_group.channel.organization_id}),
                        "action_id": ScenarioStep.get_step("distribute_alerts", "UnResolveGroupStep").routing_uid(),
                    },
                )

            if self.alert_group.channel.is_available_for_custom_templates:
                buttons.append(
                    {
                        "text": {"type": "plain_text", "text": ":mag: Format Alert", "emoji": True},
                        "type": "button",
                        "value": json.dumps(
                            {
                                "alert_group_pk": str(self.alert_group.pk),
                                "organization_id": self.alert_group.channel.organization_id,
                            }
                        ),
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
                "value": json.dumps(
                    {
                        "resolution_note_window_action": "edit",
                        "alert_group_pk": self.alert_group.pk,
                        "organization_id": self.alert_group.channel.organization_id,
                    }
                ),
            }
            if resolution_notes_count == 0:
                resolution_notes_button["style"] = "primary"
                resolution_notes_button["text"]["text"] = "Add Resolution notes"
            buttons.append(resolution_notes_button)
        else:
            if not self.alert_group.resolved:
                buttons.append(
                    {
                        "text": {"type": "plain_text", "text": "Resolve", "emoji": True},
                        "type": "button",
                        "style": "primary",
                        "value": json.dumps({"organization_id": self.alert_group.channel.organization_id}),
                        "action_id": ScenarioStep.get_step("distribute_alerts", "ResolveGroupStep").routing_uid(),
                    },
                )
        blocks = [{"type": "actions", "elements": buttons}]
        return blocks

    def _get_invitation_attachment(self):
        Invitation = apps.get_model("alerts", "Invitation")
        invitations = Invitation.objects.filter(is_active=True, alert_group=self.alert_group).all()
        if len(invitations) == 0:
            return []
        buttons = []
        for invitation in invitations:
            invitee_name = invitation.invitee.get_user_verbal_for_team_for_slack()
            buttons.append(
                {
                    "name": "{}_{}".format(
                        ScenarioStep.get_step("distribute_alerts", "StopInvitationProcess").routing_uid(), invitation.pk
                    ),
                    "text": "Stop inviting {}".format(invitee_name),
                    "type": "button",
                    "style": "primary",
                    "value": json.dumps({"organization_id": self.alert_group.channel.organization_id}),
                },
            )
        return [
            {
                "fallback": "Invitations...",
                "callback_id": "invitations",
                "actions": buttons,
            }
        ]
