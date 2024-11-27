import json
import logging
import typing
from datetime import datetime

from apps.alerts.constants import ActionSource
from apps.alerts.incident_appearance.renderers.constants import DEFAULT_BACKUP_TITLE
from apps.alerts.incident_appearance.renderers.slack_renderer import AlertSlackRenderer
from apps.alerts.models import Alert, AlertGroup, AlertGroupLogRecord, AlertReceiveChannel, Invitation
from apps.api.permissions import RBACPermission
from apps.slack.chatops_proxy_routing import make_private_metadata, make_value
from apps.slack.errors import (
    SlackAPIChannelArchivedError,
    SlackAPIChannelNotFoundError,
    SlackAPIError,
    SlackAPIInvalidAuthError,
    SlackAPIMessageNotFoundError,
    SlackAPIRatelimitError,
    SlackAPIRestrictedActionError,
    SlackAPITokenError,
)
from apps.slack.models import SlackChannel, SlackTeamIdentity, SlackUserIdentity
from apps.slack.scenarios import scenario_step
from apps.slack.slack_formatter import SlackFormatter
from apps.slack.tasks import send_message_to_thread_if_bot_not_in_channel
from apps.slack.types import (
    Block,
    BlockActionType,
    CompositionObjectOption,
    EventPayload,
    InteractiveMessageActionType,
    ModalView,
    PayloadType,
    ScenarioRoute,
)
from common.utils import clean_markup, is_string_with_visible_characters

from .step_mixins import AlertGroupActionsMixin

if typing.TYPE_CHECKING:
    from apps.user_management.models import Organization

