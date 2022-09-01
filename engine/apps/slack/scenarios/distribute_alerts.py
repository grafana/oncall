import json
import logging
from contextlib import suppress
from datetime import datetime

from django.apps import apps
from django.core.cache import cache
from django.utils import timezone
from jinja2 import TemplateError

from apps.alerts.constants import ActionSource
from apps.alerts.incident_appearance.renderers.constants import DEFAULT_BACKUP_TITLE
from apps.alerts.incident_appearance.renderers.slack_renderer import AlertSlackRenderer
from apps.alerts.models import AlertGroup, AlertGroupLogRecord, AlertReceiveChannel, Invitation
from apps.alerts.tasks import custom_button_result
from apps.alerts.utils import render_curl_command
from apps.slack.constants import CACHE_UPDATE_INCIDENT_SLACK_MESSAGE_LIFETIME, SLACK_RATE_LIMIT_DELAY
from apps.slack.scenarios import scenario_step
from apps.slack.scenarios.slack_renderer import AlertGroupLogSlackRenderer
from apps.slack.slack_client import SlackClientWithErrorHandling
from apps.slack.slack_client.exceptions import (
    SlackAPIChannelArchivedException,
    SlackAPIException,
    SlackAPIRateLimitException,
    SlackAPITokenException,
)
from apps.slack.slack_formatter import SlackFormatter
from apps.slack.tasks import (
    post_or_update_log_report_message_task,
    send_message_to_thread_if_bot_not_in_channel,
    update_incident_slack_message,
)
from apps.slack.utils import get_cache_key_update_incident_slack_message
from common.constants.role import Role
from common.utils import clean_markup, is_string_with_visible_characters

from .step_mixins import CheckAlertIsUnarchivedMixin, IncidentActionsAccessControlMixin

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AlertShootingStep(scenario_step.ScenarioStep):

    tags = [
        scenario_step.ScenarioStep.TAG_TRIGGERED_BY_SYSTEM,
    ]

    def publish_slack_messages(self, slack_team_identity, alert_group, alert, attachments, channel_id, blocks):
        SlackMessage = apps.get_model("slack", "SlackMessage")
        # channel_id can be None if general log channel for slack_team_identity is not set
        if channel_id is None:
            logger.info(f"Failed to post message to Slack for alert_group {alert_group.pk} because channel_id is None")
            alert_group.reason_to_skip_escalation = AlertGroup.CHANNEL_NOT_SPECIFIED
            alert_group.save(update_fields=["reason_to_skip_escalation"])
            print("Not delivering alert due to channel_id is None.")
            return

        try:
            result = self._slack_client.api_call(
                "chat.postMessage", channel=channel_id, attachments=attachments, blocks=blocks
            )

            slack_message = SlackMessage.objects.create(
                slack_id=result["ts"],
                organization=alert_group.channel.organization,
                _slack_team_identity=slack_team_identity,
                channel_id=channel_id,
                alert_group=alert_group,
            )

            alert_group.slack_message = slack_message
            alert_group.save(update_fields=["slack_message"])

            # If alert was made out of a message:
            if alert_group.channel.integration == AlertReceiveChannel.INTEGRATION_SLACK_CHANNEL:
                channel = json.loads(alert.integration_unique_data)["channel"]
                result = self._slack_client.api_call(
                    "chat.postMessage",
                    channel=channel,
                    thread_ts=json.loads(alert.integration_unique_data)["ts"],
                    text=":rocket: <{}|Incident registered!>".format(alert_group.slack_message.permalink),
                    team=slack_team_identity,
                )
                SlackMessage(
                    slack_id=result["ts"],
                    organization=alert_group.channel.organization,
                    _slack_team_identity=self.slack_team_identity,
                    channel_id=channel,
                    alert_group=alert_group,
                ).save()

            alert.delivered = True
        except SlackAPITokenException:
            alert_group.reason_to_skip_escalation = AlertGroup.ACCOUNT_INACTIVE
            alert_group.save(update_fields=["reason_to_skip_escalation"])
            print("Not delivering alert due to account_inactive.")
        except SlackAPIChannelArchivedException:
            alert_group.reason_to_skip_escalation = AlertGroup.CHANNEL_ARCHIVED
            alert_group.save(update_fields=["reason_to_skip_escalation"])
            print("Not delivering alert due to channel is archived.")
        except SlackAPIRateLimitException as e:
            # don't rate limit maintenance alert
            if alert_group.channel.integration != AlertReceiveChannel.INTEGRATION_MAINTENANCE:
                alert_group.reason_to_skip_escalation = AlertGroup.RATE_LIMITED
                alert_group.save(update_fields=["reason_to_skip_escalation"])
                delay = e.response.get("rate_limit_delay") or SLACK_RATE_LIMIT_DELAY
                alert_group.channel.start_send_rate_limit_message_task(delay)
                print("Not delivering alert due to slack rate limit.")
            else:
                raise e
        except SlackAPIException as e:
            # TODO: slack-onprem check exceptions
            if e.response["error"] == "channel_not_found":
                alert_group.reason_to_skip_escalation = AlertGroup.CHANNEL_ARCHIVED
                alert_group.save(update_fields=["reason_to_skip_escalation"])
                print("Not delivering alert due to channel is archived.")
            elif e.response["error"] == "restricted_action":
                # workspace settings prevent bot to post message (eg. bot is not a full member)
                alert_group.reason_to_skip_escalation = AlertGroup.RESTRICTED_ACTION
                alert_group.save(update_fields=["reason_to_skip_escalation"])
                print("Not delivering alert due to workspace restricted action.")
            else:
                raise e
        finally:
            alert.save()

    def process_signal(self, alert):
        # do not try to post alert group message to slack if its channel is rate limited
        if alert.group.channel.is_rate_limited_in_slack:
            logger.info("Skip posting or updating alert_group in Slack due to rate limit")
            AlertGroup.all_objects.filter(
                pk=alert.group.pk,
                slack_message_sent=False,
            ).update(slack_message_sent=True, reason_to_skip_escalation=AlertGroup.RATE_LIMITED)
            return

        num_updated_rows = AlertGroup.all_objects.filter(pk=alert.group.pk, slack_message_sent=False).update(
            slack_message_sent=True
        )

        if num_updated_rows == 1:
            try:
                channel_id = alert.group.channel_filter.slack_channel_id_or_general_log_id
                self._send_first_alert(alert, channel_id)
            except SlackAPIException as e:
                AlertGroup.all_objects.filter(pk=alert.group.pk).update(slack_message_sent=False)
                raise e

            is_debug_mode = (
                alert.group.channel.maintenance_mode is not None
                or alert.group.channel.organization.maintenance_mode is not None
            )
            if is_debug_mode:
                self._send_debug_mode_notice(alert.group, channel_id)
            else:
                # check if alert group was posted to slack before posting message to thread
                if not alert.group.skip_escalation_in_slack:
                    self._send_thread_messages(alert.group, channel_id)
        else:
            # check if alert group was posted to slack before updating its message
            if not alert.group.skip_escalation_in_slack:
                update_task_id = update_incident_slack_message.apply_async(
                    (self.slack_team_identity.pk, alert.group.pk),
                    countdown=10,
                )
                cache.set(
                    get_cache_key_update_incident_slack_message(alert.group.pk),
                    update_task_id,
                    timeout=CACHE_UPDATE_INCIDENT_SLACK_MESSAGE_LIFETIME,
                )
            else:
                logger.info("Skip updating alert_group in Slack due to rate limit")

    def _send_first_alert(self, alert, channel_id):
        attachments = alert.group.render_slack_attachments()
        blocks = alert.group.render_slack_blocks()

        self.publish_slack_messages(
            slack_team_identity=self.slack_team_identity,
            alert_group=alert.group,
            alert=alert,
            attachments=attachments,
            channel_id=channel_id,
            blocks=blocks,
        )

    def _send_debug_mode_notice(self, alert_group, channel_id):
        blocks = []
        text = "Escalations are silenced due to Debug mode"
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})
        self._slack_client.api_call(
            "chat.postMessage",
            channel=channel_id,
            text=text,
            attachments=[],
            thread_ts=alert_group.slack_message.slack_id,
            mrkdwn=True,
            blocks=blocks,
        )

    def _send_thread_messages(self, alert_group, channel_id):
        post_or_update_log_report_message_task.apply_async(
            (alert_group.pk, self.slack_team_identity.pk),
        )

        send_message_to_thread_if_bot_not_in_channel.apply_async(
            (alert_group.pk, self.slack_team_identity.pk, channel_id),
            countdown=1,  # delay for message so that the log report is published first
        )

    def process_scenario(self, slack_user_identity, slack_team_identity, alert, payload=None):
        pass


