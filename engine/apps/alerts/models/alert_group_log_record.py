import json
import logging
import typing

import humanize
from django.db import models
from django.db.models import JSONField
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.fields import DateTimeField

from apps.alerts import tasks
from apps.alerts.utils import render_relative_timeline
from apps.slack.slack_formatter import SlackFormatter
from common.utils import clean_markup

if typing.TYPE_CHECKING:
    from apps.alerts.models import AlertGroup, CustomButton, EscalationPolicy, Invitation
    from apps.user_management.models import User

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class AlertGroupLogRecord(models.Model):
    alert_group: "AlertGroup"
    author: typing.Optional["User"]
    custom_button: typing.Optional["CustomButton"]
    dependent_alert_group: typing.Optional["AlertGroup"]
    escalation_policy: typing.Optional["EscalationPolicy"]
    invitation: typing.Optional["Invitation"]
    root_alert_group: typing.Optional["AlertGroup"]

    (
        TYPE_ACK,
        TYPE_UN_ACK,
        TYPE_INVITE,
        TYPE_STOP_INVITATION,
        TYPE_RE_INVITE,
        TYPE_ESCALATION_TRIGGERED,
        TYPE_INVITATION_TRIGGERED,
        TYPE_SILENCE,
        TYPE_ATTACHED,
        TYPE_UNATTACHED,
        TYPE_CUSTOM_BUTTON_TRIGGERED,
        TYPE_AUTO_UN_ACK,
        TYPE_FAILED_ATTACHMENT,
        TYPE_RESOLVED,
        TYPE_UN_RESOLVED,
        TYPE_UN_SILENCE,
        TYPE_ESCALATION_FINISHED,
        TYPE_ESCALATION_FAILED,
        TYPE_ACK_REMINDER_TRIGGERED,
        TYPE_WIPED,
        TYPE_DELETED,
        TYPE_REGISTERED,
        TYPE_ROUTE_ASSIGNED,
        TYPE_DIRECT_PAGING,
        TYPE_UNPAGE_USER,
        TYPE_RESTRICTED,
    ) = range(26)

    TYPES_FOR_LICENCE_CALCULATION = (
        TYPE_ACK,
        TYPE_UN_ACK,
        TYPE_INVITE,
        TYPE_STOP_INVITATION,
        TYPE_RE_INVITE,
        TYPE_SILENCE,
        TYPE_ATTACHED,
        TYPE_UNATTACHED,
        TYPE_CUSTOM_BUTTON_TRIGGERED,
        TYPE_FAILED_ATTACHMENT,
        TYPE_RESOLVED,
        TYPE_UN_RESOLVED,
        TYPE_UN_SILENCE,
    )

    TYPE_CHOICES = (
        (TYPE_ACK, "Acknowledged"),
        (TYPE_UN_ACK, "Unacknowledged"),
        (TYPE_INVITE, "Invite"),
        (TYPE_STOP_INVITATION, "Stop invitation"),
        (TYPE_RE_INVITE, "Re-invite"),
        (TYPE_ESCALATION_TRIGGERED, "Escalation triggered"),
        (TYPE_INVITATION_TRIGGERED, "Invitation triggered"),
        (TYPE_ESCALATION_FINISHED, "Escalation finished"),
        (TYPE_SILENCE, "Silenced"),
        (TYPE_UN_SILENCE, "Unsilenced"),
        (TYPE_ATTACHED, "Attached"),
        (TYPE_UNATTACHED, "Unattached"),
        (TYPE_CUSTOM_BUTTON_TRIGGERED, "Custom button triggered"),
        (TYPE_AUTO_UN_ACK, "Unacknowledged by timeout"),
        (TYPE_FAILED_ATTACHMENT, "Failed attachment"),
        (TYPE_RESOLVED, "Incident resolved"),
        (TYPE_UN_RESOLVED, "Incident unresolved"),
        (TYPE_ESCALATION_FAILED, "Escalation failed"),
        (TYPE_ACK_REMINDER_TRIGGERED, "Acknowledge reminder triggered"),
        (TYPE_WIPED, "Wiped"),
        (TYPE_DELETED, "Deleted"),
        (TYPE_REGISTERED, "Incident registered"),
        (TYPE_ROUTE_ASSIGNED, "A route is assigned to the incident"),
        (TYPE_DIRECT_PAGING, "Trigger direct paging escalation"),
        (TYPE_UNPAGE_USER, "Unpage a user"),
        (TYPE_RESTRICTED, "Restricted"),
    )

    # Handlers should be named like functions.
    ACTIONS_TO_HANDLERS_MAP = {
        TYPE_ACK: "acknowledge",
        TYPE_UN_ACK: "un_acknowledge",
        TYPE_INVITE: "invite",
        TYPE_STOP_INVITATION: "un_invite",
        TYPE_RE_INVITE: "re_invite",
        TYPE_ESCALATION_TRIGGERED: "escalation_triggered",
        TYPE_INVITATION_TRIGGERED: "invitation_triggered",
        TYPE_SILENCE: "silence",
        TYPE_UN_SILENCE: "un_silence",
        TYPE_ATTACHED: "attach",
        TYPE_UNATTACHED: "un_attach",
        TYPE_CUSTOM_BUTTON_TRIGGERED: "custom_button_triggered",
        TYPE_AUTO_UN_ACK: "auto_un_acknowledge",
        TYPE_FAILED_ATTACHMENT: "fail_attach",
        TYPE_RESOLVED: "resolve",
        TYPE_UN_RESOLVED: "un_resolve",
        TYPE_ESCALATION_FINISHED: "escalation_finished",
        TYPE_ESCALATION_FAILED: "escalation_failed",
        TYPE_ACK_REMINDER_TRIGGERED: "ack_reminder_triggered",
        TYPE_WIPED: "wiped",
        TYPE_DELETED: "deleted",
        TYPE_DIRECT_PAGING: "trigger_page",
        TYPE_UNPAGE_USER: "unpage_user",
    }
    (
        ERROR_ESCALATION_NOTIFY_USER_NO_RECIPIENT,
        ERROR_ESCALATION_NOTIFY_QUEUE_NO_RECIPIENTS,
        ERROR_ESCALATION_NOTIFY_MULTIPLE_NO_RECIPIENTS,
        ERROR_ESCALATION_SCHEDULE_DOES_NOT_EXIST,
        ERROR_ESCALATION_SCHEDULE_DOES_NOT_SELECTED,
        ERROR_ESCALATION_ICAL_IMPORT_FAILED,
        ERROR_ESCALATION_ICAL_NO_VALID_USERS,
        ERROR_ESCALATION_NO_SCHEDULE_IN_CHANNEL,
        ERROR_ESCALATION_WAIT_STEP_IS_NOT_CONFIGURED,
        ERROR_ESCALATION_NOTIFY_IF_TIME_IS_NOT_CONFIGURED,
        ERROR_ESCALATION_UNSPECIFIED_STEP,
        ERROR_ESCALATION_NOTIFY_GROUP_STEP_IS_NOT_CONFIGURED,
        ERROR_ESCALATION_USER_GROUP_IS_EMPTY,
        ERROR_ESCALATION_USER_GROUP_DOES_NOT_EXIST,
        ERROR_ESCALATION_TRIGGER_CUSTOM_BUTTON_STEP_IS_NOT_CONFIGURED,
        ERROR_ESCALATION_NOTIFY_IN_SLACK,
        ERROR_ESCALATION_NOTIFY_IF_NUM_ALERTS_IN_WINDOW_STEP_IS_NOT_CONFIGURED,
        ERROR_ESCALATION_TRIGGER_CUSTOM_WEBHOOK_ERROR,
    ) = range(18)

    type = models.IntegerField(choices=TYPE_CHOICES)

    author = models.ForeignKey(
        "user_management.User",
        on_delete=models.SET_NULL,
        related_name="log_records",
        default=None,
        null=True,
    )

    escalation_policy = models.ForeignKey(
        "alerts.EscalationPolicy", on_delete=models.SET_NULL, related_name="log_records", null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    alert_group = models.ForeignKey(
        "alerts.AlertGroup",
        on_delete=models.CASCADE,
        related_name="log_records",
    )
    root_alert_group = models.ForeignKey(
        "alerts.AlertGroup",
        on_delete=models.SET_NULL,
        related_name="root_log_records",
        default=None,
        null=True,
    )
    dependent_alert_group = models.ForeignKey(
        "alerts.AlertGroup",
        on_delete=models.SET_NULL,
        related_name="dependent_log_records",
        default=None,
        null=True,
    )
    invitation = models.ForeignKey(
        "alerts.Invitation",
        on_delete=models.SET_NULL,
        related_name="log_records",
        default=None,
        null=True,
    )
    custom_button = models.ForeignKey(
        "alerts.CustomButton",
        on_delete=models.SET_DEFAULT,
        related_name="log_records",
        default=None,
        null=True,
    )
    reason = models.TextField(null=True, default=None)

    silence_delay = models.DurationField(default=None, null=True)

    eta = models.DateTimeField(default=None, null=True)

    escalation_error_code = models.PositiveIntegerField(null=True, default=None)

    escalation_policy_step = models.IntegerField(null=True, default=None)
    step_specific_info = JSONField(null=True, default=None)

    STEP_SPECIFIC_INFO_KEYS = ["schedule_name", "custom_button_name", "usergroup_handle"]

    def render_log_line_json(self):
        time = humanize.naturaldelta(self.alert_group.started_at - self.created_at)
        created_at = DateTimeField().to_representation(self.created_at)
        author = self.author.short() if self.author is not None else None

        sf = SlackFormatter(self.alert_group.channel.organization)
        action = sf.format(self.rendered_log_line_action(substitute_author_with_tag=True))
        action = clean_markup(action)

        result = {
            "time": time,
            "action": action,
            "realm": "alert_group",
            "type": self.type,
            "created_at": created_at,
            "author": author,
        }
        return result

    def rendered_incident_log_line(self, for_slack=False, html=False):
        timeline = render_relative_timeline(self.created_at, self.alert_group.started_at)

        if html:
            result = f"<b>{timeline}:</b> "
        else:
            result = f"*{timeline}:* "

        result += self.rendered_log_line_action(for_slack=for_slack, html=html)
        return result

    def rendered_log_line_action(self, for_slack=False, html=False, substitute_author_with_tag=False):
        from apps.alerts.models import EscalationPolicy

        result = ""
        author_name = None
        invitee_name = None
        escalation_policy_step = None
        step_specific_info = self.get_step_specific_info()

        if self.escalation_policy_step is not None:
            escalation_policy_step = self.escalation_policy_step
        elif self.escalation_policy is not None:
            escalation_policy_step = self.escalation_policy.step

        if self.author is not None:
            if substitute_author_with_tag:
                author_name = "{{author}}"
            elif for_slack:
                author_name = self.author.get_username_with_slack_verbal()
            else:
                author_name = self.author.username
        if self.invitation is not None:
            if for_slack:
                invitee_name = self.invitation.invitee.get_username_with_slack_verbal()
            else:
                invitee_name = self.invitation.invitee.username

        if self.type == AlertGroupLogRecord.TYPE_REGISTERED:
            result += "alert group registered"
        elif self.type == AlertGroupLogRecord.TYPE_RESTRICTED:
            result += self.reason
        elif self.type == AlertGroupLogRecord.TYPE_ROUTE_ASSIGNED:
            channel_filter = self.alert_group.channel_filter_with_respect_to_escalation_snapshot
            escalation_chain = self.alert_group.escalation_chain_with_respect_to_escalation_snapshot

            if channel_filter is not None:
                result += f'alert group assigned to route "{channel_filter.str_for_clients}"'

                if escalation_chain is not None:
                    result += f' with escalation chain "{escalation_chain.name}"'
                else:
                    result += " with no escalation chain, skipping escalation"
            else:
                result += "alert group assigned to deleted route, skipping escalation"
        elif self.type == AlertGroupLogRecord.TYPE_ACK:
            result += f"acknowledged by {f'{author_name}' if author_name else 'alert source'}"
        elif self.type == AlertGroupLogRecord.TYPE_UN_ACK:
            result += f"unacknowledged by {author_name}"
        elif self.type == AlertGroupLogRecord.TYPE_AUTO_UN_ACK:
            result += "unacknowledged automatically"
        elif self.type == AlertGroupLogRecord.TYPE_INVITE:
            result += f"{author_name} activated invitation for {invitee_name}"
        elif self.type == AlertGroupLogRecord.TYPE_STOP_INVITATION:
            if self.invitation.invitee == self.author:
                result += f"{author_name} deactivated invitation"
            else:
                result += f"{author_name} deactivated invitation for {invitee_name}"
        elif self.type == AlertGroupLogRecord.TYPE_RE_INVITE:
            result += f"{author_name} restarted invitation for {invitee_name}"
        elif self.type == AlertGroupLogRecord.TYPE_INVITATION_TRIGGERED:
            pass  # moved to UserNotificationPolicyLogRecord
        elif self.type == AlertGroupLogRecord.TYPE_ESCALATION_TRIGGERED:
            if escalation_policy_step == EscalationPolicy.STEP_NOTIFY_IF_TIME:
                if self.eta is not None:
                    if for_slack:
                        result += "escalation stopped until <!date^{:.0f}^{{date}} {{time}}|notify_if_time>".format(
                            self.eta.timestamp()
                        )
                    else:
                        result += f"escalation stopped until {self.eta.strftime('%B %d %Y %H:%M:%S')} (UTC)"
                else:
                    result += 'triggered step "Continue escalation if time"'
            elif escalation_policy_step == EscalationPolicy.STEP_NOTIFY_IF_NUM_ALERTS_IN_TIME_WINDOW:
                is_step_configured = (
                    self.escalation_policy is not None
                    and self.escalation_policy.num_alerts_in_window is not None
                    and self.escalation_policy.num_minutes_in_window is not None
                )

                if is_step_configured:
                    num_alerts_in_window = self.escalation_policy.num_alerts_in_window
                    num_minutes_in_window = self.escalation_policy.num_minutes_in_window
                    result += (
                        f'triggered step "Continue escalation if >{num_alerts_in_window} alerts '
                        f'per {num_minutes_in_window} minutes"'
                    )
                else:
                    result += 'triggered step "Continue escalation if >X alerts per Y minutes"'

            elif escalation_policy_step in [
                EscalationPolicy.STEP_NOTIFY_GROUP,
                EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT,
            ]:
                usergroup_handle = ""
                if step_specific_info is not None:
                    usergroup_handle = step_specific_info.get("usergroup_handle", "")
                elif self.escalation_policy is not None and self.escalation_policy.notify_to_group is not None:
                    usergroup_handle = self.escalation_policy.notify_to_group.handle
                important_text = ""
                if escalation_policy_step == EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT:
                    important_text = " (Important)"
                result += f'triggered step "Notify @{usergroup_handle} User Group{important_text}"'
            elif escalation_policy_step in [
                EscalationPolicy.STEP_NOTIFY_SCHEDULE,
                EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT,
            ]:
                schedule_name = None
                if step_specific_info is not None:
                    schedule_name = step_specific_info.get("schedule_name", "")
                elif self.escalation_policy is not None and self.escalation_policy.notify_schedule is not None:
                    schedule_name = self.escalation_policy.notify_schedule.name
                schedule_name = f"'{schedule_name}'" if schedule_name else ""
                important_text = ""
                if escalation_policy_step == EscalationPolicy.STEP_NOTIFY_SCHEDULE_IMPORTANT:
                    important_text = " (Important)"
                result += f'triggered step "Notify on-call from Schedule {schedule_name}{important_text}"'
            elif escalation_policy_step == EscalationPolicy.STEP_REPEAT_ESCALATION_N_TIMES:
                result += "escalation started from the beginning"
            else:
                result += f'triggered step "{EscalationPolicy.get_step_display_name(escalation_policy_step)}"'
        elif self.type == AlertGroupLogRecord.TYPE_SILENCE:
            if self.silence_delay is None:
                result += f"silenced by {author_name} forever"
            else:
                if self.silence_delay.total_seconds() == 0:
                    # Before renaming snooze to silence and implementation of silence without time limit zero delay ment unsnooze
                    result += f"unsilenced by {author_name}"
                else:
                    result += f"silenced by {author_name} for {humanize.naturaldelta(self.silence_delay)}"
        elif self.type == AlertGroupLogRecord.TYPE_UN_SILENCE:
            if self.author is not None:
                result += f"unsilenced by {author_name}"
            else:
                result += "alert group unsilenced"
        elif self.type == AlertGroupLogRecord.TYPE_ATTACHED:
            # Log record of dependent alert group
            if self.root_alert_group:
                if self.alert_group.slack_message is not None and self.root_alert_group.slack_message is not None:
                    if html:
                        result += (
                            f"attached to <a href='{self.root_alert_group.slack_message.permalink}'>"
                            f"{self.root_alert_group.long_verbose_name_without_formatting}</a> by {author_name}"
                        )
                    else:
                        result += (
                            f"attached to <{self.root_alert_group.slack_message.permalink}|"
                            f"{self.root_alert_group.long_verbose_name_without_formatting}> by {author_name}"
                        )
                else:
                    result += f"attached to {self.root_alert_group.long_verbose_name} by {author_name}"
            # Log record of root alert group
            elif self.dependent_alert_group:
                if self.alert_group.slack_message is not None and self.dependent_alert_group.slack_message is not None:
                    if html:
                        result += (
                            f"<a href='{self.dependent_alert_group.slack_message.permalink}'>"
                            f"{self.dependent_alert_group.long_verbose_name_without_formatting}</a> has been attached to this alert "
                            f"by {author_name}"
                        )
                    else:
                        result += (
                            f"<{self.dependent_alert_group.slack_message.permalink}|"
                            f"{self.dependent_alert_group.long_verbose_name_without_formatting}> has been attached to this alert "
                            f"by {author_name or 'maintenance'}"
                        )
                else:
                    result += (
                        f"{self.dependent_alert_group.long_verbose_name} has been attached to this alert "
                        f"by {author_name or 'maintenance'}"
                    )
        elif self.type == AlertGroupLogRecord.TYPE_UNATTACHED:
            if self.root_alert_group:
                if self.alert_group.slack_message is not None and self.root_alert_group.slack_message is not None:
                    if html:
                        result += (
                            f"unattached from <a href='{self.root_alert_group.slack_message.permalink}'>"
                            f"{self.root_alert_group.long_verbose_name_without_formatting}</a>"
                            f"{f' by {author_name}' if author_name else ''}"
                        )
                    else:
                        result += (
                            f"unattached from <{self.root_alert_group.slack_message.permalink}|"
                            f"{self.root_alert_group.long_verbose_name_without_formatting}>"
                            f"{f' by {author_name}' if author_name else ''}"
                        )
                else:
                    result += (
                        f"unattached from {self.root_alert_group.long_verbose_name}"
                        f"{f' by {author_name}' if author_name else ''}"
                    )
            elif self.dependent_alert_group:
                if self.alert_group.slack_message is not None and self.dependent_alert_group.slack_message is not None:
                    if html:
                        result += (
                            f"<a href='{self.dependent_alert_group.slack_message.permalink}'>"
                            f"{self.dependent_alert_group.long_verbose_name_without_formatting}</a> has been unattached from this alert"
                            f"{f' by {author_name}' if author_name else ''}"
                        )
                    else:
                        result += (
                            f"<{self.dependent_alert_group.slack_message.permalink}|"
                            f"{self.dependent_alert_group.long_verbose_name_without_formatting}> has been unattached from this alert"
                            f"{f' by {author_name}' if author_name else ''}"
                        )
                else:
                    result += (
                        f"{self.dependent_alert_group.long_verbose_name} has been unattached from this alert"
                        f"{f' by {author_name}' if author_name else ''}"
                    )
        elif self.type == AlertGroupLogRecord.TYPE_CUSTOM_BUTTON_TRIGGERED:
            webhook_name = ""
            trigger = None
            if step_specific_info is not None:
                webhook_name = step_specific_info.get("webhook_name") or step_specific_info.get("custom_button_name")
                trigger = step_specific_info.get("trigger")
            elif self.custom_button is not None:
                webhook_name = f"`{self.custom_button.name}`"
            if trigger is None and self.author:
                trigger = f"{author_name}"
            else:
                trigger = trigger or "escalation chain"
            result += f"outgoing webhook `{webhook_name}` triggered by {trigger}"
        elif self.type == AlertGroupLogRecord.TYPE_FAILED_ATTACHMENT:
            if self.alert_group.slack_message is not None:
                result += (
                    f"failed to attach to <{self.root_alert_group.slack_message.permalink}|"
                    f"{self.root_alert_group.long_verbose_name_without_formatting}> "
                    f"by {author_name} because it is already attached or resolved."
                )
            else:
                result += (
                    f"failed to attach to {self.root_alert_group.long_verbose_name} by {author_name}"
                    f"because it is already attached or resolved."
                )
        elif self.type == AlertGroupLogRecord.TYPE_RESOLVED:
            result += f"alert group resolved {f'by {author_name}'if author_name else ''}"
        elif self.type == AlertGroupLogRecord.TYPE_UN_RESOLVED:
            result += f"unresolved by {author_name}"
        elif self.type == AlertGroupLogRecord.TYPE_WIPED:
            result += "wiped"
        elif self.type == AlertGroupLogRecord.TYPE_DIRECT_PAGING:
            result += self.reason
        elif self.type == AlertGroupLogRecord.TYPE_UNPAGE_USER:
            result += self.reason
        elif self.type == AlertGroupLogRecord.TYPE_ESCALATION_FAILED:
            if self.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_USER_NO_RECIPIENT:
                result += 'skipped escalation step "Notify User" because no users are set'
            elif self.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_QUEUE_NO_RECIPIENTS:
                result += 'skipped escalation step "Notify User (next each time)" because no users are set'
            elif self.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_MULTIPLE_NO_RECIPIENTS:
                result += 'skipped escalation step "Notify multiple Users" because no users are set'
            elif self.escalation_error_code in [
                AlertGroupLogRecord.ERROR_ESCALATION_SCHEDULE_DOES_NOT_EXIST,
                AlertGroupLogRecord.ERROR_ESCALATION_NO_SCHEDULE_IN_CHANNEL,
            ]:
                result += 'skipped escalation step "Notify Schedule" because schedule doesn\'t exist'
            elif self.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_SCHEDULE_DOES_NOT_SELECTED:
                result += 'skipped escalation step "Notify Schedule" because it is not configured'
            elif self.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_GROUP_STEP_IS_NOT_CONFIGURED:
                result += 'skipped escalation step "Notify Group" because it is not configured'
            elif (
                self.escalation_error_code
                == AlertGroupLogRecord.ERROR_ESCALATION_TRIGGER_CUSTOM_BUTTON_STEP_IS_NOT_CONFIGURED
            ):
                result += 'skipped escalation step "Trigger Outgoing Webhook" because it is not configured'
            elif self.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_TRIGGER_CUSTOM_WEBHOOK_ERROR:
                webhook_name = trigger = ""
                if step_specific_info is not None:
                    webhook_name = step_specific_info.get("webhook_name", "")
                    trigger = step_specific_info.get("trigger", "")
                result += f"skipped {trigger} outgoing webhook `{webhook_name}`"
                if self.reason:
                    result += f": {self.reason}"
            elif self.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_IF_TIME_IS_NOT_CONFIGURED:
                result += 'skipped escalation step "Continue escalation if time" because it is not configured'
            elif (
                self.escalation_error_code
                == AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_IF_NUM_ALERTS_IN_WINDOW_STEP_IS_NOT_CONFIGURED
            ):
                result += 'skipped escalation step"Continue escalation if >X alerts per Y minutes" because it is not configured'
            elif self.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_ICAL_IMPORT_FAILED:
                if self.escalation_policy is not None and self.escalation_policy.notify_schedule is not None:
                    schedule_name = self.escalation_policy.notify_schedule.name
                    schedule_name = f' "{schedule_name}" '
                else:
                    schedule_name = " "
                result += f'escalation step "Notify Schedule"{schedule_name} skipped: iCal import was failed.'
            elif self.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_ICAL_NO_VALID_USERS:
                if self.escalation_policy is not None and self.escalation_policy.notify_schedule is not None:
                    schedule_name = self.escalation_policy.notify_schedule.name
                    schedule_name = f' "{schedule_name}" '
                else:
                    schedule_name = " "
                result += (
                    f'escalation step "Notify Schedule" {schedule_name} skipped:'
                    f" there are no users to notify for this schedule slot."
                )
            elif self.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_WAIT_STEP_IS_NOT_CONFIGURED:
                result += 'escalation step "Wait" is not configured. ' "Default delay is 5 minutes."
            elif self.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_USER_GROUP_IS_EMPTY:
                if self.escalation_policy is not None:
                    group_name = f" <!subteam^{self.escalation_policy.notify_to_group}> "
                else:
                    group_name = " "
                result += f'escalation step "Notify Group"{group_name}skipped: User Group is empty.'
            elif self.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_USER_GROUP_DOES_NOT_EXIST:
                result += 'escalation step "Notify Group" skipped: User Group does not exist.'
            elif self.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_UNSPECIFIED_STEP:
                result += "escalation step is unspecified. Skipped"
            elif self.escalation_error_code == AlertGroupLogRecord.ERROR_ESCALATION_NOTIFY_IN_SLACK:
                if self.escalation_policy_step == EscalationPolicy.STEP_FINAL_NOTIFYALL:
                    result += "failed to notify channel in Slack"
                elif self.escalation_policy_step in [
                    EscalationPolicy.STEP_NOTIFY_GROUP,
                    EscalationPolicy.STEP_NOTIFY_GROUP_IMPORTANT,
                ]:
                    usergroup_handle = None
                    if step_specific_info is not None:
                        usergroup_handle = self.step_specific_info.get("usergroup_handle", "")
                    elif self.escalation_policy is not None and self.escalation_policy.notify_to_group is not None:
                        usergroup_handle = self.escalation_policy.notify_to_group.handle
                    usergroup_handle_text = f" @{usergroup_handle}" if usergroup_handle else ""
                    result += f"failed to notify User Group{usergroup_handle_text} in Slack"
        return result

    def get_step_specific_info(self):
        step_specific_info = None
        # in some cases step_specific_info was saved with using json.dumps
        if self.step_specific_info is not None:
            if isinstance(self.step_specific_info, dict):
                step_specific_info = self.step_specific_info
            else:
                step_specific_info = json.loads(self.step_specific_info)
        return step_specific_info


@receiver(post_save, sender=AlertGroupLogRecord)
def listen_for_alertgrouplogrecord(sender, instance, created, *args, **kwargs):
    if instance.type != AlertGroupLogRecord.TYPE_DELETED:
        alert_group_pk = instance.alert_group.pk
        logger.debug(
            f"send_update_log_report_signal for alert_group {alert_group_pk}, "
            f"alert group event: {instance.get_type_display()}"
        )
        tasks.send_update_log_report_signal.apply_async(kwargs={"alert_group_pk": alert_group_pk}, countdown=8)