ATTACH_TO_ALERT_GROUPS_LIMIT = 20

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AlertShootingStep(scenario_step.ScenarioStep):
    def process_signal(self, alert: Alert) -> None:
        # do not try to post alert group message to slack if its channel is rate limited
        if alert.group.channel.is_rate_limited_in_slack:
            logger.info("Skip posting or updating alert_group in Slack due to rate limit")
            AlertGroup.objects.filter(
                pk=alert.group.pk,
                slack_message_sent=False,
            ).update(slack_message_sent=True, reason_to_skip_escalation=AlertGroup.RATE_LIMITED)
            return

        num_updated_rows = AlertGroup.objects.filter(pk=alert.group.pk, slack_message_sent=False).update(
            slack_message_sent=True
        )

        if num_updated_rows == 1:
            try:
                slack_channel = (
                    alert.group.channel_filter.slack_channel
                    if alert.group.channel_filter
                    # if channel filter is deleted mid escalation, use default Slack channel
                    else alert.group.channel.organization.default_slack_channel
                )
                self._send_first_alert(alert, slack_channel)
            except (SlackAPIError, TimeoutError):
                AlertGroup.objects.filter(pk=alert.group.pk).update(slack_message_sent=False)
                raise

            if alert.group.channel.maintenance_mode == AlertReceiveChannel.DEBUG_MAINTENANCE:
                self._send_debug_mode_notice(alert.group, slack_channel)

            if alert.group.is_maintenance_incident:
                # not sending log report message for maintenance incident
                pass
            else:
                # check if alert group was posted to slack before posting message to thread
                if not alert.group.skip_escalation_in_slack:
                    self._send_message_to_thread_if_bot_not_in_channel(alert.group, slack_channel)
        else:
            # check if alert group was posted to slack before updating its message
            alert_group = alert.group
            if not alert_group:
                # this case should hypothetically never happen, it's mostly to appease mypy with the
                # fact that alert.group can "technically" be None
                logger.info(
                    f"Skip updating alert group in Slack because alert {alert.pk} doesn't actually "
                    "have an alert group associated with it"
                )
                return

            alert_group_slack_message = alert_group.slack_message
            if not alert_group_slack_message:
                logger.info(
                    f"Skip updating alert group in Slack because alert_group {alert_group.pk} doesn't "
                    "have a slack message associated with it"
                )
                return

            alert_group_slack_message.update_alert_groups_message()

    def _send_first_alert(self, alert: Alert, slack_channel: typing.Optional[SlackChannel]) -> None:
        self._post_alert_group_to_slack(
            slack_team_identity=self.slack_team_identity,
            alert_group=alert.group,
            alert=alert,
            attachments=alert.group.render_slack_attachments(),
            slack_channel=slack_channel,
            blocks=alert.group.render_slack_blocks(),
        )

    def _post_alert_group_to_slack(
        self,
        slack_team_identity: SlackTeamIdentity,
        alert_group: AlertGroup,
        alert: Alert,
        attachments,
        slack_channel: typing.Optional[SlackChannel],
        blocks: Block.AnyBlocks,
    ) -> None:
        # slack_channel can be None if org default slack channel for slack_team_identity is not set
        if slack_channel is None:
            logger.info(
                f"Failed to post message to Slack for alert_group {alert_group.pk} because slack_channel is None"
            )

            alert_group.reason_to_skip_escalation = AlertGroup.CHANNEL_NOT_SPECIFIED
            alert_group.save(update_fields=["reason_to_skip_escalation"])

            return

        try:
            result = self._slack_client.chat_postMessage(
                channel=slack_channel.slack_id,
                attachments=attachments,
                blocks=blocks,
            )

            # TODO: once _channel_id has been fully migrated to channel, remove _channel_id
            # see https://raintank-corp.slack.com/archives/C06K1MQ07GS/p1732555465144099
            alert_group.slack_messages.create(
                slack_id=result["ts"],
                organization=alert_group.channel.organization,
                _channel_id=slack_channel.slack_id,
                channel=slack_channel,
            )

            alert.delivered = True
        except SlackAPITokenError:
            alert_group.reason_to_skip_escalation = AlertGroup.ACCOUNT_INACTIVE
            alert_group.save(update_fields=["reason_to_skip_escalation"])
            logger.info("Not delivering alert due to account_inactive.")
        except SlackAPIInvalidAuthError:
            alert_group.reason_to_skip_escalation = AlertGroup.INVALID_AUTH
            alert_group.save(update_fields=["reason_to_skip_escalation"])
            logger.info("Not delivering alert due to invalid_auth.")
        except SlackAPIChannelArchivedError:
            alert_group.reason_to_skip_escalation = AlertGroup.CHANNEL_ARCHIVED
            alert_group.save(update_fields=["reason_to_skip_escalation"])
            logger.info("Not delivering alert due to channel is archived.")
        except SlackAPIRatelimitError as e:
            # don't rate limit maintenance alert
            if not alert_group.channel.is_maintenace_integration:
                alert_group.reason_to_skip_escalation = AlertGroup.RATE_LIMITED
                alert_group.save(update_fields=["reason_to_skip_escalation"])
                alert_group.channel.start_send_rate_limit_message_task("Delivering", e.retry_after)
                logger.info("Not delivering alert due to slack rate limit.")
            else:
                raise e
        except SlackAPIChannelNotFoundError:
            alert_group.reason_to_skip_escalation = AlertGroup.CHANNEL_ARCHIVED
            alert_group.save(update_fields=["reason_to_skip_escalation"])
            logger.info("Not delivering alert due to channel is archived.")
        except SlackAPIRestrictedActionError:
            alert_group.reason_to_skip_escalation = AlertGroup.RESTRICTED_ACTION
            alert_group.save(update_fields=["reason_to_skip_escalation"])
            logger.info("Not delivering alert due to workspace restricted action.")
        finally:
            alert.save()

    def _send_debug_mode_notice(self, alert_group: AlertGroup, slack_channel: SlackChannel) -> None:
        blocks: Block.AnyBlocks = []

        text = "Escalations are silenced due to Debug mode"
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": text}})

        self._slack_client.chat_postMessage(
            channel=slack_channel.slack_id,
            text=text,
            attachments=[],
            thread_ts=alert_group.slack_message.slack_id,
            mrkdwn=True,
            blocks=blocks,
        )

    def _send_message_to_thread_if_bot_not_in_channel(
        self,
        alert_group: AlertGroup,
        slack_channel: SlackChannel,
    ) -> None:
        send_message_to_thread_if_bot_not_in_channel.apply_async(
            (alert_group.pk, self.slack_team_identity.pk, slack_channel.slack_id),
            countdown=1,  # delay for message so that the log report is published first
        )

    def process_scenario(
        self,
        slack_user_identity: SlackUserIdentity,
        slack_team_identity: SlackTeamIdentity,
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        pass


class InviteOtherPersonToIncident(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    """
    THIS SCENARIO STEP IS DEPRECATED AND WILL BE REMOVED IN THE FUTURE.
    Check out apps/slack/scenarios/manage_responders.py for the new version that uses direct paging.
    """

    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.ALERT_GROUPS_WRITE]

    def process_scenario(
        self,
        slack_user_identity: SlackUserIdentity,
        slack_team_identity: SlackTeamIdentity,
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        from apps.user_management.models import User

        alert_group = self.get_alert_group(slack_team_identity, payload)
        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        selected_user = None

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
            alert_group.slack_message.update_alert_groups_message()

    def process_signal(self, log_record: AlertGroupLogRecord) -> None:
        log_record.alert_group.slack_message.update_alert_groups_message()


class SilenceGroupStep(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.ALERT_GROUPS_WRITE]

    def process_scenario(
        self,
        slack_user_identity: SlackUserIdentity,
        slack_team_identity: SlackTeamIdentity,
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        alert_group = self.get_alert_group(slack_team_identity, payload)
        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        value = payload["actions"][0]["selected_option"]["value"]
        try:
            silence_delay = json.loads(value)["delay"]
        except TypeError:
            # Deprecated handler kept for backward compatibility (so older Slack messages can still be processed)
            silence_delay = int(value)

        alert_group.silence_by_user_or_backsync(
            self.user, silence_delay=silence_delay, action_source=ActionSource.SLACK
        )

    def process_signal(self, log_record: AlertGroupLogRecord) -> None:
        log_record.alert_group.slack_message.update_alert_groups_message()


class UnSilenceGroupStep(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.ALERT_GROUPS_WRITE]

    def process_scenario(
        self,
        slack_user_identity: SlackUserIdentity,
        slack_team_identity: SlackTeamIdentity,
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        alert_group = self.get_alert_group(slack_team_identity, payload)
        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        alert_group.un_silence_by_user_or_backsync(self.user, action_source=ActionSource.SLACK)

    def process_signal(self, log_record: AlertGroupLogRecord) -> None:
        log_record.alert_group.slack_message.update_alert_groups_message()


class SelectAttachGroupStep(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.ALERT_GROUPS_WRITE]

    def process_scenario(
        self,
        slack_user_identity: SlackUserIdentity,
        slack_team_identity: SlackTeamIdentity,
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        alert_group = self.get_alert_group(slack_team_identity, payload)
        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        blocks: Block.AnyBlocks = []
        view: ModalView = {
            "callback_id": AttachGroupStep.routing_uid(),
            "blocks": blocks,
            "type": "modal",
            "title": {
                "type": "plain_text",
                "text": "Attach to Alert Group",
            },
            "private_metadata": make_private_metadata(
                {
                    "organization_id": self.organization.pk if self.organization else alert_group.organization.pk,
                    "alert_group_pk": alert_group.pk,
                },
                self.organization,
            ),
            "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        }
        attached_incidents_exists = alert_group.dependent_alert_groups.exists()
        if attached_incidents_exists:
            attached_incidents = alert_group.dependent_alert_groups.all()
            text = (
                f"Oops! This Alert Group cannot be attached to another one because it already has "
                f"attached Alert Group ({attached_incidents.count()}):\n"
            )
            for dependent_alert in attached_incidents:
                if dependent_alert.slack_permalink:
                    dependent_alert_text = (
                        f"\n<{dependent_alert.slack_permalink}|{dependent_alert.long_verbose_name_without_formatting}>"
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
                            "text": "Oops! There are no Alert Groups available to attach.",
                        },
                    }
                )
        self._slack_client.views_open(trigger_id=payload["trigger_id"], view=view)

    def get_select_incidents_blocks(self, alert_group: AlertGroup) -> Block.AnyBlocks:
        collected_options: typing.List[CompositionObjectOption] = []
        blocks: Block.AnyBlocks = []

        org = alert_group.channel.organization
        alert_receive_channel_ids = AlertReceiveChannel.objects.filter(organization=org).values_list("id", flat=True)

        alert_groups_queryset = (
            AlertGroup.objects.prefetch_related(
                "alerts",
                "channel__organization",
            )
            .filter(channel_id__in=list(alert_receive_channel_ids), resolved=False, root_alert_group__isnull=True)
            .exclude(pk=alert_group.pk)
            .order_by("-pk")
        )

        sf = SlackFormatter(org)
        for alert_group_to_attach in alert_groups_queryset[:ATTACH_TO_ALERT_GROUPS_LIMIT]:
            # long_verbose_name_without_formatting was removed from here because it increases queries count due to
            # alerts.first().
            # alert_group_to_attach.alerts.exists() and alerts.all()[0] don't make additional queries to db due to
            # prefetch_related.
            first_alert = alert_group_to_attach.alerts.all()[0]
            templated_alert = AlertSlackRenderer(first_alert).templated_alert
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
                    "value": make_value({root_ag_id_value_key: alert_group_to_attach.pk}, org),
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
                        "options": collected_options[:ATTACH_TO_ALERT_GROUPS_LIMIT],
                    },
                    "label": {
                        "type": "plain_text",
                        "text": "Select Alert Group:",
                        "emoji": True,
                    },
                }
            )
        return blocks


class AttachGroupStep(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    REQUIRED_PERMISSIONS = []  # Permissions are handled in SelectAttachGroupStep

    def process_signal(self, log_record: AlertGroupLogRecord) -> None:
        alert_group = log_record.alert_group

        if log_record.type == AlertGroupLogRecord.TYPE_ATTACHED and log_record.alert_group.is_maintenance_incident:
            text = f"{log_record.rendered_log_line_action(for_slack=True)}"
            self.alert_group_slack_service.publish_message_to_alert_group_thread(alert_group, text=text)

        if log_record.type == AlertGroupLogRecord.TYPE_FAILED_ATTACHMENT:
            ephemeral_text = log_record.rendered_log_line_action(for_slack=True)
            slack_user_identity = log_record.author.slack_user_identity

            if slack_user_identity:
                self._slack_client.chat_postEphemeral(
                    user=slack_user_identity.slack_id,
                    # TODO: once _channel_id has been fully migrated to channel, remove _channel_id
                    # see https://raintank-corp.slack.com/archives/C06K1MQ07GS/p173255546
                    # channel=alert_group.slack_message.channel.slack_id,
                    channel=alert_group.slack_message._channel_id,
                    text="{}{}".format(ephemeral_text[:1].upper(), ephemeral_text[1:]),
                    unfurl_links=True,
                )

        alert_group.slack_message.update_alert_groups_message()

    def process_scenario(
        self,
        slack_user_identity: SlackUserIdentity,
        slack_team_identity: SlackTeamIdentity,
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        # submit selection in modal window
        if payload["type"] == PayloadType.VIEW_SUBMISSION:
            alert_group_pk = json.loads(payload["view"]["private_metadata"])["alert_group_pk"]
            alert_group = AlertGroup.objects.get(pk=alert_group_pk)
            root_alert_group_pk = _get_root_alert_group_id_from_value(
                payload["view"]["state"]["values"][SelectAttachGroupStep.routing_uid()][AttachGroupStep.routing_uid()][
                    "selected_option"
                ]["value"]
            )
            root_alert_group = AlertGroup.objects.get(pk=root_alert_group_pk)
        # old version of attach selection by dropdown
        else:
            try:
                root_alert_group_pk = int(
                    _get_root_alert_group_id_from_value(payload["actions"][0]["selected_options"][0]["value"])
                )
            except KeyError:
                root_alert_group_pk = int(
                    _get_root_alert_group_id_from_value(payload["actions"][0]["selected_option"]["value"])
                )

            root_alert_group = AlertGroup.objects.get(pk=root_alert_group_pk)
            alert_group = self.get_alert_group(slack_team_identity, payload)

        alert_group.attach_by_user(self.user, root_alert_group, action_source=ActionSource.SLACK)


root_ag_id_value_key = "ag_id"


def _get_root_alert_group_id_from_value(value: str) -> str:
    """
    Extract ag ID from value string.
    It might be either JSON-encoded object or just a user ID.
    Json encoded object introduced for Chatops-Proxy routing, plain string with user ID is legacy.
    """
    try:
        data = json.loads(value)
        return data[root_ag_id_value_key]
    except json.JSONDecodeError:
        return value


class UnAttachGroupStep(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.ALERT_GROUPS_WRITE]

    def process_scenario(
        self,
        slack_user_identity: SlackUserIdentity,
        slack_team_identity: SlackTeamIdentity,
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        alert_group = self.get_alert_group(slack_team_identity, payload)
        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        alert_group.un_attach_by_user(self.user, action_source=ActionSource.SLACK)

    def process_signal(self, log_record: AlertGroupLogRecord) -> None:
        log_record.alert_group.slack_message.update_alert_groups_message()


class StopInvitationProcess(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    """
    THIS SCENARIO STEP IS DEPRECATED AND WILL BE REMOVED IN THE FUTURE.
    Check out apps/slack/scenarios/manage_responders.py for the new version that uses direct paging.
    """

    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.ALERT_GROUPS_WRITE]

    def process_scenario(
        self,
        slack_user_identity: SlackUserIdentity,
        slack_team_identity: SlackTeamIdentity,
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        alert_group = self.get_alert_group(slack_team_identity, payload)
        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        try:
            value = json.loads(payload["actions"][0]["value"])
            invitation_id = value["invitation_id"]
        except KeyError:
            # Deprecated handler kept for backward compatibility (so older Slack messages can still be processed)
            invitation_id = payload["actions"][0]["name"].split("_")[1]

        Invitation.stop_invitation(invitation_id, self.user)

    def process_signal(self, log_record: AlertGroupLogRecord) -> None:
        log_record.alert_group.slack_message.update_alert_groups_message()


class ResolveGroupStep(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.ALERT_GROUPS_WRITE]

    def process_scenario(
        self,
        slack_user_identity: SlackUserIdentity,
        slack_team_identity: SlackTeamIdentity,
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        ResolutionNoteModalStep = scenario_step.ScenarioStep.get_step("resolution_note", "ResolutionNoteModalStep")

        alert_group = self.get_alert_group(slack_team_identity, payload)
        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        if alert_group.is_maintenance_incident:
            alert_group.stop_maintenance(self.user)
        else:
            # TODO: refactor that check, it should be in alert core, not in slack.
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

            alert_group.resolve_by_user_or_backsync(self.user, action_source=ActionSource.SLACK)

    def process_signal(self, log_record: AlertGroupLogRecord) -> None:
        # Do not rerender alert_groups which happened while maintenance.
        # They have no slack messages, since they just attached to the maintenance incident.
        if not log_record.alert_group.happened_while_maintenance:
            log_record.alert_group.slack_message.update_alert_groups_message()


class UnResolveGroupStep(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.ALERT_GROUPS_WRITE]

    def process_scenario(
        self,
        slack_user_identity: SlackUserIdentity,
        slack_team_identity: SlackTeamIdentity,
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        alert_group = self.get_alert_group(slack_team_identity, payload)
        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        alert_group.un_resolve_by_user_or_backsync(self.user, action_source=ActionSource.SLACK)

    def process_signal(self, log_record: AlertGroupLogRecord) -> None:
        log_record.alert_group.slack_message.update_alert_groups_message()


class AcknowledgeGroupStep(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.ALERT_GROUPS_WRITE]

    def process_scenario(
        self,
        slack_user_identity: SlackUserIdentity,
        slack_team_identity: SlackTeamIdentity,
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        alert_group = self.get_alert_group(slack_team_identity, payload)
        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        alert_group.acknowledge_by_user_or_backsync(self.user, action_source=ActionSource.SLACK)

    def process_signal(self, log_record: AlertGroupLogRecord) -> None:
        log_record.alert_group.slack_message.update_alert_groups_message()


class UnAcknowledgeGroupStep(AlertGroupActionsMixin, scenario_step.ScenarioStep):
    REQUIRED_PERMISSIONS = [RBACPermission.Permissions.ALERT_GROUPS_WRITE]

    def process_scenario(
        self,
        slack_user_identity: SlackUserIdentity,
        slack_team_identity: SlackTeamIdentity,
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        alert_group = self.get_alert_group(slack_team_identity, payload)
        if not self.is_authorized(alert_group):
            self.open_unauthorized_warning(payload)
            return

        alert_group.un_acknowledge_by_user_or_backsync(self.user, action_source=ActionSource.SLACK)

    def process_signal(self, log_record: AlertGroupLogRecord) -> None:
        from apps.alerts.models import AlertGroupLogRecord

        alert_group = log_record.alert_group
        slack_message = alert_group.slack_message

        logger.debug(f"Started process_signal in UnAcknowledgeGroupStep for alert_group {alert_group.pk}")

        if log_record.type == AlertGroupLogRecord.TYPE_AUTO_UN_ACK:
            if log_record.author is not None:
                user_verbal = log_record.author.get_username_with_slack_verbal(mention=True)
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
                f" Alert Group is unacknowledged automatically."
            )

            if slack_message.ack_reminder_message_ts:
                try:
                    self._slack_client.chat_update(
                        # TODO: once _channel_id has been fully migrated to channel, remove _channel_id
                        # see https://raintank-corp.slack.com/archives/C06K1MQ07GS/p173255546
                        # channel=slack_message.channel.slack_id,
                        channel=slack_message._channel_id,
                        ts=slack_message.ack_reminder_message_ts,
                        text=text,
                        attachments=message_attachments,
                    )
                except SlackAPIMessageNotFoundError:
                    # post to thread if ack reminder message was deleted in Slack
                    self.alert_group_slack_service.publish_message_to_alert_group_thread(
                        alert_group, attachments=message_attachments, text=text
                    )
                except SlackAPITokenError:
                    pass
            else:
                self.alert_group_slack_service.publish_message_to_alert_group_thread(
                    alert_group, attachments=message_attachments, text=text
                )

        slack_message.update_alert_groups_message()
        logger.debug(f"Finished process_signal in UnAcknowledgeGroupStep for alert_group {alert_group.pk}")


class AcknowledgeConfirmationStep(AcknowledgeGroupStep):
    def process_scenario(
        self,
        slack_user_identity: SlackUserIdentity,
        slack_team_identity: SlackTeamIdentity,
        payload: "EventPayload",
        predefined_org: typing.Optional["Organization"] = None,
    ) -> None:
        from apps.alerts.models import AlertGroup

        value = payload["actions"][0]["value"]
        try:
            alert_group_pk = json.loads(value)["alert_group_pk"]
        except json.JSONDecodeError:
            # Deprecated and kept for backward compatibility (so older Slack messages can still be processed)
            alert_group_pk = value.split("_")[1]

        alert_group = AlertGroup.objects.get(pk=alert_group_pk)
        channel = payload["channel"]["id"]
        message_ts = payload["message_ts"]

        if alert_group.acknowledged:
            if alert_group.acknowledged_by == AlertGroup.USER:
                if self.user == alert_group.acknowledged_by_user:
                    user_verbal = alert_group.acknowledged_by_user.get_username_with_slack_verbal()
                    text = f"{user_verbal} confirmed that the Alert Group is still acknowledged."
                    self._slack_client.chat_update(channel=channel, ts=message_ts, text=text)
                    alert_group.acknowledged_by_confirmed = datetime.utcnow()
                    alert_group.save(update_fields=["acknowledged_by_confirmed"])
                else:
                    self._slack_client.chat_postEphemeral(
                        channel=channel,
                        user=slack_user_identity.slack_id,
                        text="This Alert Group is acknowledged by another user. Acknowledge it yourself first.",
                    )
            elif alert_group.acknowledged_by == AlertGroup.SOURCE:
                user_verbal = self.user.get_username_with_slack_verbal()
                text = f"{user_verbal} confirmed that the Alert Group is still acknowledged."
                self._slack_client.chat_update(channel=channel, ts=message_ts, text=text)
                alert_group.acknowledged_by_confirmed = datetime.utcnow()
                alert_group.save(update_fields=["acknowledged_by_confirmed"])
        else:
            self._slack_client.chat_delete(channel=channel, ts=message_ts)
            self._slack_client.chat_postEphemeral(
                channel=channel,
                user=slack_user_identity.slack_id,
                text="This Alert Group is already unacknowledged.",
            )

    def process_signal(self, log_record: AlertGroupLogRecord) -> None:
        from apps.user_management.models import Organization

        alert_group = log_record.alert_group
        organization = alert_group.channel.organization
        slack_message = alert_group.slack_message
        slack_channel = slack_message.channel

        user_verbal = log_record.author.get_username_with_slack_verbal(mention=True)
        text = f"{user_verbal}, please confirm that you're still working on this Alert Group."

        if organization.unacknowledge_timeout != Organization.UNACKNOWLEDGE_TIMEOUT_NEVER:
            try:
                response = self._slack_client.chat_postMessage(
                    channel=slack_channel.slack_id,
                    text=text,
                    attachments=[
                        {
                            "fallback": "Are you still working on this Alert Group?",
                            "text": text,
                            "callback_id": "alert",
                            "attachment_type": "default",
                            "footer": "This is a reminder that the Alert Group is still acknowledged"
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
                                    "value": make_value({"alert_group_pk": alert_group.pk}, organization),
                                },
                            ],
                        }
                    ],
                    thread_ts=slack_message.slack_id,
                )
            except (SlackAPITokenError, SlackAPIChannelArchivedError, SlackAPIChannelNotFoundError):
                pass
            else:
                # TODO: once _channel_id has been fully migrated to channel, remove _channel_id
                # see https://raintank-corp.slack.com/archives/C06K1MQ07GS/p1732555465144099
                alert_group.slack_messages.create(
                    slack_id=response["ts"],
                    organization=organization,
                    _channel_id=slack_channel.slack_id,
                    channel=slack_channel,
                )

                slack_message.ack_reminder_message_ts = response["ts"]
                slack_message.save(update_fields=["ack_reminder_message_ts"])
        else:
            text = f"This is a reminder that the Alert Group is still acknowledged by {user_verbal}"
            self.alert_group_slack_service.publish_message_to_alert_group_thread(alert_group, text=text)


class WipeGroupStep(scenario_step.ScenarioStep):
    def process_signal(self, log_record: AlertGroupLogRecord) -> None:
        alert_group = log_record.alert_group

        self.alert_group_slack_service.publish_message_to_alert_group_thread(
            alert_group,
            text=f"Wiped by {log_record.author.get_username_with_slack_verbal()}",
        )
        alert_group.slack_message.update_alert_groups_message()


class DeleteGroupStep(scenario_step.ScenarioStep):
    def process_signal(self, log_record: AlertGroupLogRecord) -> None:
        alert_group = log_record.alert_group

        # Remove "memo" emoji from resolution note messages
        for message in alert_group.resolution_note_slack_messages.filter(added_to_resolution_note=True):
            try:
                self._slack_client.reactions_remove(
                    channel=message.slack_channel_slack_id, name="memo", timestamp=message.ts
                )
            except SlackAPIRatelimitError:
                # retries on ratelimit are handled in apps.alerts.tasks.delete_alert_group.delete_alert_group
                raise
            except SlackAPIError:
                pass
            message.delete()

        # Remove resolution note messages posted by OnCall bot
        for message in alert_group.resolution_note_slack_messages.filter(posted_by_bot=True):
            try:
                self._slack_client.chat_delete(channel=message.slack_channel_slack_id, ts=message.ts)
            except SlackAPIRatelimitError:
                # retries on ratelimit are handled in apps.alerts.tasks.delete_alert_group.delete_alert_group
                raise
            except SlackAPIError:
                pass
            message.delete()

        # Remove alert group Slack messages
        for message in alert_group.slack_messages.all():
            try:
                self._slack_client.chat_delete(
                    # TODO: once _channel_id has been fully migrated to channel, remove _channel_id
                    # see https://raintank-corp.slack.com/archives/C06K1MQ07GS/p173255546
                    # channel=message.channel.slack_id,
                    channel=message._channel_id,
                    ts=message.slack_id,
                )
            except SlackAPIRatelimitError:
                # retries on ratelimit are handled in apps.alerts.tasks.delete_alert_group.delete_alert_group
                raise
            except SlackAPIError:
                pass
            message.delete()


STEPS_ROUTING: ScenarioRoute.RoutingSteps = [
    {
        "payload_type": PayloadType.INTERACTIVE_MESSAGE,
        "action_type": InteractiveMessageActionType.BUTTON,
        "action_name": ResolveGroupStep.routing_uid(),
        "step": ResolveGroupStep,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": ResolveGroupStep.routing_uid(),
        "step": ResolveGroupStep,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": UnResolveGroupStep.routing_uid(),
        "step": UnResolveGroupStep,
    },
    {
        "payload_type": PayloadType.INTERACTIVE_MESSAGE,
        "action_type": InteractiveMessageActionType.BUTTON,
        "action_name": AcknowledgeGroupStep.routing_uid(),
        "step": AcknowledgeGroupStep,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": AcknowledgeGroupStep.routing_uid(),
        "step": AcknowledgeGroupStep,
    },
    {
        "payload_type": PayloadType.INTERACTIVE_MESSAGE,
        "action_type": InteractiveMessageActionType.BUTTON,
        "action_name": AcknowledgeConfirmationStep.routing_uid(),
        "step": AcknowledgeConfirmationStep,
    },
    {
        "payload_type": PayloadType.INTERACTIVE_MESSAGE,
        "action_type": InteractiveMessageActionType.BUTTON,
        "action_name": UnAcknowledgeGroupStep.routing_uid(),
        "step": UnAcknowledgeGroupStep,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": UnAcknowledgeGroupStep.routing_uid(),
        "step": UnAcknowledgeGroupStep,
    },
    {
        "payload_type": PayloadType.INTERACTIVE_MESSAGE,
        "action_type": InteractiveMessageActionType.SELECT,
        "action_name": SilenceGroupStep.routing_uid(),
        "step": SilenceGroupStep,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.STATIC_SELECT,
        "block_action_id": SilenceGroupStep.routing_uid(),
        "step": SilenceGroupStep,
    },
    {
        "payload_type": PayloadType.INTERACTIVE_MESSAGE,
        "action_type": InteractiveMessageActionType.BUTTON,
        "action_name": UnSilenceGroupStep.routing_uid(),
        "step": UnSilenceGroupStep,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": UnSilenceGroupStep.routing_uid(),
        "step": UnSilenceGroupStep,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.BUTTON,
        "block_action_id": SelectAttachGroupStep.routing_uid(),
        "step": SelectAttachGroupStep,
    },
    {
        "payload_type": PayloadType.INTERACTIVE_MESSAGE,
        "action_type": InteractiveMessageActionType.SELECT,
        "action_name": AttachGroupStep.routing_uid(),
        "step": AttachGroupStep,
    },
    {
        "payload_type": PayloadType.VIEW_SUBMISSION,
        "view_callback_id": AttachGroupStep.routing_uid(),
        "step": AttachGroupStep,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.STATIC_SELECT,
        "block_action_id": AttachGroupStep.routing_uid(),
        "step": AttachGroupStep,
    },
    {
        "payload_type": PayloadType.INTERACTIVE_MESSAGE,
        "action_type": InteractiveMessageActionType.BUTTON,
        "action_name": UnAttachGroupStep.routing_uid(),
        "step": UnAttachGroupStep,
    },
    {
        "payload_type": PayloadType.INTERACTIVE_MESSAGE,
        "action_type": InteractiveMessageActionType.SELECT,
        "action_name": InviteOtherPersonToIncident.routing_uid(),
        "step": InviteOtherPersonToIncident,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.USERS_SELECT,
        "block_action_id": InviteOtherPersonToIncident.routing_uid(),
        "step": InviteOtherPersonToIncident,
    },
    {
        "payload_type": PayloadType.BLOCK_ACTIONS,
        "block_action_type": BlockActionType.STATIC_SELECT,
        "block_action_id": InviteOtherPersonToIncident.routing_uid(),
        "step": InviteOtherPersonToIncident,
    },
    {
        "payload_type": PayloadType.INTERACTIVE_MESSAGE,
        "action_type": InteractiveMessageActionType.BUTTON,
        "action_name": StopInvitationProcess.routing_uid(),
        "step": StopInvitationProcess,
    },
]