class InviteOtherPersonToIncident(
    CheckAlertIsUnarchivedMixin,
    IncidentActionsAccessControlMixin,
    scenario_step.ScenarioStep,
):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    ALLOWED_ROLES = [Role.ADMIN, Role.EDITOR]
    ACTION_VERBOSE = "invite to incident"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        User = apps.get_model("user_management", "User")

        alert_group = self.get_alert_group_from_slack_message(payload)
        selected_user = None

        if not self.check_alert_is_unarchived(slack_team_identity, payload, alert_group):
            return

        try:
            # user selection
            selected_user_id = json.loads(payload["actions"][0]["selected_option"]["value"])["user_id"]
            if selected_user_id is not None:  # None if there are no users to select
                selected_user = User.objects.get(pk=selected_user_id)
        except (KeyError, json.JSONDecodeError):
            # for old version with user slack_id selection
            warning_text = "Oops! Something goes wrong, please try again"
            self.open_warning_window(payload, warning_text)
        if selected_user is not None:
            Invitation.invite_user(selected_user, alert_group, self.user)
        else:
            self._update_slack_message(alert_group)

    def process_signal(self, log_record):
        alert_group = log_record.alert_group
        self._update_slack_message(alert_group)


class SilenceGroupStep(
    CheckAlertIsUnarchivedMixin,
    IncidentActionsAccessControlMixin,
    scenario_step.ScenarioStep,
):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    ALLOWED_ROLES = [Role.ADMIN, Role.EDITOR]
    ACTION_VERBOSE = "silence incident"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):

        try:
            silence_delay = int(payload["actions"][0]["selected_options"][0]["value"])
        except KeyError:
            silence_delay = int(payload["actions"][0]["selected_option"]["value"])

        alert_group = self.get_alert_group_from_slack_message(payload)

        if self.check_alert_is_unarchived(slack_team_identity, payload, alert_group):
            alert_group.silence_by_user(self.user, silence_delay, action_source=ActionSource.SLACK)

    def process_signal(self, log_record):
        alert_group = log_record.alert_group
        self._update_slack_message(alert_group)


