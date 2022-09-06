import logging
from collections import namedtuple
from typing import Optional
from urllib.parse import urljoin
from uuid import uuid1

import pytz
from celery import uuid as celery_uuid
from django.apps import apps
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import IntegrityError, models
from django.db.models import JSONField, Q, QuerySet
from django.utils import timezone
from django.utils.functional import cached_property

from apps.alerts.escalation_snapshot import EscalationSnapshotMixin
from apps.alerts.incident_appearance.renderers.constants import DEFAULT_BACKUP_TITLE
from apps.alerts.incident_appearance.renderers.slack_renderer import AlertGroupSlackRenderer
from apps.alerts.incident_log_builder import IncidentLogBuilder
from apps.alerts.signals import alert_group_action_triggered_signal
from apps.alerts.tasks import acknowledge_reminder_task, call_ack_url, send_alert_group_signal, unsilence_task
from apps.slack.slack_formatter import SlackFormatter
from apps.user_management.models import User
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length
from common.utils import clean_markup, str_or_backup

from .alert_group_counter import AlertGroupCounter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def generate_public_primary_key_for_alert_group():
    prefix = "I"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while AlertGroup.all_objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="AlertGroup"
        )
        failure_counter += 1

    return new_public_primary_key


class AlertGroupQuerySet(models.QuerySet):
    def create(self, **kwargs):
        organization = kwargs["channel"].organization

        inside_organization_number = AlertGroupCounter.objects.get_value(organization=organization) + 1
        return super().create(**kwargs, inside_organization_number=inside_organization_number)

    def get_or_create_grouping(self, channel, channel_filter, group_data):
        """
        This method is similar to default Django QuerySet.get_or_create(), please see the original get_or_create method.
        The difference is that this method is trying to get an object using multiple queries with different filters.
        Also, "create" is invoked without transaction.atomic to reduce number of ConcurrentUpdateError's which can be
        raised in AlertGroupQuerySet.create() due to optimistic locking of AlertGroupCounter model.
        """
        search_params = {
            "channel": channel,
            "channel_filter": channel_filter,
            "distinction": group_data.group_distinction,
        }

        # Try to return the last open group
        # Note that (channel, channel_filter, distinction, is_open_for_grouping) is in unique_together
        try:
            return self.get(**search_params, is_open_for_grouping=True), False
        except self.model.DoesNotExist:
            pass

        # If it's an "OK" alert, try to return the latest resolved group
        if group_data.is_resolve_signal:
            try:
                return self.filter(**search_params, resolved=True).latest(), False
            except self.model.DoesNotExist:
                pass

        # Create a new group if we couldn't group it to any existing ones
        try:
            return (
                self.create(**search_params, is_open_for_grouping=True, web_title_cache=group_data.web_title_cache),
                True,
            )
        except IntegrityError:
            try:
                return self.get(**search_params, is_open_for_grouping=True), False
            except self.model.DoesNotExist:
                pass
            raise


class UnarchivedAlertGroupQuerySet(models.QuerySet):
    def filter(self, *args, **kwargs):
        return super().filter(*args, **kwargs, is_archived=False)


class AlertGroupSlackRenderingMixin:
    """
    Ideally this mixin should not exist. Instead of this instance of AlertGroupSlackRenderer should be created and used
    but slack rendering is distributed throughout the codebase.
    """

    @cached_property
    def slack_renderer(self):
        return AlertGroupSlackRenderer(self)

    def render_slack_attachments(self):
        return self.slack_renderer.render_alert_group_attachments()

    def render_slack_blocks(self):
        return self.slack_renderer.render_alert_group_blocks()

    @property
    def slack_templated_first_alert(self):
        return self.slack_renderer.alert_renderer.templated_alert


