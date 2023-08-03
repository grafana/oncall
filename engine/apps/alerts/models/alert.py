import hashlib
import logging
import typing
from uuid import uuid4

from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import JSONField

from apps.alerts import tasks
from apps.alerts.constants import TASK_DELAY_SECONDS
from apps.alerts.incident_appearance.templaters import TemplateLoader
from common.jinja_templater import apply_jinja_template
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import AlertGroup

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

    def get_integration_optimization_hash(self):
        """
        Should be overloaded in child classes.
        """
        raise NotImplementedError

    @classmethod
    def create(
        cls,
        title,
        message,
        image_url,
        link_to_upstream_details,
        alert_receive_channel,
        integration_unique_data,
        raw_request_data,
        enable_autoresolve=True,
        is_demo=False,
        channel_filter=None,
        force_route_id=None,
    ):
        """
        Creates an alert and a group if needed.
        """
        # This import is here to avoid circular imports
        from apps.alerts.models import AlertGroup, AlertGroupLogRecord, AlertReceiveChannel, ChannelFilter

        group_data = Alert.render_group_data(alert_receive_channel, raw_request_data, is_demo)
        if channel_filter is None:
            channel_filter = ChannelFilter.select_filter(alert_receive_channel, raw_request_data, force_route_id)

        group, group_created = AlertGroup.objects.get_or_create_grouping(
            channel=alert_receive_channel,
            channel_filter=channel_filter,
            group_data=group_data,
        )

        if group_created:
            group.log_records.create(type=AlertGroupLogRecord.TYPE_REGISTERED)
            group.log_records.create(type=AlertGroupLogRecord.TYPE_ROUTE_ASSIGNED)

        mark_as_resolved = (
            enable_autoresolve and group_data.is_resolve_signal and alert_receive_channel.allow_source_based_resolving
        )
        if not group.resolved and mark_as_resolved:
            group.resolve_by_source()

        mark_as_acknowledged = group_data.is_acknowledge_signal
        if not group.acknowledged and mark_as_acknowledged:
            group.acknowledge_by_source()

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

        # Store exact alert which resolved group.
        if group.resolved_by == AlertGroup.SOURCE and group.resolved_by_alert is None:
            group.resolved_by_alert = alert
            group.save(update_fields=["resolved_by_alert"])

        if settings.DEBUG:
            tasks.distribute_alert(alert.pk)
        else:
            tasks.distribute_alert.apply_async((alert.pk,), countdown=TASK_DELAY_SECONDS)

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
                    tasks.send_alert_group_signal.apply_async((log_record_for_root_incident.pk,))
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
    def render_group_data(cls, alert_receive_channel, raw_request_data, is_demo=False):
        from apps.alerts.models import AlertGroup

        template_manager = TemplateLoader()

        is_resolve_signal = False
        is_acknowledge_signal = False
        group_distinction = None

        acknowledge_condition_template = template_manager.get_attr_template(
            "acknowledge_condition", alert_receive_channel
        )
        resolve_condition_template = template_manager.get_attr_template("resolve_condition", alert_receive_channel)
        grouping_id_template = template_manager.get_attr_template("grouping_id", alert_receive_channel)

        # set web_title_cache to web title to allow alert group searching based on web_title_cache
        web_title_template = template_manager.get_attr_template("title", alert_receive_channel, render_for="web")
        if web_title_template:
            try:
                web_title_cache = apply_jinja_template(web_title_template, raw_request_data)
            except (JinjaTemplateError, JinjaTemplateWarning) as e:
                web_title_cache = e.fallback_message
                logger.warning(
                    f"web_title_cache error on channel={alert_receive_channel.public_primary_key}: {e.fallback_message}"
                )
        else:
            web_title_cache = None

        if grouping_id_template is not None:
            try:
                group_distinction = apply_jinja_template(grouping_id_template, raw_request_data)
            except (JinjaTemplateError, JinjaTemplateWarning) as e:
                logger.warning(
                    f"grouping_id_template error on channel={alert_receive_channel.public_primary_key}: {e.fallback_message}"
                )

        # Insert random uuid to prevent grouping of demo alerts or alerts with group_distinction=None
        if is_demo or not group_distinction:
            group_distinction = cls.insert_random_uuid(group_distinction)

        if group_distinction is not None:
            group_distinction = hashlib.md5(str(group_distinction).encode()).hexdigest()

        if resolve_condition_template is not None:
            try:
                is_resolve_signal = apply_jinja_template(resolve_condition_template, payload=raw_request_data)
            except (JinjaTemplateError, JinjaTemplateWarning) as e:
                logger.warning(
                    f"resolve_condition_template error on channel={alert_receive_channel.public_primary_key}: {e.fallback_message}"
                )

            if isinstance(is_resolve_signal, str):
                is_resolve_signal = is_resolve_signal.strip().lower() in ["1", "true", "ok"]
            else:
                is_resolve_signal = False
        if acknowledge_condition_template is not None:
            try:
                is_acknowledge_signal = apply_jinja_template(acknowledge_condition_template, payload=raw_request_data)
            except (JinjaTemplateError, JinjaTemplateWarning) as e:
                logger.warning(
                    f"acknowledge_condition_template error on channel={alert_receive_channel.public_primary_key}: {e.fallback_message}"
                )

            if isinstance(is_acknowledge_signal, str):
                is_acknowledge_signal = is_acknowledge_signal.strip().lower() in ["1", "true", "ok"]
            else:
                is_acknowledge_signal = False

        return AlertGroup.GroupData(
            is_resolve_signal=is_resolve_signal,
            is_acknowledge_signal=is_acknowledge_signal,
            group_distinction=group_distinction,
            web_title_cache=web_title_cache,
        )

    @staticmethod
    def insert_random_uuid(distinction):
        if distinction is not None:
            distinction += str(uuid4())
        else:
            distinction = str(uuid4())

        return distinction