class UnSilenceGroupStep(
    CheckAlertIsUnarchivedMixin,
    IncidentActionsAccessControlMixin,
    scenario_step.ScenarioStep,
):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    ALLOWED_ROLES = [Role.ADMIN, Role.EDITOR]
    ACTION_VERBOSE = "unsilence incident"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):

        alert_group = self.get_alert_group_from_slack_message(payload)
        if self.check_alert_is_unarchived(slack_team_identity, payload, alert_group):
            alert_group.un_silence_by_user(self.user, action_source=ActionSource.SLACK)

    def process_signal(self, log_record):
        alert_group = log_record.alert_group
        self._update_slack_message(alert_group)


class SelectAttachGroupStep(
    CheckAlertIsUnarchivedMixin,
    IncidentActionsAccessControlMixin,
    scenario_step.ScenarioStep,
):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    ALLOWED_ROLES = [Role.ADMIN, Role.EDITOR]
    ACTION_VERBOSE = "Select Incident for Attaching to"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        AlertGroup = apps.get_model("alerts", "AlertGroup")
        value = json.loads(payload["actions"][0]["value"])
        alert_group_pk = value.get("alert_group_pk")
        alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)

        if not self.check_alert_is_unarchived(slack_team_identity, payload, alert_group):
            return
        blocks = []
        view = {
            "callback_id": AttachGroupStep.routing_uid(),
            "blocks": blocks,
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Attach to Incident",
            },
            "private_metadata": json.dumps(
                {
                    "organization_id": self.organization.pk if self.organization else alert_group.organization.pk,
                    "alert_group_pk": alert_group_pk,
                }
            ),
            "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        }
        attached_incidents_exists = alert_group.dependent_alert_groups.exists()
        if attached_incidents_exists:
            attached_incidents = alert_group.dependent_alert_groups.all()
            text = (
                f"Oops! This incident cannot be attached to another one because it already has "
                f"attached incidents ({attached_incidents.count()}):\n"
            )
            for dependent_alert in attached_incidents:
                if dependent_alert.permalink:
                    dependent_alert_text = (
                        f"\n<{dependent_alert.permalink}|{dependent_alert.long_verbose_name_without_formatting}>"
                    )
                else:
                    dependent_alert_text = f"\n{dependent_alert.long_verbose_name}"
                if len(dependent_alert_text + text) <= 2995:  # max 3000 symbols
                    text += dependent_alert_text
                else:
                    text += "\n..."
                    break
            blocks.append(
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": text,
                    },
                }
            )
        else:
            blocks.extend(self.get_select_incidents_blocks(alert_group))
            if blocks:
                view["submit"] = {
                    "type": "plain_text",
                    "text": "Submit",
                }
            else:
                blocks.append(
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Oops! There is no incidents, available to attach.",
                        },
                    }
                )
        self._slack_client.api_call(
            "views.open",
            trigger_id=payload["trigger_id"],
            view=view,
        )

    def get_select_incidents_blocks(self, alert_group):
        collected_options = []
        blocks = []

        alert_receive_channel_ids = AlertReceiveChannel.objects.filter(
            organization=alert_group.channel.organization
        ).values_list("id", flat=True)

        alert_groups_queryset = (
            AlertGroup.unarchived_objects.prefetch_related(
                "alerts",
                "channel__organization",
            )
            .filter(channel_id__in=list(alert_receive_channel_ids), resolved=False, root_alert_group__isnull=True)
            .exclude(pk=alert_group.pk)
            .order_by("-pk")
        )

        for alert_group_to_attach in alert_groups_queryset[:60]:
            # long_verbose_name_without_formatting was removed from here because it increases queries count due to
            # alerts.first().
            # alert_group_to_attach.alerts.exists() and alerts.all()[0] don't make additional queries to db due to
            # prefetch_related.
            first_alert = alert_group_to_attach.alerts.all()[0]
            templated_alert = AlertSlackRenderer(first_alert).templated_alert
            sf = SlackFormatter(alert_group_to_attach.channel.organization)
            if is_string_with_visible_characters(templated_alert.title):
                alert_name = templated_alert.title
                alert_name = sf.format(alert_name)
                alert_name = clean_markup(alert_name)
            else:
                alert_name = (
                    f"#{alert_group_to_attach.inside_organization_number} "
                    f"{DEFAULT_BACKUP_TITLE} via {alert_group_to_attach.channel.verbal_name}"
                )
            if len(alert_name) > 75:
                alert_name = f"{alert_name[:72]}..."
            collected_options.append(
                {
                    "text": {"type": "plain_text", "text": f"{alert_name}", "emoji": True},
                    "value": str(alert_group_to_attach.pk),
                }
            )
        if len(collected_options) > 0:
            blocks.append(
                {
                    "type": "input",
                    "block_id": self.routing_uid(),
                    "element": {
                        "type": "static_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Attach to...",
                        },
                        "action_id": AttachGroupStep.routing_uid(),
                        "options": collected_options[:60],
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Select incident:",
                        "emoji": True,
                    },
                }
            )
        return blocks


