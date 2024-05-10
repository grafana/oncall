import hashlib
import logging
import typing
from functools import partial
from uuid import uuid4

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models, transaction
from django.db.models import JSONField

from apps.alerts import tasks
from apps.alerts.constants import TASK_DELAY_SECONDS
from apps.alerts.incident_appearance.templaters import TemplateLoader
from apps.alerts.signals import alert_group_escalation_snapshot_built
from apps.alerts.tasks.distribute_alert import send_alert_create_signal
from apps.labels.alert_group_labels import assign_labels, gather_labels_from_alert_receive_channel_and_raw_request_data
from apps.labels.types import AlertLabels
from common.jinja_templater import apply_jinja_template_to_alert_payload_and_labels
from common.jinja_templater.apply_jinja_template import (
    JinjaTemplateError,
    JinjaTemplateWarning,
    templated_value_is_truthy,
)
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import AlertGroup, AlertReceiveChannel, ChannelFilter

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def generate_public_primary_key_for_alert():
    prefix = "A"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while Alert.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="Alert"
        )
        failure_counter += 1

    return new_public_primary_key


class Alert(models.Model):
    group: typing.Optional["AlertGroup"]
    resolved_alert_groups: "RelatedManager['AlertGroup']"

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_alert,
    )

    is_resolve_signal = models.BooleanField(default=False)
    is_the_first_alert_in_group = models.BooleanField(default=False)
    message = models.TextField(max_length=3000, default=None, null=True)
    image_url = models.URLField(default=None, null=True, max_length=300)
    delivered = models.BooleanField(default=False)
    title = models.TextField(max_length=1500, default=None, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    link_to_upstream_details = models.URLField(max_length=500, default=None, null=True)
    integration_unique_data = JSONField(default=None, null=True)
    raw_request_data = JSONField()

    # This hash is for integration-specific needs
    integration_optimization_hash = models.CharField(max_length=100, db_index=True, default=None, null=True)

    group = models.ForeignKey(
        "alerts.AlertGroup", on_delete=models.CASCADE, null=True, default=None, related_name="alerts"
    )

    RawRequestData: typing.TypeAlias = typing.Union[typing.Dict, typing.List]

    def get_integration_optimization_hash(self):
        """
        Should be overloaded in child classes.
        """
        raise NotImplementedError

    @classmethod
    def create(
        cls,
        title: typing.Optional[str],
        message: typing.Optional[str],
        image_url: typing.Optional[str],
        link_to_upstream_details: typing.Optional[str],
        alert_receive_channel: "AlertReceiveChannel",
        integration_unique_data: typing.Optional[typing.Dict],
        raw_request_data: RawRequestData,
        enable_autoresolve=True,
        is_demo: bool = False,
        channel_filter: typing.Optional["ChannelFilter"] = None,
        received_at: typing.Optional[str] = None,
    ) -> "Alert":
        """
        Creates an alert and a group if needed.
        """
        # This import is here to avoid circular imports
        from apps.alerts.models import AlertGroup, AlertGroupLogRecord, AlertReceiveChannel, ChannelFilter

        parsed_labels = gather_labels_from_alert_receive_channel_and_raw_request_data(
            alert_receive_channel, raw_request_data
        )
        group_data = Alert.render_group_data(alert_receive_channel, raw_request_data, parsed_labels, is_demo)

        if channel_filter is None:
            channel_filter = ChannelFilter.select_filter(alert_receive_channel, raw_request_data, parsed_labels)

        # Get or create group
        group, group_created = AlertGroup.objects.get_or_create_grouping(
            channel=alert_receive_channel,
            channel_filter=channel_filter,
            group_data=group_data,
            received_at=received_at,
        )
        logger.debug(f"alert group {group.pk} created={group_created}")

        # Create alert
        alert = cls(
            is_resolve_signal=group_data.is_resolve_signal,
            title=title,
            message=message,
            image_url=image_url,
            link_to_upstream_details=link_to_upstream_details,
            group=group,
            integration_unique_data=integration_unique_data,
            raw_request_data=raw_request_data,
            is_the_first_alert_in_group=group_created,
        )
        alert.save()
        logger.debug(f"alert {alert.pk} created for alert group {group.pk}")

        transaction.on_commit(partial(send_alert_create_signal.apply_async, (alert.pk,)))

        if group_created:
            assign_labels(group, alert_receive_channel, parsed_labels)
            group.log_records.create(type=AlertGroupLogRecord.TYPE_REGISTERED)
            group.log_records.create(type=AlertGroupLogRecord.TYPE_ROUTE_ASSIGNED)

        if group_created or alert.group.pause_escalation:
            # Build escalation snapshot if needed and start escalation
            alert.group.start_escalation_if_needed(countdown=TASK_DELAY_SECONDS)

        if group_created:
            # TODO: consider moving to start_escalation_if_needed
            alert_group_escalation_snapshot_built.send(sender=cls.__class__, alert_group=alert.group)

        mark_as_acknowledged = group_data.is_acknowledge_signal
        if not group.acknowledged and mark_as_acknowledged:
            group.acknowledge_by_source()

        mark_as_resolved = (
            enable_autoresolve and group_data.is_resolve_signal and alert_receive_channel.allow_source_based_resolving
        )
        if not group.resolved and mark_as_resolved:
            group.resolve_by_source()

        # Store exact alert which resolved group.
        if group.resolved_by == AlertGroup.SOURCE and group.resolved_by_alert is None:
            group.resolved_by_alert = alert
            group.save(update_fields=["resolved_by_alert"])

        if group_created:
            # all code below related to maintenance mode
            maintenance_uuid = None

            if alert_receive_channel.maintenance_mode == AlertReceiveChannel.MAINTENANCE:
                maintenance_uuid = alert_receive_channel.maintenance_uuid

            if maintenance_uuid is not None:
                try:
                    maintenance_incident = AlertGroup.objects.get(maintenance_uuid=maintenance_uuid)
                    group.root_alert_group = maintenance_incident
                    group.save(update_fields=["root_alert_group"])
                    log_record_for_root_incident = maintenance_incident.log_records.create(
                        type=AlertGroupLogRecord.TYPE_ATTACHED, dependent_alert_group=group, reason="Attach dropdown"
                    )
                    logger.debug(
                        f"call send_alert_group_signal for alert_group {maintenance_incident.pk} (maintenance), "
                        f"log record {log_record_for_root_incident.pk} with type "
                        f"'{log_record_for_root_incident.get_type_display()}'"
                    )
                    transaction.on_commit(partial(tasks.send_alert_group_signal.delay, log_record_for_root_incident.pk))
                except AlertGroup.DoesNotExist:
                    pass

        return alert

    def wipe(self, wiped_by, wiped_at):
        wiped_by_user_verbal = "by " + wiped_by.username

        self.integration_unique_data = {}
        self.raw_request_data = {}
        self.title = f"Wiped {wiped_by_user_verbal} at {wiped_at.strftime('%Y-%m-%d')}"
        self.message = ""
        self.image_url = None
        self.link_to_upstream_details = None
        self.save(
            update_fields=[
                "integration_unique_data",
                "raw_request_data",
                "title",
                "message",
                "image_url",
                "link_to_upstream_details",
            ]
        )

    @classmethod
    def _apply_jinja_template_to_alert_payload_and_labels(
        cls,
        template: str,
        template_name: str,
        alert_receive_channel: "AlertReceiveChannel",
        raw_request_data: RawRequestData,
        labels: typing.Optional[AlertLabels],
        use_error_msg_as_fallback=False,
        check_if_templated_value_is_truthy=False,
    ) -> typing.Union[str, None, bool]:
        try:
            templated_value = apply_jinja_template_to_alert_payload_and_labels(template, raw_request_data, labels)
            return templated_value_is_truthy(templated_value) if check_if_templated_value_is_truthy else templated_value
        except (JinjaTemplateError, JinjaTemplateWarning) as e:
            fallback_msg = e.fallback_message

            logger.warning(
                f"{template_name} error on channel={alert_receive_channel.public_primary_key}: {fallback_msg}"
            )

            if use_error_msg_as_fallback:
                return fallback_msg
            elif check_if_templated_value_is_truthy:
                return False
            return None

    @classmethod
    def render_group_data(
        cls,
        alert_receive_channel: "AlertReceiveChannel",
        raw_request_data: RawRequestData,
        labels: typing.Optional[AlertLabels],
        is_demo=False,
    ) -> "AlertGroup.GroupData":
        from apps.alerts.models import AlertGroup

        template_manager = TemplateLoader()

        is_resolve_signal = False
        is_acknowledge_signal = False
        group_distinction: typing.Optional[str] = None
        web_title_cache: typing.Optional[str] = None

        # set web_title_cache to web title to allow alert group searching based on web_title_cache
        if (
            web_title_template := template_manager.get_attr_template("title", alert_receive_channel, render_for="web")
        ) is not None:
            web_title_cache = cls._apply_jinja_template_to_alert_payload_and_labels(
                web_title_template,
                "web_title_cache",
                alert_receive_channel,
                raw_request_data,
                labels,
                use_error_msg_as_fallback=True,
            )

        if (
            grouping_id_template := template_manager.get_attr_template("grouping_id", alert_receive_channel)
        ) is not None:
            group_distinction = cls._apply_jinja_template_to_alert_payload_and_labels(
                grouping_id_template, "grouping_id_template", alert_receive_channel, raw_request_data, labels
            )

        # Insert random uuid to prevent grouping of demo alerts or alerts with group_distinction=None
        if is_demo or not group_distinction:
            group_distinction = cls.insert_random_uuid(group_distinction)

        if group_distinction is not None:
            group_distinction = hashlib.md5(str(group_distinction).encode()).hexdigest()

        if (
            resolve_condition_template := template_manager.get_attr_template("resolve_condition", alert_receive_channel)
        ) is not None:
            is_resolve_signal = cls._apply_jinja_template_to_alert_payload_and_labels(
                resolve_condition_template,
                "resolve_condition_template",
                alert_receive_channel,
                raw_request_data,
                labels,
                check_if_templated_value_is_truthy=True,
            )

        if (
            acknowledge_condition_template := template_manager.get_attr_template(
                "acknowledge_condition", alert_receive_channel
            )
        ) is not None:
            is_acknowledge_signal = cls._apply_jinja_template_to_alert_payload_and_labels(
                acknowledge_condition_template,
                "acknowledge_condition_template",
                alert_receive_channel,
                raw_request_data,
                labels,
                check_if_templated_value_is_truthy=True,
            )

        return AlertGroup.GroupData(
            is_resolve_signal=is_resolve_signal,
            is_acknowledge_signal=is_acknowledge_signal,
            group_distinction=group_distinction,
            web_title_cache=web_title_cache,
        )

    @staticmethod
    def insert_random_uuid(distinction: typing.Optional[str]) -> str:
        if distinction is not None:
            distinction += str(uuid4())
        else:
            distinction = str(uuid4())

        return distinction