class AlertGroup(AlertGroupSlackRenderingMixin, EscalationSnapshotMixin, models.Model):
    all_objects = AlertGroupQuerySet.as_manager()
    unarchived_objects = UnarchivedAlertGroupQuerySet.as_manager()

    (
        NEW,
        ACKNOWLEDGED,
        RESOLVED,
        SILENCED,
    ) = range(4)

    # exists for status filter in API
    STATUS_CHOICES = ((NEW, "New"), (ACKNOWLEDGED, "Acknowledged"), (RESOLVED, "Resolved"), (SILENCED, "Silenced"))

    GroupData = namedtuple(
        "GroupData", ["is_resolve_signal", "group_distinction", "web_title_cache", "is_acknowledge_signal"]
    )

    SOURCE, USER, NOT_YET, LAST_STEP, ARCHIVED, WIPED, DISABLE_MAINTENANCE = range(7)
    SOURCE_CHOICES = (
        (SOURCE, "source"),
        (USER, "user"),
        (NOT_YET, "not yet"),
        (LAST_STEP, "last escalation step"),
        (ARCHIVED, "archived"),
        (WIPED, "wiped"),
        (DISABLE_MAINTENANCE, "stop maintenance"),
    )

    ACKNOWLEDGE = "acknowledge"
    RESOLVE = "resolve"
    SILENCE = "silence"
    RESTART = "restart"

    BULK_ACTIONS = [
        ACKNOWLEDGE,
        RESOLVE,
        SILENCE,
        RESTART,
    ]

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_alert_group,
    )

    channel = models.ForeignKey(
        "alerts.AlertReceiveChannel",
        on_delete=models.CASCADE,
        related_name="alert_groups",
    )

    # Distinction is a difference between groups inside the same channel.
    # For example different types of alerts from the same channel should go to different groups.
    # Distinction is what describes their difference.
    distinction = models.CharField(max_length=100, null=True, default=None, db_index=True)
    web_title_cache = models.TextField(null=True, default=None)

    inside_organization_number = models.IntegerField(default=0)

    channel_filter = models.ForeignKey(
        "alerts.ChannelFilter",
        on_delete=models.SET_DEFAULT,
        related_name="alert_groups",
        null=True,
        default=None,
    )

    resolved = models.BooleanField(default=False)

    resolved_by = models.IntegerField(choices=SOURCE_CHOICES, default=NOT_YET)
    resolved_by_user = models.ForeignKey(
        "user_management.User",
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="resolved_alert_groups",
    )

    resolved_by_alert = models.ForeignKey(
        "alerts.Alert",
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="resolved_alert_groups",
    )

    resolved_at = models.DateTimeField(blank=True, null=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_on_source = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    acknowledged_by = models.IntegerField(choices=SOURCE_CHOICES, default=NOT_YET)
    acknowledged_by_user = models.ForeignKey(
        "user_management.User",
        on_delete=models.SET_NULL,
        null=True,
        default=None,
    )
    acknowledged_by_confirmed = models.DateTimeField(null=True, default=None)

    is_escalation_finished = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)

    slack_message_sent = models.BooleanField(default=False)

    active_escalation_id = models.CharField(max_length=100, null=True, default=None)  # ID generated by celery
    active_resolve_calculation_id = models.CharField(max_length=100, null=True, default=None)  # ID generated by celery

    SILENCE_DELAY_OPTIONS = (
        (1800, "30 minutes"),
        (3600, "1 hour"),
        (14400, "4 hours"),
        (43200, "12 hours"),
        (57600, "16 hours"),
        (72000, "20 hours"),
        (86400, "24 hours"),
        (-1, "Forever"),
    )
    silenced = models.BooleanField(default=False)
    silenced_at = models.DateTimeField(null=True)
    silenced_by_user = models.ForeignKey(
        "user_management.User",
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="silenced_alert_groups",
    )
    silenced_until = models.DateTimeField(blank=True, null=True)
    unsilence_task_uuid = models.CharField(max_length=100, null=True, default=None)

    @property
    def is_silenced_forever(self):
        return self.silenced and self.silenced_until is None

    @property
    def is_silenced_for_period(self):
        return self.silenced and self.silenced_until is not None

    @property
    def status(self):
        if self.resolved:
            return AlertGroup.RESOLVED
        elif self.acknowledged:
            return AlertGroup.ACKNOWLEDGED
        elif self.silenced:
            return AlertGroup.SILENCED
        else:
            return AlertGroup.NEW

    ACCOUNT_INACTIVE, CHANNEL_ARCHIVED, NO_REASON, RATE_LIMITED, CHANNEL_NOT_SPECIFIED, RESTRICTED_ACTION = range(6)
    REASONS_TO_SKIP_ESCALATIONS = (
        (ACCOUNT_INACTIVE, "account_inactive"),
        (CHANNEL_ARCHIVED, "channel_archived"),
        (NO_REASON, "no_reason"),
        (RATE_LIMITED, "rate_limited"),
        (CHANNEL_NOT_SPECIFIED, "channel_not_specified"),
        (RESTRICTED_ACTION, "restricted_action"),
    )
    reason_to_skip_escalation = models.IntegerField(choices=REASONS_TO_SKIP_ESCALATIONS, default=NO_REASON)

    SEVERITY_HIGH, SEVERITY_LOW, SEVERITY_NONE = range(3)
    SEVERITY_CHOICES = (
        (SEVERITY_HIGH, "high"),
        (SEVERITY_LOW, "low"),
        (SEVERITY_NONE, "none"),
    )
    manual_severity = models.IntegerField(choices=SEVERITY_CHOICES, default=SEVERITY_NONE)

    resolution_note_ts = models.CharField(max_length=100, null=True, default=None)

    root_alert_group = models.ForeignKey(
        "alerts.AlertGroup",
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="dependent_alert_groups",
    )

    # cached_render_for_web and active_cache_for_web_calculation_id are deprecated
    cached_render_for_web = models.JSONField(default=dict)
    active_cache_for_web_calculation_id = models.CharField(max_length=100, null=True, default=None)

    last_unique_unacknowledge_process_id = models.CharField(max_length=100, null=True, default=None)
    is_archived = models.BooleanField(default=False)

    wiped_at = models.DateTimeField(null=True, default=None)
    wiped_by = models.ForeignKey(
        "user_management.User", on_delete=models.SET_NULL, null=True, default=None, related_name="wiped_by_user"
    )

    slack_message = models.OneToOneField(
        "slack.SlackMessage",
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="_alert_group",
    )

    slack_log_message = models.OneToOneField(
        "slack.SlackMessage",
        on_delete=models.SET_NULL,
        null=True,
        default=None,
    )

    prevent_posting_alerts = models.BooleanField(default=False)
    maintenance_uuid = models.CharField(max_length=100, unique=True, null=True, default=None)

    raw_escalation_snapshot = JSONField(null=True, default=None)
    estimate_escalation_finish_time = models.DateTimeField(null=True, default=None)

    # This field is used for constraints so we can use get_or_create() in concurrent calls
    # https://docs.djangoproject.com/en/3.2/ref/models/querysets/#get-or-create
    # Combined with unique_together below, it allows only one alert group with
    # the combination (alert_receive_channel_id, channel_filter_id, distinction, is_open_for_grouping=True)
    # If is_open_for_grouping=None, then we can have as many combinations of
    # (alert_receive_channel_id, channel_filter_id, distinction, is_open_for_grouping=None) as we want
    # We just don't care about that because we'll use only get_or_create(...is_open_for_grouping=True...)
    # https://code.djangoproject.com/ticket/28545
    is_open_for_grouping = models.BooleanField(default=None, null=True, blank=True)

    class Meta:
        get_latest_by = "pk"
        unique_together = [
            "channel_id",
            "channel_filter_id",
            "distinction",
            "is_open_for_grouping",
        ]
        indexes = [
            models.Index(
                fields=["channel_id", "resolved", "acknowledged", "silenced", "root_alert_group_id", "is_archived"]
            ),
        ]

    def __str__(self):
        return f"{self.pk}: {self.web_title_cache}"

    @property
    def is_maintenance_incident(self):
        return self.maintenance_uuid is not None

    def stop_maintenance(self, user: User) -> None:
        Organization = apps.get_model("user_management", "Organization")
        AlertReceiveChannel = apps.get_model("alerts", "AlertReceiveChannel")

        try:
            integration_on_maintenance = AlertReceiveChannel.objects.get(maintenance_uuid=self.maintenance_uuid)
            integration_on_maintenance.force_disable_maintenance(user)
            return
        except AlertReceiveChannel.DoesNotExist:
            pass

        try:
            organization_on_maintenance = Organization.objects.get(maintenance_uuid=self.maintenance_uuid)
            organization_on_maintenance.force_disable_maintenance(user)
            return
        except Organization.DoesNotExist:
            pass

        self.resolve_by_disable_maintenance()

    @property
    def skip_escalation_in_slack(self):
        return self.reason_to_skip_escalation in (
            AlertGroup.CHANNEL_ARCHIVED,
            AlertGroup.ACCOUNT_INACTIVE,
            AlertGroup.RATE_LIMITED,
            AlertGroup.CHANNEL_NOT_SPECIFIED,
        )

    def is_alert_a_resolve_signal(self, alert):
        raise NotImplementedError

    @property
    def permalink(self):
        if self.slack_message is not None:
            return self.slack_message.permalink

    @property
    def web_link(self):
        return urljoin(self.channel.organization.web_link, f"?page=incident&id={self.public_primary_key}")

    @property
    def happened_while_maintenance(self):
        return self.root_alert_group is not None and self.root_alert_group.maintenance_uuid is not None

    def acknowledge_by_user(self, user: User, action_source: Optional[str] = None) -> None:
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
        logger.debug(f"Started acknowledge_by_user for alert_group {self.pk}")
        # if incident was silenced or resolved, unsilence/unresolve it without starting escalation
        if self.silenced:
            self.un_silence()
            self.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_SILENCE,
                author=user,
                silence_delay=None,
                reason="Acknowledge button",
            )
        if self.resolved:
            self.unresolve()
            self.log_records.create(type=AlertGroupLogRecord.TYPE_UN_RESOLVED, author=user, reason="Acknowledge button")

        self.acknowledge(acknowledged_by_user=user, acknowledged_by=AlertGroup.USER)
        self.stop_escalation()
        if self.is_root_alert_group:
            self.start_ack_reminder(user)

        if self.can_call_ack_url:
            self.start_call_ack_url()

        log_record = self.log_records.create(type=AlertGroupLogRecord.TYPE_ACK, author=user)

        logger.debug(
            f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}', action source: {action_source}"
        )

        alert_group_action_triggered_signal.send(
            sender=self.acknowledge_by_user,
            log_record=log_record.pk,
            action_source=action_source,
        )

        for dependent_alert_group in self.dependent_alert_groups.all():
            dependent_alert_group.acknowledge_by_user(user, action_source=action_source)

        logger.debug(f"Finished acknowledge_by_user for alert_group {self.pk}")

    def acknowledge_by_source(self):
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

        # if incident was silenced, unsilence it without starting escalation
        if self.silenced:
            self.un_silence()
            self.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_SILENCE,
                silence_delay=None,
                reason="Acknowledge by source",
            )
        self.acknowledge(acknowledged_by=AlertGroup.SOURCE)
        self.stop_escalation()

        log_record = self.log_records.create(type=AlertGroupLogRecord.TYPE_ACK)

        logger.debug(
            f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}', action source: alert"
        )

        alert_group_action_triggered_signal.send(
            sender=self.acknowledge_by_source,
            log_record=log_record.pk,
            action_source=None,
        )

        for dependent_alert_group in self.dependent_alert_groups.all():
            dependent_alert_group.acknowledge_by_source()

    def un_acknowledge_by_user(self, user: User, action_source: Optional[str] = None) -> None:
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

        logger.debug(f"Started un_acknowledge_by_user for alert_group {self.pk}")
        self.unacknowledge()
        if self.is_root_alert_group:
            self.start_escalation_if_needed()

        log_record = self.log_records.create(type=AlertGroupLogRecord.TYPE_UN_ACK, author=user)

        logger.debug(
            f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}', action source: {action_source}"
        )

        alert_group_action_triggered_signal.send(
            sender=self.un_acknowledge_by_user,
            log_record=log_record.pk,
            action_source=action_source,
        )

        for dependent_alert_group in self.dependent_alert_groups.all():
            dependent_alert_group.un_acknowledge_by_user(user, action_source=action_source)
        logger.debug(f"Finished un_acknowledge_by_user for alert_group {self.pk}")

    def resolve_by_user(self, user: User, action_source: Optional[str] = None) -> None:
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

        # if incident was silenced, unsilence it without starting escalation
        if self.silenced:
            self.un_silence()
            self.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_SILENCE,
                author=user,
                silence_delay=None,
                reason="Resolve button",
            )
        self.resolve(resolved_by=AlertGroup.USER, resolved_by_user=user)
        self.stop_escalation()
        log_record = self.log_records.create(type=AlertGroupLogRecord.TYPE_RESOLVED, author=user)

        logger.debug(
            f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}', action source: {action_source}"
        )

        alert_group_action_triggered_signal.send(
            sender=self.resolve_by_user,
            log_record=log_record.pk,
            action_source=action_source,
        )

        for dependent_alert_group in self.dependent_alert_groups.all():
            dependent_alert_group.resolve_by_user(user, action_source=action_source)

    def resolve_by_source(self):
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
        # if incident was silenced, unsilence it without starting escalation
        if self.silenced:
            self.un_silence()
            self.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_SILENCE,
                silence_delay=None,
                reason="Resolve by source",
            )
        self.resolve(resolved_by=AlertGroup.SOURCE)
        self.stop_escalation()
        log_record = self.log_records.create(type=AlertGroupLogRecord.TYPE_RESOLVED)

        logger.debug(
            f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}', action source: alert"
        )

        alert_group_action_triggered_signal.send(
            sender=self.resolve_by_source,
            log_record=log_record.pk,
            action_source=None,
        )

        for dependent_alert_group in self.dependent_alert_groups.all():
            dependent_alert_group.resolve_by_source()

    def resolve_by_archivation(self):
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
        # if incident was silenced, unsilence it without starting escalation
        if self.silenced:
            self.un_silence()
            self.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_SILENCE,
                silence_delay=None,
                reason="Resolve by archivation",
            )
        self.archive()
        self.stop_escalation()
        if not self.resolved:
            self.resolve(resolved_by=AlertGroup.ARCHIVED)

            log_record = self.log_records.create(type=AlertGroupLogRecord.TYPE_RESOLVED)

            logger.debug(
                f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
                f"log record {log_record.pk} with type '{log_record.get_type_display()}', action source: archivation"
            )

            alert_group_action_triggered_signal.send(
                sender=self.resolve_by_archivation,
                log_record=log_record.pk,
                action_source=None,
            )

        for dependent_alert_group in self.dependent_alert_groups.all():
            dependent_alert_group.resolve_by_archivation()

    def resolve_by_last_step(self):
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

        self.resolve(resolved_by=AlertGroup.LAST_STEP)
        self.stop_escalation()
        log_record = self.log_records.create(type=AlertGroupLogRecord.TYPE_RESOLVED)

        logger.debug(
            f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}', action source: resolve step"
        )

        alert_group_action_triggered_signal.send(
            sender=self.resolve_by_last_step,
            log_record=log_record.pk,
            action_source=None,
        )

        for dependent_alert_group in self.dependent_alert_groups.all():
            dependent_alert_group.resolve_by_last_step()

    def resolve_by_disable_maintenance(self):
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

        self.resolve(resolved_by=AlertGroup.DISABLE_MAINTENANCE)
        self.stop_escalation()
        log_record = self.log_records.create(type=AlertGroupLogRecord.TYPE_RESOLVED)

        logger.debug(
            f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}', "
            f"action source: disable maintenance"
        )

        alert_group_action_triggered_signal.send(
            sender=self.resolve_by_disable_maintenance,
            log_record=log_record.pk,
            action_source=None,
        )

        for dependent_alert_group in self.dependent_alert_groups.all():
            dependent_alert_group.resolve_by_disable_maintenance()

    def un_resolve_by_user(self, user: User, action_source: Optional[str] = None) -> None:
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

        if self.wiped_at is None:
            self.unresolve()
            log_record = self.log_records.create(type=AlertGroupLogRecord.TYPE_UN_RESOLVED, author=user)

            if self.is_root_alert_group:
                self.start_escalation_if_needed()

            logger.debug(
                f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
                f"log record {log_record.pk} with type '{log_record.get_type_display()}', "
                f"action source: {action_source}"
            )

            alert_group_action_triggered_signal.send(
                sender=self.un_resolve_by_user,
                log_record=log_record.pk,
                action_source=action_source,
            )

            for dependent_alert_group in self.dependent_alert_groups.all():
                dependent_alert_group.un_resolve_by_user(user, action_source=action_source)

    def attach_by_user(self, user: User, root_alert_group: "AlertGroup", action_source: Optional[str] = None) -> None:
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

        if root_alert_group.root_alert_group is None and not root_alert_group.resolved:
            self.root_alert_group = root_alert_group
            self.save(update_fields=["root_alert_group"])
            self.stop_escalation()
            if root_alert_group.acknowledged and not self.acknowledged:
                self.acknowledge_by_user(user, action_source=action_source)
            elif not root_alert_group.acknowledged and self.acknowledged:
                self.un_acknowledge_by_user(user, action_source=action_source)

            if root_alert_group.silenced and not self.silenced:
                self.silence_by_user(user, action_source=action_source, silence_delay=None)

            if not root_alert_group.silenced and self.silenced:
                self.un_silence_by_user(user, action_source=action_source)

            log_record = self.log_records.create(
                type=AlertGroupLogRecord.TYPE_ATTACHED,
                author=user,
                root_alert_group=root_alert_group,
                reason="Attach dropdown",
            )

            logger.debug(
                f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
                f"log record {log_record.pk} with type '{log_record.get_type_display()}', "
                f"action source: {action_source}"
            )

            alert_group_action_triggered_signal.send(
                sender=self.attach_by_user,
                log_record=log_record.pk,
                action_source=action_source,
            )

            log_record_for_root_incident = root_alert_group.log_records.create(
                type=AlertGroupLogRecord.TYPE_ATTACHED,
                author=user,
                dependent_alert_group=self,
                reason="Attach dropdown",
            )

            logger.debug(
                f"send alert_group_action_triggered_signal for alert_group {root_alert_group.pk}, "
                f"log record {log_record_for_root_incident.pk} with type "
                f"'{log_record_for_root_incident.get_type_display()}', action source: {action_source}"
            )

            alert_group_action_triggered_signal.send(
                sender=self.attach_by_user,
                log_record=log_record_for_root_incident.pk,
                action_source=action_source,
            )

        else:
            log_record = self.log_records.create(
                type=AlertGroupLogRecord.TYPE_FAILED_ATTACHMENT,
                author=user,
                root_alert_group=root_alert_group,
                reason="Failed to attach dropdown",
            )

            logger.debug(
                f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
                f"log record {log_record.pk} with type '{log_record.get_type_display()}', "
                f"action source: {action_source}"
            )

            alert_group_action_triggered_signal.send(
                sender=self.attach_by_user,
                log_record=log_record.pk,
                action_source=action_source,
            )

    def un_attach_by_user(self, user: User, action_source: Optional[str] = None) -> None:
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

        root_alert_group = self.root_alert_group
        self.root_alert_group = None
        self.save(update_fields=["root_alert_group"])

        self.start_escalation_if_needed()

        log_record = self.log_records.create(
            type=AlertGroupLogRecord.TYPE_UNATTACHED,
            author=user,
            root_alert_group=root_alert_group,
            reason="Unattach button",
        )

        logger.debug(
            f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}', "
            f"action source: {action_source}"
        )

        alert_group_action_triggered_signal.send(
            sender=self.un_attach_by_user,
            log_record=log_record.pk,
            action_source=action_source,
        )

        log_record_for_root_incident = root_alert_group.log_records.create(
            type=AlertGroupLogRecord.TYPE_UNATTACHED,
            author=user,
            dependent_alert_group=self,
            reason="Unattach dropdown",
        )

        logger.debug(
            f"send alert_group_action_triggered_signal for alert_group {root_alert_group.pk}, "
            f"log record {log_record_for_root_incident.pk} "
            f"with type '{log_record_for_root_incident.get_type_display()}', action source: {action_source}"
        )

        alert_group_action_triggered_signal.send(
            sender=self.un_attach_by_user,
            log_record=log_record_for_root_incident.pk,
            action_source=action_source,
        )

    def un_attach_by_delete(self):
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

        self.root_alert_group = None
        self.save(update_fields=["root_alert_group"])

        self.start_escalation_if_needed()

        log_record = self.log_records.create(
            type=AlertGroupLogRecord.TYPE_UNATTACHED,
            reason="Unattach by deleting root incident",
        )

        logger.debug(
            f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}', "
            f"action source: delete"
        )

        alert_group_action_triggered_signal.send(
            sender=self.un_attach_by_delete,
            log_record=log_record.pk,
            action_source=None,
        )

    def silence_by_user(self, user: User, silence_delay: Optional[int], action_source: Optional[str] = None) -> None:
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
        if self.resolved:
            self.unresolve()
            self.log_records.create(type=AlertGroupLogRecord.TYPE_UN_RESOLVED, author=user, reason="Silence button")

        if self.acknowledged:
            self.unacknowledge()
            self.log_records.create(type=AlertGroupLogRecord.TYPE_UN_ACK, author=user, reason="Silence button")

        if self.silenced:
            self.un_silence()
            self.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_SILENCE,
                author=user,
                silence_delay=None,
                reason="Silence button",
            )

        now = timezone.now()

        if silence_delay is not None and silence_delay > 0:
            silence_delay_timedelta = timezone.timedelta(seconds=silence_delay)
            silenced_until = now + silence_delay_timedelta
            if self.is_root_alert_group:
                self.start_unsilence_task(countdown=silence_delay)
        else:
            silence_delay_timedelta = None
            silenced_until = None

        self.silence(silenced_at=now, silenced_until=silenced_until, silenced_by_user=user)

        log_record = self.log_records.create(
            type=AlertGroupLogRecord.TYPE_SILENCE,
            author=user,
            silence_delay=silence_delay_timedelta,
            reason="Silence button",
        )

        logger.debug(
            f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}', "
            f"action source: {action_source}"
        )

        alert_group_action_triggered_signal.send(
            sender=self.silence_by_user,
            log_record=log_record.pk,
            action_source=action_source,
        )
        for dependent_alert_group in self.dependent_alert_groups.all():
            dependent_alert_group.silence_by_user(user, silence_delay, action_source)

    def un_silence_by_user(self, user: User, action_source: Optional[str] = None) -> None:
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

        self.un_silence()
        if self.is_root_alert_group:
            self.start_escalation_if_needed()

        log_record = self.log_records.create(
            type=AlertGroupLogRecord.TYPE_UN_SILENCE,
            author=user,
            silence_delay=None,
            # 2.Look like some time ago there was no TYPE_UN_SILENCE
            reason="Unsilence button",
        )

        logger.debug(
            f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}', "
            f"action source: {action_source}"
        )

        alert_group_action_triggered_signal.send(
            sender=self.un_silence_by_user,
            log_record=log_record.pk,
            action_source=action_source,
        )
        for dependent_alert_group in self.dependent_alert_groups.all():
            dependent_alert_group.un_silence_by_user(user, action_source=action_source)

    def wipe_by_user(self, user: User) -> None:
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

        if not self.wiped_at:
            self.resolve(resolved_by=AlertGroup.WIPED)
            self.stop_escalation()
            self.distinction = ""
            self.web_title_cache = None
            self.wiped_at = timezone.now()
            self.wiped_by = user
            for alert in self.alerts.all():
                alert.wipe(wiped_by=self.wiped_by, wiped_at=self.wiped_at)

            self.save(update_fields=["distinction", "web_title_cache", "wiped_at", "wiped_by"])

        log_record = self.log_records.create(
            type=AlertGroupLogRecord.TYPE_WIPED,
            author=user,
        )

        logger.debug(
            f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}', "
            f"action source: wipe"
        )

        alert_group_action_triggered_signal.send(
            sender=self.wipe_by_user,
            log_record=log_record.pk,
            action_source=None,
        )

        for dependent_alert_group in self.dependent_alert_groups.all():
            dependent_alert_group.wipe_by_user(user)

    def delete_by_user(self, user: User):
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
        self.stop_escalation()
        # prevent creating multiple logs
        # filter instead of get_or_create cause it can be multiple logs of this type due deleting error
        log_record = self.log_records.filter(type=AlertGroupLogRecord.TYPE_DELETED).last()

        if not log_record:
            log_record = self.log_records.create(
                type=AlertGroupLogRecord.TYPE_DELETED,
                author=user,
            )

        logger.debug(
            f"send alert_group_action_triggered_signal for alert_group {self.pk}, "
            f"log record {log_record.pk} with type '{log_record.get_type_display()}', "
            f"action source: delete"
        )

        alert_group_action_triggered_signal.send(
            sender=self.delete_by_user,
            log_record=log_record.pk,
            action_source=None,  # TODO: Action source is none - it is suspicious
            # this flag forces synchrony call for action handler in representatives
            # (for now it is actual only for Slack representative)
            force_sync=True,
        )

        dependent_alerts = list(self.dependent_alert_groups.all())

        self.hard_delete()

        for dependent_alert_group in dependent_alerts:  # unattach dependent incidents
            dependent_alert_group.un_attach_by_delete()

    def hard_delete(self):
        ResolutionNote = apps.get_model("alerts", "ResolutionNote")

        alerts = self.alerts.all()
        alerts.delete()

        self.slack_messages.all().delete()
        self.personal_log_records.all().delete()
        self.log_records.all().delete()
        self.invitations.all().delete()
        resolution_notes = ResolutionNote.objects_with_deleted.filter(alert_group=self)
        resolution_notes.delete()
        self.resolution_note_slack_messages.all().delete()
        self.delete()

    @staticmethod
    def bulk_acknowledge(user: User, alert_groups: "QuerySet[AlertGroup]") -> None:
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
        root_alert_groups_to_acknowledge = alert_groups.filter(
            ~Q(acknowledged=True, resolved=False),  # don't need to ack acknowledged incidents once again
            root_alert_group__isnull=True,
            maintenance_uuid__isnull=True,  # don't ack maintenance incident
        )
        # Find all dependent alert_groups to update them in one query
        dependent_alert_groups_to_acknowledge = AlertGroup.all_objects.filter(
            root_alert_group__in=root_alert_groups_to_acknowledge
        )
        alert_groups_to_acknowledge = root_alert_groups_to_acknowledge | dependent_alert_groups_to_acknowledge

        # it is needed to unserolve those alert_groups which were resolved to build proper log.
        alert_groups_to_unresolve_before_acknowledge = alert_groups_to_acknowledge.filter(resolved=True)

        # it is needed to unsilence those alert_groups which were silenced to build proper log.
        alert_groups_to_unsilence_before_acknowledge = alert_groups_to_acknowledge.filter(silenced=True)

        # convert current qs to list to prevent changes by update
        alert_groups_to_acknowledge_list = list(alert_groups_to_acknowledge)
        alert_groups_to_unresolve_before_acknowledge_list = list(alert_groups_to_unresolve_before_acknowledge)
        alert_groups_to_unsilence_before_acknowledge_list = list(alert_groups_to_unsilence_before_acknowledge)

        alert_groups_to_acknowledge.update(
            acknowledged=True,
            resolved=False,
            resolved_at=None,
            resolved_by=AlertGroup.NOT_YET,
            resolved_by_user=None,
            silenced_until=None,
            silenced_by_user=None,
            silenced_at=None,
            silenced=False,
            acknowledged_at=timezone.now(),
            acknowledged_by_user=user,
            acknowledged_by=AlertGroup.USER,
            is_escalation_finished=True,
        )

        for alert_group in alert_groups_to_unresolve_before_acknowledge_list:
            alert_group.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_RESOLVED,
                author=user,
                reason="Bulk action acknowledge",
            )

        for alert_group in alert_groups_to_unsilence_before_acknowledge_list:
            alert_group.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_SILENCE, author=user, reason="Bulk action acknowledge"
            )

        for alert_group in alert_groups_to_acknowledge_list:

            if alert_group.is_root_alert_group:
                alert_group.start_ack_reminder(user)

            if alert_group.can_call_ack_url:
                alert_group.start_call_ack_url()

            log_record = alert_group.log_records.create(type=AlertGroupLogRecord.TYPE_ACK, author=user)
            send_alert_group_signal.apply_async((log_record.pk,))

    @staticmethod
    def bulk_resolve(user: User, alert_groups: "QuerySet[AlertGroup]") -> None:
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

        # stop maintenance for maintenance incidents
        alert_groups_to_stop_maintenance = alert_groups.filter(resolved=False, maintenance_uuid__isnull=False)
        for alert_group in alert_groups_to_stop_maintenance:
            alert_group.stop_maintenance(user)

        root_alert_groups_to_resolve = alert_groups.filter(
            resolved=False,
            root_alert_group__isnull=True,
            maintenance_uuid__isnull=True,
        )
        if root_alert_groups_to_resolve.count() == 0:
            return

        organization = root_alert_groups_to_resolve.first().channel.organization
        if organization.is_resolution_note_required:
            root_alert_groups_to_resolve = root_alert_groups_to_resolve.filter(
                Q(resolution_notes__isnull=False, resolution_notes__deleted_at=None)
            )
        dependent_alert_groups_to_resolve = AlertGroup.all_objects.filter(
            root_alert_group__in=root_alert_groups_to_resolve
        )
        alert_groups_to_resolve = root_alert_groups_to_resolve | dependent_alert_groups_to_resolve

        # it is needed to unsilence those alert_groups which were silenced to build proper log.
        alert_groups_to_unsilence_before_resolve = alert_groups_to_resolve.filter(silenced=True)

        # convert current qs to list to prevent changes by update
        alert_groups_to_resolve_list = list(alert_groups_to_resolve)
        alert_groups_to_unsilence_before_resolve_list = list(alert_groups_to_unsilence_before_resolve)

        alert_groups_to_resolve.update(
            resolved=True,
            resolved_at=timezone.now(),
            is_open_for_grouping=None,
            resolved_by_user=user,
            resolved_by=AlertGroup.USER,
            is_escalation_finished=True,
            silenced_until=None,
            silenced_by_user=None,
            silenced_at=None,
            silenced=False,
        )

        for alert_group in alert_groups_to_unsilence_before_resolve_list:
            alert_group.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_SILENCE, author=user, reason="Bulk action resolve"
            )

        for alert_group in alert_groups_to_resolve_list:
            log_record = alert_group.log_records.create(type=AlertGroupLogRecord.TYPE_RESOLVED, author=user)
            send_alert_group_signal.apply_async((log_record.pk,))

    @staticmethod
    def bulk_restart(user: User, alert_groups: "QuerySet[AlertGroup]") -> None:
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

        root_alert_groups_unack = alert_groups.filter(
            resolved=False,
            acknowledged=True,
            root_alert_group__isnull=True,
            maintenance_uuid__isnull=True,  # don't restart maintenance incident
        )
        dependent_alert_groups_unack = AlertGroup.all_objects.filter(root_alert_group__in=root_alert_groups_unack)
        alert_groups_to_restart_unack = root_alert_groups_unack | dependent_alert_groups_unack

        root_alert_groups_unresolve = alert_groups.filter(resolved=True, root_alert_group__isnull=True)
        dependent_alert_groups_unresolve = AlertGroup.all_objects.filter(
            root_alert_group__in=root_alert_groups_unresolve
        )
        alert_groups_to_restart_unresolve = root_alert_groups_unresolve | dependent_alert_groups_unresolve

        alert_groups_to_restart_unsilence = alert_groups.filter(
            resolved=False,
            acknowledged=False,
            silenced=True,
            root_alert_group__isnull=True,
        )

        # convert current qs to list to prevent changes by update
        alert_groups_to_restart_unack_list = list(alert_groups_to_restart_unack)
        alert_groups_to_restart_unresolve_list = list(alert_groups_to_restart_unresolve)
        alert_groups_to_restart_unsilence_list = list(alert_groups_to_restart_unsilence)

        alert_groups_to_restart = (
            alert_groups_to_restart_unack | alert_groups_to_restart_unresolve | alert_groups_to_restart_unsilence
        )

        alert_groups_to_restart.update(
            acknowledged=False,
            acknowledged_at=None,
            acknowledged_by_user=None,
            acknowledged_by=AlertGroup.NOT_YET,
            resolved=False,
            resolved_at=None,
            is_open_for_grouping=None,
            resolved_by_user=None,
            resolved_by=AlertGroup.NOT_YET,
            silenced_until=None,
            silenced_by_user=None,
            silenced_at=None,
            silenced=False,
        )

        # unresolve alert groups
        for alert_group in alert_groups_to_restart_unresolve_list:
            log_record = alert_group.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_RESOLVED,
                author=user,
                reason="Bulk action restart",
            )

            if alert_group.is_root_alert_group:
                alert_group.start_escalation_if_needed()

            send_alert_group_signal.apply_async((log_record.pk,))

        # unacknowledge alert groups
        for alert_group in alert_groups_to_restart_unack_list:
            log_record = alert_group.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_ACK,
                author=user,
                reason="Bulk action restart",
            )

            if alert_group.is_root_alert_group:
                alert_group.start_escalation_if_needed()

            send_alert_group_signal.apply_async((log_record.pk,))

        # unsilence alert groups
        for alert_group in alert_groups_to_restart_unsilence_list:
            log_record = alert_group.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_SILENCE, author=user, reason="Bulk action restart"
            )
            alert_group.start_escalation_if_needed()

            send_alert_group_signal.apply_async((log_record.pk,))

    @staticmethod
    def bulk_silence(user: User, alert_groups: "QuerySet[AlertGroup]", silence_delay: int) -> None:
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")

        now = timezone.now()
        silence_for_period = silence_delay is not None and silence_delay > 0

        if silence_for_period:
            silence_delay_timedelta = timezone.timedelta(seconds=silence_delay)
            silenced_until = now + silence_delay_timedelta
        else:
            silence_delay_timedelta = None
            silenced_until = None

        root_alert_groups_to_silence = alert_groups.filter(
            root_alert_group__isnull=True,
            maintenance_uuid__isnull=True,  # don't silence maintenance incident
        )
        dependent_alert_groups_to_silence = alert_groups.filter(root_alert_group__in=root_alert_groups_to_silence)
        alert_groups_to_silence = root_alert_groups_to_silence | dependent_alert_groups_to_silence
        alert_groups_to_unsilence_before_silence = alert_groups_to_silence.filter(
            silenced=True, acknowledged=False, resolved=False
        )
        alert_groups_to_unacknowledge_before_silence = alert_groups_to_silence.filter(resolved=False, acknowledged=True)
        alert_groups_to_unresolve_before_silence = alert_groups_to_silence.filter(resolved=True)

        # convert current qs to list to prevent changes by update
        alert_groups_to_silence_list = list(alert_groups_to_silence)
        alert_groups_to_unsilence_before_silence_list = list(alert_groups_to_unsilence_before_silence)
        alert_groups_to_unacknowledge_before_silence_list = list(alert_groups_to_unacknowledge_before_silence)
        alert_groups_to_unresolve_before_silence_list = list(alert_groups_to_unresolve_before_silence)

        if silence_for_period:
            alert_groups_to_silence.update(
                acknowledged=False,
                acknowledged_at=None,
                acknowledged_by_user=None,
                acknowledged_by=AlertGroup.NOT_YET,
                resolved=False,
                resolved_at=None,
                resolved_by_user=None,
                resolved_by=AlertGroup.NOT_YET,
                silenced=True,
                silenced_at=now,
                silenced_until=silenced_until,
                silenced_by_user=user,
            )
        else:
            alert_groups_to_silence.update(
                acknowledged=False,
                acknowledged_at=None,
                acknowledged_by_user=None,
                acknowledged_by=AlertGroup.NOT_YET,
                resolved=False,
                resolved_at=None,
                resolved_by_user=None,
                resolved_by=AlertGroup.NOT_YET,
                silenced=True,
                silenced_at=now,
                silenced_until=silenced_until,
                silenced_by_user=user,
                is_escalation_finished=True,
            )

        for alert_group in alert_groups_to_unresolve_before_silence_list:
            alert_group.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_RESOLVED,
                author=user,
                reason="Bulk action silence",
            )

        for alert_group in alert_groups_to_unsilence_before_silence_list:
            alert_group.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_SILENCE,
                author=user,
                reason="Bulk action silence",
            )

        for alert_group in alert_groups_to_unacknowledge_before_silence_list:
            alert_group.log_records.create(
                type=AlertGroupLogRecord.TYPE_UN_ACK,
                author=user,
                reason="Bulk action silence",
            )

        for alert_group in alert_groups_to_silence_list:
            log_record = alert_group.log_records.create(
                type=AlertGroupLogRecord.TYPE_SILENCE,
                author=user,
                silence_delay=silence_delay_timedelta,
                reason="Bulk action silence",
            )

            send_alert_group_signal.apply_async((log_record.pk,))
            if silence_for_period and alert_group.is_root_alert_group:
                alert_group.start_unsilence_task(countdown=silence_delay)

    def start_ack_reminder(self, user: User):
        Organization = apps.get_model("user_management", "Organization")
        unique_unacknowledge_process_id = uuid1()
        logger.info(
            f"AlertGroup acknowledged by user with pk "
            f"{user.pk}, "
            f"acknowledge timeout task has been started with process id {unique_unacknowledge_process_id}"
        )

        seconds = Organization.ACKNOWLEDGE_REMIND_DELAY[self.channel.organization.acknowledge_remind_timeout]
        if seconds > 0:
            delay = timezone.timedelta(seconds=seconds).total_seconds()
            acknowledge_reminder_task.apply_async(
                (
                    self.pk,
                    unique_unacknowledge_process_id,
                ),
                countdown=delay,
            )
            self.last_unique_unacknowledge_process_id = unique_unacknowledge_process_id
            self.save(update_fields=["last_unique_unacknowledge_process_id"])

    def start_call_ack_url(self):
        get_ack_url = self.alerts.first().integration_unique_data.get("ack_url_get", None)
        channel_id = self.slack_message.channel_id if self.slack_message is not None else None
        if get_ack_url and not self.acknowledged_on_source:
            call_ack_url.apply_async(
                (get_ack_url, self.pk, channel_id),
            )
        post_ack_url = self.alerts.first().integration_unique_data.get("ack_url_post", None)
        if post_ack_url and not self.acknowledged_on_source:
            call_ack_url.apply_async(
                (post_ack_url, self.pk, channel_id, "POST"),
            )

    def start_unsilence_task(self, countdown):
        task_id = celery_uuid()
        self.unsilence_task_uuid = task_id

        # recalculate finish escalation time
        escalation_start_time = timezone.now() + timezone.timedelta(seconds=countdown)
        self.estimate_escalation_finish_time = self.calculate_eta_for_finish_escalation(
            start_time=escalation_start_time
        )

        self.save(update_fields=["unsilence_task_uuid", "estimate_escalation_finish_time"])
        unsilence_task.apply_async((self.pk,), task_id=task_id, countdown=countdown)

    @property
    def can_call_ack_url(self):
        return type(self.alerts.first().integration_unique_data) is dict

    @property
    def is_root_alert_group(self):
        return self.root_alert_group is None

    def acknowledge(self, **kwargs):
        if not self.acknowledged:
            self.acknowledged = True
            self.acknowledged_at = timezone.now()

            for k, v in kwargs.items():
                setattr(self, k, v)

            self.save(update_fields=["acknowledged", "acknowledged_at", *kwargs.keys()])

    def unacknowledge(self):
        self.un_silence()
        if self.acknowledged:
            self.acknowledged = False
            self.acknowledged_at = None
            self.acknowledged_by_user = None
            self.acknowledged_by = AlertGroup.NOT_YET
            self.save(update_fields=["acknowledged", "acknowledged_at", "acknowledged_by_user", "acknowledged_by"])

    def resolve(self, **kwargs):
        if not self.resolved:
            self.resolved = True
            self.resolved_at = timezone.now()
            self.is_open_for_grouping = None

            for k, v in kwargs.items():
                setattr(self, k, v)

            self.save(update_fields=["resolved", "resolved_at", "is_open_for_grouping", *kwargs.keys()])

    def unresolve(self):
        self.unacknowledge()
        if self.resolved:
            self.resolved = False
            self.resolved_at = None
            self.resolved_by = AlertGroup.NOT_YET
            self.resolved_by_user = None
            self.save(update_fields=["resolved", "resolved_at", "resolved_by", "resolved_by_user"])

    def silence(self, **kwargs):
        if not self.silenced:
            self.silenced = True
            if "silenced_at" not in kwargs:
                kwargs["silenced_at"] = timezone.now()

            for k, v in kwargs.items():
                setattr(self, k, v)

            self.save(update_fields=["silenced", *kwargs.keys()])

    def un_silence(self):
        self.silenced_until = None
        self.silenced_by_user = None
        self.silenced_at = None
        self.silenced = False
        self.unsilence_task_uuid = None
        self.save(
            update_fields=["silenced_until", "silenced", "silenced_by_user", "silenced_at", "unsilence_task_uuid"]
        )

    def archive(self):
        if self.root_alert_group:
            self.root_alert_group = None
        self.is_archived = True
        self.save(update_fields=["is_archived", "root_alert_group"])

    @property
    def long_verbose_name(self):
        title = str_or_backup(self.slack_templated_first_alert.title, DEFAULT_BACKUP_TITLE)
        return title

    @property
    def long_verbose_name_without_formatting(self):
        sf = SlackFormatter(self.channel.organization)
        title = self.long_verbose_name
        title = sf.format(title)
        title = clean_markup(title)
        return title

    def get_resolve_text(self, mention_user=False):
        if self.resolved_by == AlertGroup.SOURCE:
            return "Resolved by alert source"
        elif self.resolved_by == AlertGroup.ARCHIVED:
            return "Resolved because alert has been archived"
        elif self.resolved_by == AlertGroup.LAST_STEP:
            return "Resolved automatically"
        elif self.resolved_by == AlertGroup.WIPED:
            return "Resolved by wipe"
        elif self.resolved_by == AlertGroup.DISABLE_MAINTENANCE:
            return "Resolved by stop maintenance"
        else:
            if self.resolved_by_user is not None:
                user_text = self.resolved_by_user.get_user_verbal_for_team_for_slack(mention=mention_user)
                return f"Resolved by {user_text}"
            else:
                return "Resolved"

    def get_acknowledge_text(self, mention_user=False):
        if self.acknowledged_by == AlertGroup.SOURCE:
            return "Acknowledged by alert source"
        elif self.acknowledged_by == AlertGroup.USER and self.acknowledged_by_user is not None:
            user_text = self.acknowledged_by_user.get_user_verbal_for_team_for_slack(mention=mention_user)
            return f"Acknowledged by {user_text}"
        else:
            return "Acknowledged"

    def render_after_resolve_report_json(self):
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
        UserNotificationPolicyLogRecord = apps.get_model("base", "UserNotificationPolicyLogRecord")
        ResolutionNote = apps.get_model("alerts", "ResolutionNote")

        log_builder = IncidentLogBuilder(self)
        log_records_list = log_builder.get_log_records_list(with_resolution_notes=True)
        result_log_report = list()

        for log_record in log_records_list:
            if type(log_record) == AlertGroupLogRecord:
                result_log_report.append(log_record.render_log_line_json())
            elif type(log_record) == UserNotificationPolicyLogRecord:
                result_log_report.append(log_record.rendered_notification_log_line_json)
            elif type(log_record) == ResolutionNote:
                result_log_report.append(log_record.render_log_line_json())
        return result_log_report

    @property
    def has_resolution_notes(self):
        return self.resolution_notes.exists()

    def render_resolution_notes_for_csv_report(self):
        result = ""

        resolution_notes = self.resolution_notes.all().prefetch_related("resolution_note_slack_message")
        if len(resolution_notes) > 0:
            result += "Notes: "
            result += " ".join(
                [
                    "{} ({} by {}), ".format(
                        resolution_note.text,
                        resolution_note.created_at.astimezone(pytz.utc),
                        resolution_note.author_verbal(mention=True),
                    )
                    for resolution_note in resolution_notes
                ]
            )
        return result

    @property
    def state(self):
        if self.resolved:
            return "resolved"
        elif self.acknowledged:
            return "acknowledged"
        elif self.silenced:
            return "silenced"
        else:
            return "new"

    @property
    def notify_in_slack_enabled(self):
        channel_filter = self.channel_filter_with_respect_to_escalation_snapshot
        if channel_filter is not None:
            return channel_filter.notify_in_slack
        else:
            return True

    @property
    def is_presented_in_slack(self):
        return self.slack_message and self.channel.organization.slack_team_identity

    @property
    def slack_channel_id(self):
        slack_channel_id = None
        if self.channel.organization.slack_team_identity is not None:
            slack_message = self.get_slack_message()
            if slack_message is not None:
                slack_channel_id = slack_message.channel_id
            elif self.channel_filter is not None:
                slack_channel_id = self.channel_filter.slack_channel_id_or_general_log_id
        return slack_channel_id

    def get_slack_message(self):
        SlackMessage = apps.get_model("slack", "SlackMessage")
        if self.slack_message is None:
            slack_message = SlackMessage.objects.filter(alert_group=self).order_by("created_at").first()
            return slack_message
        return self.slack_message

    @cached_property
    def last_stop_escalation_log(self):
        AlertGroupLogRecord = apps.get_model("alerts", "AlertGroupLogRecord")
        stop_escalation_log = (
            self.log_records.filter(
                type__in=[
                    AlertGroupLogRecord.TYPE_RESOLVED,
                    AlertGroupLogRecord.TYPE_ACK,
                    AlertGroupLogRecord.TYPE_SILENCE,
                ]
            )
            .order_by("pk")
            .last()
        )

        return stop_escalation_log