class AttachGroupStep(
    CheckAlertIsUnarchivedMixin,
    IncidentActionsAccessControlMixin,
    scenario_step.ScenarioStep,
):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    ALLOWED_ROLES = [Role.ADMIN, Role.EDITOR]
    ACTION_VERBOSE = "Attach incident"

    def process_signal(self, log_record):
        alert_group = log_record.alert_group

        if log_record.type == AlertGroupLogRecord.TYPE_ATTACHED and log_record.alert_group.is_maintenance_incident:
            text = f"{log_record.rendered_log_line_action(for_slack=True)}"
            self.publish_message_to_thread(alert_group, text=text)

        if log_record.type == AlertGroupLogRecord.TYPE_FAILED_ATTACHMENT:
            ephemeral_text = log_record.rendered_log_line_action(for_slack=True)
            slack_user_identity = log_record.author.slack_user_identity

            if slack_user_identity:
                self._slack_client.api_call(
                    "chat.postEphemeral",
                    user=slack_user_identity.slack_id,
                    channel=alert_group.slack_message.channel_id,
                    text="{}{}".format(ephemeral_text[:1].upper(), ephemeral_text[1:]),
                    unfurl_links=True,
                )

        self._update_slack_message(alert_group)

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):

        # submit selection in modal window
        if payload["type"] == scenario_step.PAYLOAD_TYPE_VIEW_SUBMISSION:
            alert_group_pk = json.loads(payload["view"]["private_metadata"])["alert_group_pk"]
            alert_group = AlertGroup.all_objects.get(pk=alert_group_pk)
            root_alert_group_pk = payload["view"]["state"]["values"][SelectAttachGroupStep.routing_uid()][
                AttachGroupStep.routing_uid()
            ]["selected_option"]["value"]
            root_alert_group = AlertGroup.all_objects.get(pk=root_alert_group_pk)
        # old version of attach selection by dropdown
        else:
            try:
                root_alert_group_pk = int(payload["actions"][0]["selected_options"][0]["value"])
            except KeyError:
                root_alert_group_pk = int(payload["actions"][0]["selected_option"]["value"])

            root_alert_group = AlertGroup.all_objects.get(pk=root_alert_group_pk)
            alert_group = self.get_alert_group_from_slack_message(payload)

        if self.check_alert_is_unarchived(slack_team_identity, payload, alert_group) and self.check_alert_is_unarchived(
            slack_team_identity, payload, root_alert_group
        ):
            alert_group.attach_by_user(self.user, root_alert_group, action_source=ActionSource.SLACK)
        else:
            self._update_slack_message(alert_group)


class UnAttachGroupStep(
    CheckAlertIsUnarchivedMixin,
    IncidentActionsAccessControlMixin,
    scenario_step.ScenarioStep,
):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    ALLOWED_ROLES = [Role.ADMIN, Role.EDITOR]
    ACTION_VERBOSE = "Unattach incident"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        alert_group = self.get_alert_group_from_slack_message(payload)
        if self.check_alert_is_unarchived(slack_team_identity, payload, alert_group):
            alert_group.un_attach_by_user(self.user, action_source=ActionSource.SLACK)

    def process_signal(self, log_record):
        alert_group = log_record.alert_group
        self._update_slack_message(alert_group)


class StopInvitationProcess(CheckAlertIsUnarchivedMixin, IncidentActionsAccessControlMixin, scenario_step.ScenarioStep):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    ALLOWED_ROLES = [Role.ADMIN, Role.EDITOR]
    ACTION_VERBOSE = "stop invitation"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        alert_group = self.get_alert_group_from_slack_message(payload)
        if not self.check_alert_is_unarchived(slack_team_identity, payload, alert_group):
            return

        invitation_pk = payload["actions"][0]["name"].split("_")[1]
        Invitation.stop_invitation(invitation_pk, self.user)

    def process_signal(self, log_record):
        self._update_slack_message(log_record.invitation.alert_group)


class CustomButtonProcessStep(
    CheckAlertIsUnarchivedMixin,
    IncidentActionsAccessControlMixin,
    scenario_step.ScenarioStep,
):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    ALLOWED_ROLES = [Role.ADMIN, Role.EDITOR]
    ACTION_VERBOSE = "click custom button"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        CustomButtom = apps.get_model("alerts", "CustomButton")
        alert_group = self.get_alert_group_from_slack_message(payload)
        if self.check_alert_is_unarchived(slack_team_identity, payload, alert_group):
            custom_button_pk = payload["actions"][0]["name"].split("_")[1]
            alert_group_pk = payload["actions"][0]["name"].split("_")[2]
            try:
                CustomButtom.objects.get(pk=custom_button_pk)
            except CustomButtom.DoesNotExist:
                warning_text = "Oops! This button was deleted"
                self.open_warning_window(payload, warning_text=warning_text)
                self._update_slack_message(alert_group)
            else:
                custom_button_result.apply_async(
                    args=(
                        custom_button_pk,
                        alert_group_pk,
                    ),
                    kwargs={"user_pk": self.user.pk},
                )

    def process_signal(self, log_record):
        alert_group = log_record.alert_group
        result_message = log_record.reason
        custom_button = log_record.custom_button
        debug_message = ""
        if not log_record.step_specific_info["is_request_successful"]:
            with suppress(TemplateError, json.JSONDecodeError):
                post_kwargs = custom_button.build_post_kwargs(log_record.alert_group.alerts.first())
                curl_request = render_curl_command(log_record.custom_button.webhook, "POST", post_kwargs)
                debug_message = f"```{curl_request}```"

        if log_record.author is not None:
            user_verbal = log_record.author.get_user_verbal_for_team_for_slack(mention=True)
            text = (
                f"{user_verbal} sent a request from an outgoing webhook `{log_record.custom_button.name}` "
                f"with the result `{result_message}`"
            )
        else:
            text = (
                f"A request from an outgoing webhook `{log_record.custom_button.name}` was sent "
                f"according to escalation policy with the result `{result_message}`"
            )
        attachments = [
            {"callback_id": "alert", "text": debug_message},
        ]
        self.publish_message_to_thread(alert_group, attachments=attachments, text=text)


class ResolveGroupStep(
    CheckAlertIsUnarchivedMixin,
    IncidentActionsAccessControlMixin,
    scenario_step.ScenarioStep,
):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    ALLOWED_ROLES = [Role.ADMIN, Role.EDITOR]
    ACTION_VERBOSE = "resolve incident"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        ResolutionNoteModalStep = scenario_step.ScenarioStep.get_step("resolution_note", "ResolutionNoteModalStep")

        alert_group = self.get_alert_group_from_slack_message(payload)

        if not self.check_alert_is_unarchived(slack_team_identity, payload, alert_group):
            return

        if alert_group.maintenance_uuid is None:

            if self.organization.is_resolution_note_required and not alert_group.has_resolution_notes:

                resolution_note_data = {
                    "resolution_note_window_action": "edit",
                    "alert_group_pk": alert_group.pk,
                    "action_resolve": True,
                }
                ResolutionNoteModalStep(slack_team_identity, self.organization, self.user).process_scenario(
                    slack_user_identity, slack_team_identity, payload, data=resolution_note_data
                )
                return

            alert_group.resolve_by_user(self.user, action_source=ActionSource.SLACK)
        else:
            alert_group.stop_maintenance(self.user)

    def process_signal(self, log_record):
        alert_group = log_record.alert_group

        if not alert_group.happened_while_maintenance:
            self._update_slack_message(alert_group)


class UnResolveGroupStep(
    CheckAlertIsUnarchivedMixin,
    IncidentActionsAccessControlMixin,
    scenario_step.ScenarioStep,
):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    ALLOWED_ROLES = [Role.ADMIN, Role.EDITOR]
    ACTION_VERBOSE = "unresolve incident"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        alert_group = self.get_alert_group_from_slack_message(payload)
        if self.check_alert_is_unarchived(slack_team_identity, payload, alert_group):
            alert_group.un_resolve_by_user(self.user, action_source=ActionSource.SLACK)

    def process_signal(self, log_record):
        alert_group = log_record.alert_group
        self._update_slack_message(alert_group)


class AcknowledgeGroupStep(
    CheckAlertIsUnarchivedMixin,
    IncidentActionsAccessControlMixin,
    scenario_step.ScenarioStep,
):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    ALLOWED_ROLES = [Role.ADMIN, Role.EDITOR]
    ACTION_VERBOSE = "acknowledge incident"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        alert_group = self.get_alert_group_from_slack_message(payload)
        logger.debug(f"process_scenario in AcknowledgeGroupStep for alert_group {alert_group.pk}")
        if self.check_alert_is_unarchived(slack_team_identity, payload, alert_group):
            alert_group.acknowledge_by_user(self.user, action_source=ActionSource.SLACK)

    def process_signal(self, log_record):
        alert_group = log_record.alert_group
        logger.debug(f"Started process_signal in AcknowledgeGroupStep for alert_group {alert_group.pk}")
        self._update_slack_message(alert_group)
        logger.debug(f"Finished process_signal in AcknowledgeGroupStep for alert_group {alert_group.pk}")


class UnAcknowledgeGroupStep(
    CheckAlertIsUnarchivedMixin,
    IncidentActionsAccessControlMixin,
    scenario_step.ScenarioStep,
):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    ALLOWED_ROLES = [Role.ADMIN, Role.EDITOR]
    ACTION_VERBOSE = "unacknowledge incident"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        alert_group = self.get_alert_group_from_slack_message(payload)
        logger.debug(f"process_scenario in UnAcknowledgeGroupStep for alert_group {alert_group.pk}")
        if self.check_alert_is_unarchived(slack_team_identity, payload, alert_group):
            alert_group.un_acknowledge_by_user(self.user, action_source=ActionSource.SLACK)

    def process_signal(self, log_record):
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
        alert_group = log_record.alert_group
        logger.debug(f"Started process_signal in UnAcknowledgeGroupStep for alert_group {alert_group.pk}")

        if log_record.type == AlertGroupLogRecord.TYPE_AUTO_UN_ACK:
            channel_id = alert_group.slack_message.channel_id
            if log_record.author is not None:
                user_verbal = log_record.author.get_user_verbal_for_team_for_slack(mention=True)
            else:
                user_verbal = "No one"

            message_attachments = [
                {
                    "callback_id": "alert",
                    "text": "",
                    "footer": "Escalation started again...",
                },
            ]
            text = (
                f"{user_verbal} hasn't responded to an acknowledge timeout reminder."
                f" Incident is unacknowledged automatically"
            )
            if alert_group.slack_message.ack_reminder_message_ts:
                try:
                    self._slack_client.api_call(
                        "chat.update",
                        channel=channel_id,
                        ts=alert_group.slack_message.ack_reminder_message_ts,
                        text=text,
                        attachments=message_attachments,
                    )
                except SlackAPIException as e:
                    # post to thread if ack reminder message was deleted in Slack
                    if e.response["error"] == "message_not_found":
                        self.publish_message_to_thread(alert_group, attachments=message_attachments, text=text)
                    elif e.response["error"] == "account_inactive":
                        logger.info(
                            f"Skip unacknowledge slack message for alert_group {alert_group.pk} due to account_inactive"
                        )
                    else:
                        raise
            else:
                self.publish_message_to_thread(alert_group, attachments=message_attachments, text=text)
        self._update_slack_message(alert_group)
        logger.debug(f"Finished process_signal in UnAcknowledgeGroupStep for alert_group {alert_group.pk}")


class AcknowledgeConfirmationStep(AcknowledgeGroupStep):
    ACTION_VERBOSE = "confirm acknowledge status"

    def process_scenario(self, slack_user_identity, slack_team_identity, payload, action=None):
        AlertGroup = apps.get_model("alerts", "AlertGroup")
        alert_group_id = payload["actions"][0]["value"].split("_")[1]
        alert_group = AlertGroup.all_objects.get(pk=alert_group_id)
        channel = payload["channel"]["id"]
        message_ts = payload["message_ts"]

        if alert_group.acknowledged:
            if alert_group.acknowledged_by == AlertGroup.USER:
                if self.user == alert_group.acknowledged_by_user:
                    user_verbal = alert_group.acknowledged_by_user.get_user_verbal_for_team_for_slack()
                    text = f"{user_verbal} confirmed that the incident is still acknowledged"
                    self._slack_client.api_call(
                        "chat.update",
                        channel=channel,
                        ts=message_ts,
                        text=text,
                    )
                    alert_group.acknowledged_by_confirmed = datetime.utcnow()
                    alert_group.save(update_fields=["acknowledged_by_confirmed"])
                else:
                    self._slack_client.api_call(
                        "chat.postEphemeral",
                        channel=channel,
                        user=slack_user_identity.slack_id,
                        text="This alert is acknowledged by another user. Acknowledge it yourself first.",
                    )
            elif alert_group.acknowledged_by == AlertGroup.SOURCE:
                user_verbal = self.user.get_user_verbal_for_team_for_slack()
                text = f"{user_verbal} confirmed that the incident is still acknowledged"
                self._slack_client.api_call(
                    "chat.update",
                    channel=channel,
                    ts=message_ts,
                    text=text,
                )
                alert_group.acknowledged_by_confirmed = datetime.utcnow()
                alert_group.save(update_fields=["acknowledged_by_confirmed"])
        else:
            self._slack_client.api_call(
                "chat.delete",
                channel=channel,
                ts=message_ts,
            )
            self._slack_client.api_call(
                "chat.postEphemeral",
                channel=channel,
                user=slack_user_identity.slack_id,
                text="This alert is already unacknowledged.",
            )

    def process_signal(self, log_record):
        Organization = apps.get_model("user_management", "Organization")
        SlackMessage = apps.get_model("slack", "SlackMessage")

        alert_group = log_record.alert_group
        channel_id = alert_group.slack_message.channel_id
        user_verbal = log_record.author.get_user_verbal_for_team_for_slack(mention=True)
        text = f"{user_verbal}, please confirm that you're still working on this incident."

        if alert_group.channel.organization.unacknowledge_timeout != Organization.UNACKNOWLEDGE_TIMEOUT_NEVER:
            attachments = [
                {
                    "fallback": "Are you still working on this incident?",
                    "text": text,
                    "callback_id": "alert",
                    "attachment_type": "default",
                    "footer": "This is a reminder that the incident is still acknowledged"
                    " and not resolved. It will be unacknowledged automatically and escalation will"
                    " start again soon.",
                    "actions": [
                        {
                            "name": scenario_step.ScenarioStep.get_step(
                                "distribute_alerts", "AcknowledgeConfirmationStep"
                            ).routing_uid(),
                            "text": "Confirm",
                            "type": "button",
                            "style": "primary",
                            "value": scenario_step.ScenarioStep.get_step(
                                "distribute_alerts", "AcknowledgeConfirmationStep"
                            ).routing_uid()
                            + ("_" + str(alert_group.pk)),
                        },
                    ],
                }
            ]
            try:
                response = self._slack_client.api_call(
                    "chat.postMessage",
                    channel=channel_id,
                    text=text,
                    attachments=attachments,
                    thread_ts=alert_group.slack_message.slack_id,
                )
            except SlackAPITokenException as e:
                logger.warning(
                    f"Unable to post acknowledge reminder in slack. "
                    f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                    f"{e}"
                )
            except SlackAPIChannelArchivedException:
                logger.warning(
                    f"Unable to post acknowledge reminder in slack. "
                    f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                    f"Reason: 'is_archived'"
                )
            except SlackAPIException as e:
                if e.response["error"] == "channel_not_found":
                    logger.warning(
                        f"Unable to post acknowledge reminder in slack. "
                        f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                        f"Reason: 'channel_not_found'"
                    )
                else:
                    raise e
            else:
                SlackMessage(
                    slack_id=response["ts"],
                    organization=alert_group.channel.organization,
                    _slack_team_identity=self.slack_team_identity,
                    channel_id=channel_id,
                    alert_group=alert_group,
                ).save()

                alert_group.slack_message.ack_reminder_message_ts = response["ts"]
                alert_group.slack_message.save(update_fields=["ack_reminder_message_ts"])
        else:
            text = f"This is a reminder that the incident is still acknowledged by {user_verbal}"
            self.publish_message_to_thread(alert_group, text=text)


class WipeGroupStep(scenario_step.ScenarioStep):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    ACTION_VERBOSE = "wipe incident"

    def process_signal(self, log_record):
        alert_group = log_record.alert_group
        user_verbal = log_record.author.get_user_verbal_for_team_for_slack()
        text = f"Wiped by {user_verbal}"
        self.publish_message_to_thread(alert_group, text=text)
        self._update_slack_message(alert_group)


class DeleteGroupStep(scenario_step.ScenarioStep):

    tags = [
        scenario_step.ScenarioStep.TAG_INCIDENT_ROUTINE,
    ]

    ACTION_VERBOSE = "delete incident"

    def process_signal(self, log_record):
        alert_group = log_record.alert_group

        self.remove_resolution_note_reaction(alert_group)

        bot_messages_ts = []
        bot_messages_ts.extend(alert_group.slack_messages.values_list("slack_id", flat=True))
        bot_messages_ts.extend(
            alert_group.resolution_note_slack_messages.filter(posted_by_bot=True).values_list("ts", flat=True)
        )
        channel_id = alert_group.slack_message.channel_id

        for message_ts in bot_messages_ts:
            try:
                self._slack_client.api_call(
                    "chat.delete",
                    channel=channel_id,
                    ts=message_ts,
                )
            except SlackAPITokenException as e:
                logger.error(
                    f"Unable to delete messages in slack. Message ts: {message_ts}"
                    f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                    f"{e}"
                )
            except SlackAPIException as e:
                if e.response["error"] == "channel_not_found":
                    logger.warning(
                        f"Unable to delete messages in slack. Message ts: {message_ts}"
                        f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                        f"Reason: 'channel_not_found'"
                        f"{e}"
                    )
                elif e.response["error"] == "message_not_found":
                    logger.warning(
                        f"Unable to delete messages in slack. Message ts: {message_ts}"
                        f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                        f"Reason: 'message_not_found'"
                        f"{e}"
                    )
                elif e.response["error"] == "is_archived":
                    logger.warning(
                        f"Unable to delete messages in slack. Message ts: {message_ts}"
                        f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                        f"Reason: 'is_archived'"
                        f"{e}"
                    )
                elif e.response["error"] == "cant_delete_message":
                    sc_with_access_token = SlackClientWithErrorHandling(
                        self.slack_team_identity.access_token
                    )  # used access_token instead of bot_access_token
                    sc_with_access_token.api_call(
                        "chat.delete",
                        channel=channel_id,
                        ts=message_ts,
                    )
                else:
                    raise e

    def remove_resolution_note_reaction(self, alert_group):
        for message in alert_group.resolution_note_slack_messages.filter(added_to_resolution_note=True):
            message.added_to_resolution_note = False
            message.save(update_fields=["added_to_resolution_note"])
            try:
                self._slack_client.api_call(
                    "reactions.remove",
                    channel=message.slack_channel_id,
                    name="memo",
                    timestamp=message.ts,
                )
            except SlackAPITokenException as e:
                logger.warning(
                    f"Unable to delete resolution note reaction in slack. "
                    f"Slack team identity pk: {self.slack_team_identity.pk}.\n"
                    f"{e}"
                )
            except SlackAPIException as e:
                logger.warning(f"Unable to delete resolution note reaction in slack.\n" f"{e}")


class UpdateLogReportMessageStep(scenario_step.ScenarioStep):
    def process_signal(self, alert_group):
        if alert_group.skip_escalation_in_slack or alert_group.channel.is_rate_limited_in_slack:
            return

        self.update_log_message(alert_group)

    def post_log_message(self, alert_group):
        SlackMessage = apps.get_model("slack", "SlackMessage")

        slack_message = alert_group.get_slack_message()

        if slack_message is None:
            logger.info(f"Cannot post log message for alert_group {alert_group.pk} because SlackMessage doesn't exist")
            return None

        text = ("Building escalation plan... :thinking_face:",)

        slack_log_message = alert_group.slack_log_message

        if slack_log_message is None:
            logger.debug(f"Start posting new log message for alert_group {alert_group.pk}")
            try:
                result = self._slack_client.api_call(
                    "chat.postMessage", channel=slack_message.channel_id, thread_ts=slack_message.slack_id, text=text
                )
            except SlackAPITokenException as e:
                print(e)
            except SlackAPIRateLimitException as e:
                if not alert_group.channel.is_rate_limited_in_slack:
                    delay = e.response.get("rate_limit_delay") or SLACK_RATE_LIMIT_DELAY
                    alert_group.channel.start_send_rate_limit_message_task(delay)
                    logger.info(
                        f"Log message has not been posted for alert_group {alert_group.pk} due to slack rate limit."
                    )
            except SlackAPIException as e:
                if e.response["error"] == "channel_not_found":
                    pass
                elif e.response["error"] == "invalid_auth":
                    pass
                elif e.response["error"] == "is_archived":
                    pass
                else:
                    raise e
            else:
                logger.debug(f"Create new slack_log_message for alert_group {alert_group.pk}")
                slack_log_message = SlackMessage(
                    slack_id=result["ts"],
                    organization=self.organization,
                    _slack_team_identity=self.slack_team_identity,
                    channel_id=slack_message.channel_id,
                    last_updated=timezone.now(),
                    alert_group=alert_group,
                )
                slack_log_message.save()

                alert_group.slack_log_message = slack_log_message
                alert_group.save(update_fields=["slack_log_message"])
                logger.debug(
                    f"Finished post new log message for alert_group {alert_group.pk}, "
                    f"slack_log_message with pk '{slack_log_message.pk}' was created."
                )
        else:
            self.update_log_message(alert_group)

    def update_log_message(self, alert_group):
        slack_message = alert_group.get_slack_message()

        if slack_message is None:
            logger.info(
                f"Cannot update log message for alert_group {alert_group.pk} because SlackMessage doesn't exist"
            )
            return None

        slack_log_message = alert_group.slack_log_message

        if slack_log_message is not None:
            # prevent too frequent updates
            if timezone.now() <= slack_log_message.last_updated + timezone.timedelta(seconds=5):
                return

            attachments = AlertGroupLogSlackRenderer.render_incident_log_report_for_slack(alert_group)
            logger.debug(
                f"Update log message for alert_group {alert_group.pk}, slack_log_message {slack_log_message.pk}"
            )
            try:
                self._slack_client.api_call(
                    "chat.update",
                    channel=slack_message.channel_id,
                    text="Alert Group log",
                    ts=slack_log_message.slack_id,
                    attachments=attachments,
                )
            except SlackAPITokenException as e:
                print(e)
            except SlackAPIRateLimitException as e:
                if not alert_group.channel.is_rate_limited_in_slack:
                    delay = e.response.get("rate_limit_delay") or SLACK_RATE_LIMIT_DELAY
                    alert_group.channel.start_send_rate_limit_message_task(delay)
                    logger.info(
                        f"Log message has not been updated for alert_group {alert_group.pk} due to slack rate limit."
                    )
            except SlackAPIException as e:
                if e.response["error"] == "message_not_found":
                    alert_group.slack_log_message = None
                    alert_group.save(update_fields=["slack_log_message"])
                elif e.response["error"] == "channel_not_found":
                    pass
                elif e.response["error"] == "is_archived":
                    pass
                elif e.response["error"] == "is_inactive":
                    pass
                elif e.response["error"] == "account_inactive":
                    pass
                elif e.response["error"] == "invalid_auth":
                    pass
                else:
                    raise e
            else:
                slack_log_message.last_updated = timezone.now()
                slack_log_message.save(update_fields=["last_updated"])
                logger.debug(
                    f"Finished update log message for alert_group {alert_group.pk}, "
                    f"slack_log_message {slack_log_message.pk}"
                )
        # check how much time has passed since slack message was created
        # to prevent eternal loop of restarting update log message task
        elif timezone.now() <= slack_message.created_at + timezone.timedelta(minutes=5):
            logger.debug(
                f"Update log message failed for alert_group {alert_group.pk}: "
                f"log message does not exist yet. Restarting post_or_update_log_report_message_task..."
            )
            post_or_update_log_report_message_task.apply_async(
                (alert_group.pk, self.slack_team_identity.pk, True),
                countdown=3,
            )
        else:
            logger.debug(f"Update log message failed for alert_group {alert_group.pk}: " f"log message does not exist.")


STEPS_ROUTING = [
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
        "action_type": scenario_step.ACTION_TYPE_BUTTON,
        "action_name": ResolveGroupStep.routing_uid(),
        "step": ResolveGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_BUTTON,
        "block_action_id": ResolveGroupStep.routing_uid(),
        "step": ResolveGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_BUTTON,
        "block_action_id": UnResolveGroupStep.routing_uid(),
        "step": UnResolveGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
        "action_type": scenario_step.ACTION_TYPE_BUTTON,
        "action_name": AcknowledgeGroupStep.routing_uid(),
        "step": AcknowledgeGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_BUTTON,
        "block_action_id": AcknowledgeGroupStep.routing_uid(),
        "step": AcknowledgeGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
        "action_type": scenario_step.ACTION_TYPE_BUTTON,
        "action_name": AcknowledgeConfirmationStep.routing_uid(),
        "step": AcknowledgeConfirmationStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
        "action_type": scenario_step.ACTION_TYPE_BUTTON,
        "action_name": UnAcknowledgeGroupStep.routing_uid(),
        "step": UnAcknowledgeGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_BUTTON,
        "block_action_id": UnAcknowledgeGroupStep.routing_uid(),
        "step": UnAcknowledgeGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
        "action_type": scenario_step.ACTION_TYPE_SELECT,
        "action_name": SilenceGroupStep.routing_uid(),
        "step": SilenceGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_STATIC_SELECT,
        "block_action_id": SilenceGroupStep.routing_uid(),
        "step": SilenceGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
        "action_type": scenario_step.ACTION_TYPE_BUTTON,
        "action_name": UnSilenceGroupStep.routing_uid(),
        "step": UnSilenceGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_BUTTON,
        "block_action_id": UnSilenceGroupStep.routing_uid(),
        "step": UnSilenceGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_BUTTON,
        "block_action_id": SelectAttachGroupStep.routing_uid(),
        "step": SelectAttachGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
        "action_type": scenario_step.ACTION_TYPE_SELECT,
        "action_name": AttachGroupStep.routing_uid(),
        "step": AttachGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_VIEW_SUBMISSION,
        "view_callback_id": AttachGroupStep.routing_uid(),
        "step": AttachGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_STATIC_SELECT,
        "block_action_id": AttachGroupStep.routing_uid(),
        "step": AttachGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
        "action_type": scenario_step.ACTION_TYPE_BUTTON,
        "action_name": UnAttachGroupStep.routing_uid(),
        "step": UnAttachGroupStep,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
        "action_type": scenario_step.ACTION_TYPE_SELECT,
        "action_name": InviteOtherPersonToIncident.routing_uid(),
        "step": InviteOtherPersonToIncident,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_USERS_SELECT,
        "block_action_id": InviteOtherPersonToIncident.routing_uid(),
        "step": InviteOtherPersonToIncident,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_BLOCK_ACTIONS,
        "block_action_type": scenario_step.BLOCK_ACTION_TYPE_STATIC_SELECT,
        "block_action_id": InviteOtherPersonToIncident.routing_uid(),
        "step": InviteOtherPersonToIncident,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
        "action_type": scenario_step.ACTION_TYPE_BUTTON,
        "action_name": StopInvitationProcess.routing_uid(),
        "step": StopInvitationProcess,
    },
    {
        "payload_type": scenario_step.PAYLOAD_TYPE_INTERACTIVE_MESSAGE,
        "action_type": scenario_step.ACTION_TYPE_BUTTON,
        "action_name": CustomButtonProcessStep.routing_uid(),
        "step": CustomButtonProcessStep,
    },
]
