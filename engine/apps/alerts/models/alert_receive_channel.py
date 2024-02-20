import logging
import typing
from functools import cached_property
from urllib.parse import urljoin

import emoji
from celery import uuid as celery_uuid
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models, transaction
from django.db.models import BigIntegerField, Case, F, Q, When
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.crypto import get_random_string
from emoji import emojize

from apps.alerts.grafana_alerting_sync_manager.grafana_alerting_sync import GrafanaAlertingSyncManager
from apps.alerts.integration_options_mixin import IntegrationOptionsMixin
from apps.alerts.models.maintainable_object import MaintainableObject
from apps.alerts.tasks import disable_maintenance, disconnect_integration_from_alerting_contact_points
from apps.base.messaging import get_messaging_backend_from_id
from apps.base.utils import live_settings
from apps.integrations.legacy_prefix import remove_legacy_prefix
from apps.integrations.metadata import heartbeat
from apps.integrations.tasks import create_alert, create_alertmanager_alerts
from apps.metrics_exporter.helpers import (
    metrics_add_integrations_to_cache,
    metrics_remove_deleted_integration_from_cache,
    metrics_update_integration_cache,
)
from apps.slack.constants import SLACK_RATE_LIMIT_DELAY, SLACK_RATE_LIMIT_TIMEOUT
from apps.slack.tasks import post_slack_rate_limit_message
from apps.slack.utils import post_message_to_channel
from common.api_helpers.utils import create_engine_url
from common.exceptions import TeamCanNotBeChangedError, UnableToSendDemoAlert
from common.insight_log import EntityEvent, write_resource_insight_log
from common.jinja_templater import jinja_template_env
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import AlertGroup, ChannelFilter
    from apps.labels.models import AlertReceiveChannelAssociatedLabel
    from apps.user_management.models import Organization, Team

logger = logging.getLogger(__name__)


class MessagingBackendTemplatesItem:
    title: str | None
    message: str | None
    image_url: str | None


MessagingBackendTemplates = dict[str, MessagingBackendTemplatesItem]


class AlertmanagerV2LegacyTemplates(typing.TypedDict):
    web_title_template: str | None
    web_message_template: str | None
    web_image_url_template: str | None
    sms_title_template: str | None
    phone_call_title_template: str | None
    source_link_template: str | None
    grouping_id_template: str | None
    resolve_condition_template: str | None
    acknowledge_condition_template: str | None
    slack_title_template: str | None
    slack_message_template: str | None
    slack_image_url_template: str | None
    telegram_title_template: str | None
    telegram_message_template: str | None
    telegram_image_url_template: str | None
    messaging_backends_templates: MessagingBackendTemplates | None


def generate_public_primary_key_for_alert_receive_channel():
    prefix = "C"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while AlertReceiveChannel.objects_with_deleted.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="AlertReceiveChannel"
        )
        failure_counter += 1

    return new_public_primary_key


def random_token_generator():
    return get_random_string(length=25)


def number_to_smiles_translator(number):
    smiles = [
        ":blush:",
        ":ghost:",
        ":apple:",
        ":heart:",
        ":sunglasses:",
        ":package:",
        ":balloon:",
        ":bell:",
        ":beer:",
        ":fire:",
    ]
    smileset = []
    first = True
    while number > 0 or first:
        smileset.append(smiles[number % 10])
        number //= 10
        first = False
    return "".join(reversed(smileset))


class AlertReceiveChannelQueryset(models.QuerySet):
    def delete(self):
        self.update(deleted_at=timezone.now())


class AlertReceiveChannelManager(models.Manager):
    @staticmethod
    def create_missing_direct_paging_integrations(organization: "Organization") -> None:
        from apps.alerts.models import ChannelFilter

        # fetch teams without direct paging integration
        teams_missing_direct_paging = list(
            organization.teams.exclude(
                pk__in=organization.alert_receive_channels.filter(
                    team__isnull=False, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING
                ).values_list("team_id", flat=True)
            )
        )
        if not teams_missing_direct_paging:
            return

        # create missing integrations
        AlertReceiveChannel.objects.bulk_create(
            [
                AlertReceiveChannel(
                    organization=organization,
                    team=team,
                    integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING,
                    verbal_name=f"Direct paging ({team.name} team)",
                )
                for team in teams_missing_direct_paging
            ],
            batch_size=5000,
            ignore_conflicts=True,  # ignore if direct paging integration already exists for team
        )

        # fetch integrations for teams (some of them are created above, but some may already exist previously)
        alert_receive_channels = organization.alert_receive_channels.filter(
            team__in=teams_missing_direct_paging, integration=AlertReceiveChannel.INTEGRATION_DIRECT_PAGING
        )

        # create default routes
        ChannelFilter.objects.bulk_create(
            [
                ChannelFilter(
                    alert_receive_channel=alert_receive_channel,
                    filtering_term=None,
                    is_default=True,
                    order=0,
                )
                for alert_receive_channel in alert_receive_channels
            ],
            batch_size=5000,
            ignore_conflicts=True,  # ignore if default route already exists for integration
        )

        # add integrations to metrics cache
        metrics_add_integrations_to_cache(list(alert_receive_channels), organization)

    def get_queryset(self):
        return AlertReceiveChannelQueryset(self.model, using=self._db).filter(
            ~Q(integration=AlertReceiveChannel.INTEGRATION_MAINTENANCE), Q(deleted_at=None)
        )

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class AlertReceiveChannelManagerWithMaintenance(models.Manager):
    def get_queryset(self):
        return AlertReceiveChannelQueryset(self.model, using=self._db).filter(deleted_at=None)

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class AlertReceiveChannel(IntegrationOptionsMixin, MaintainableObject):
    """
    Channel generated by user to receive Alerts to.
    """

    alert_groups: "RelatedManager['AlertGroup']"
    channel_filters: "RelatedManager['ChannelFilter']"
    organization: "Organization"
    team: typing.Optional["Team"]
    labels: "RelatedManager['AlertReceiveChannelAssociatedLabel']"

    objects = AlertReceiveChannelManager()
    objects_with_maintenance = AlertReceiveChannelManagerWithMaintenance()
    objects_with_deleted = models.Manager()

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_alert_receive_channel,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    integration = models.CharField(
        max_length=100,
        choices=IntegrationOptionsMixin.INTEGRATION_CHOICES,
        default=IntegrationOptionsMixin.DEFAULT_INTEGRATION,
    )

    allow_source_based_resolving = models.BooleanField(default=True)

    token = models.CharField(max_length=30, default=random_token_generator, db_index=True)
    organization = models.ForeignKey(
        "user_management.Organization",
        on_delete=models.CASCADE,
        related_name="alert_receive_channels",
    )
    author = models.ForeignKey(
        "user_management.User", on_delete=models.SET_NULL, related_name="alert_receive_channels", blank=True, null=True
    )
    team = models.ForeignKey(
        "user_management.Team",
        on_delete=models.SET_NULL,
        related_name="alert_receive_channels",
        null=True,
        default=None,
    )

    smile_code = models.TextField(default=":slightly_smiling_face:")

    verbal_name = models.CharField(max_length=150, null=True, default=None)
    description_short = models.CharField(max_length=250, null=True, default=None)

    is_finished_alerting_setup = models.BooleanField(default=False)  # deprecated

    # *_*_template fields are legacy way of storing templates
    # messaging_backends_templates for new integrations' templates
    slack_title_template = models.TextField(null=True, default=None)
    slack_message_template = models.TextField(null=True, default=None)
    slack_image_url_template = models.TextField(null=True, default=None)

    sms_title_template = models.TextField(null=True, default=None)

    phone_call_title_template = models.TextField(null=True, default=None)

    web_title_template = models.TextField(null=True, default=None)
    web_message_template = models.TextField(null=True, default=None)
    web_image_url_template = models.TextField(null=True, default=None)
    web_templates_modified_at = models.DateTimeField(blank=True, null=True)

    # email related fields are deprecated in favour of messaging backend based templates
    # these templates are stored in the messaging_backends_templates field
    email_title_template = models.TextField(null=True, default=None)  # deprecated
    email_message_template = models.TextField(null=True, default=None)  # deprecated

    telegram_title_template = models.TextField(null=True, default=None)
    telegram_message_template = models.TextField(null=True, default=None)
    telegram_image_url_template = models.TextField(null=True, default=None)

    source_link_template = models.TextField(null=True, default=None)
    grouping_id_template = models.TextField(null=True, default=None)
    resolve_condition_template = models.TextField(null=True, default=None)
    acknowledge_condition_template = models.TextField(null=True, default=None)

    # additional messaging backends templates
    # e.g. {'<BACKEND-ID>': {'title': 'title template', 'message': 'message template', 'image_url': 'url template'}}
    messaging_backends_templates: MessagingBackendTemplates | None = models.JSONField(null=True, default=None)

    alertmanager_v2_migrated_at = models.DateTimeField(null=True, default=None)
    """
    Timestamp of when Alertmanager V2 migration was run for this integration using the 'alertmanager_v2_migrate'
    Django management command.
    """

    alertmanager_v2_backup_templates: AlertmanagerV2LegacyTemplates | None = models.JSONField(null=True, default=None)
    """Backing up templates before the Alertmanager V2 migration, so that they can be restored if needed."""

    rate_limited_in_slack_at = models.DateTimeField(null=True, default=None)
    rate_limit_message_task_id = models.CharField(max_length=100, null=True, default=None)

    AlertGroupCustomLabelsDB = list[tuple[str, str | None, str | None]] | None
    alert_group_labels_custom: AlertGroupCustomLabelsDB = models.JSONField(null=True, default=None)
    """
    Stores "custom labels" for alert group labels. Custom labels can be either "plain" or "templated".
    For plain labels, the format is: [<LABEL_KEY_ID>, <LABEL_VALUE_ID>, None]
    For templated labels, the format is: [<LABEL_KEY_ID>, None, <JINJA2_TEMPLATE>]
    """

    alert_group_labels_template: str | None = models.TextField(null=True, default=None)
    """Stores a Jinja2 template for "advanced label templating" for alert group labels."""

    class Meta:
        constraints = [
            # This constraint ensures that there's at most one active direct paging integration per team
            # This should work with SQLite, PostgreSQL and MySQL >= 8.0.13.
            # From the docs: Functional indexes are ignored with MySQL < 8.0.13 and MariaDB as neither supports them.
            # https://docs.djangoproject.com/en/4.2/ref/models/constraints/#expressions
            models.UniqueConstraint(
                F("organization"),
                Case(When(team=None, then=0), default=F("team"), output_field=BigIntegerField()),
                Case(When(deleted_at__isnull=True, then=True), default=None),
                Case(When(integration="direct_paging", then=True), default=None),
                name="unique_direct_paging_integration_per_team",
            )
        ]

    def __str__(self):
        short_name_with_emojis = emojize(self.short_name, language="alias")
        return f"{self.pk}: {short_name_with_emojis}"

    def get_template_attribute(self, render_for, attr_name):
        value = None
        if self.messaging_backends_templates:
            backend_id = render_for.upper()
            value = self.messaging_backends_templates.get(backend_id, {}).get(attr_name)
        return value

    def get_default_template_attribute(self, render_for, attr_name):
        defaults = {}
        backend_id = render_for.upper()
        # check backend exists
        if get_messaging_backend_from_id(backend_id):
            # fallback to web defaults for now
            defaults = getattr(self, f"INTEGRATION_TO_DEFAULT_WEB_{attr_name.upper()}_TEMPLATE", {})
        return defaults.get(self.integration)

    @classmethod
    def create(cls, **kwargs):
        organization = kwargs["organization"]
        with transaction.atomic():
            other_channels = cls.objects_with_deleted.select_for_update().filter(organization=organization)
            channel = cls(**kwargs)
            smile_code = number_to_smiles_translator(other_channels.count())
            verbal_name = (
                kwargs.get("verbal_name") or f"{dict(cls.INTEGRATION_CHOICES)[kwargs['integration']]}" f" {smile_code}"
            )
            channel.smile_code = smile_code
            channel.verbal_name = verbal_name
            channel.save()
        return channel

    def delete(self):
        self.deleted_at = timezone.now()
        self.save()

    def hard_delete(self):
        super(AlertReceiveChannel, self).delete()

    class DuplicateDirectPagingError(Exception):
        """Only one Direct Paging integration is allowed per team."""

        DETAIL = "Direct paging integration already exists for this team"  # Returned in BadRequest responses

    def save(self, *args, **kwargs):
        # Don't allow multiple Direct Paging integrations per team
        if (
            self.integration == AlertReceiveChannel.INTEGRATION_DIRECT_PAGING
            and not self.deleted_at
            and AlertReceiveChannel.objects.filter(
                organization=self.organization, team=self.team, integration=self.integration
            )
            .exclude(pk=self.pk)
            .exists()
        ):
            raise self.DuplicateDirectPagingError

        return super().save(*args, **kwargs)

    def change_team(self, team_id, user):
        if team_id == self.team_id:
            raise TeamCanNotBeChangedError("Integration is already in this team")

        if team_id is not None:
            new_team = user.available_teams.filter(public_primary_key=team_id).first()
            if not new_team:
                raise TeamCanNotBeChangedError("User is not a member of the selected team")
        else:
            new_team = None  # means General team
        self.team = new_team
        self.save(update_fields=["team"])

    @cached_property
    def grafana_alerting_sync_manager(self):
        return GrafanaAlertingSyncManager(self)

    @property
    def is_alerting_integration(self):
        return self.integration in {
            AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
            AlertReceiveChannel.INTEGRATION_LEGACY_GRAFANA_ALERTING,
        }

    @cached_property
    def team_name(self):
        return self.team.name if self.team else "No team"

    @cached_property
    def team_id_or_no_team(self):
        return self.team_id if self.team else "no_team"

    @cached_property
    def emojized_verbal_name(self):
        return emoji.emojize(self.verbal_name, language="alias")

    @property
    def new_incidents_web_link(self):
        return urljoin(
            self.organization.web_link, f"?page=incidents&integration={self.public_primary_key}&status=0&p=1"
        )

    @property
    def is_rate_limited_in_slack(self):
        return (
            self.rate_limited_in_slack_at is not None
            and self.rate_limited_in_slack_at + SLACK_RATE_LIMIT_TIMEOUT > timezone.now()
        )

    def start_send_rate_limit_message_task(self, delay=SLACK_RATE_LIMIT_DELAY):
        task_id = celery_uuid()
        self.rate_limit_message_task_id = task_id
        self.rate_limited_in_slack_at = timezone.now()
        self.save(update_fields=["rate_limit_message_task_id", "rate_limited_in_slack_at"])
        post_slack_rate_limit_message.apply_async((self.pk,), countdown=delay, task_id=task_id)

    @property
    def alert_groups_count(self):
        return self.alert_groups.count()

    @property
    def alerts_count(self):
        from apps.alerts.models import Alert

        return Alert.objects.filter(group__channel=self).count()

    @property
    def is_able_to_autoresolve(self) -> bool:
        return self.config.is_able_to_autoresolve

    @property
    def is_demo_alert_enabled(self):
        return self.config.is_demo_alert_enabled

    @property
    def description(self) -> str | None:
        # TODO: AMV2: Remove this check after legacy integrations are migrated.
        if self.integration == AlertReceiveChannel.INTEGRATION_LEGACY_GRAFANA_ALERTING:
            contact_points = self.contact_points.all()
            rendered_description = jinja_template_env.from_string(self.config.description).render(
                is_finished_alerting_setup=self.is_finished_alerting_setup,
                grafana_alerting_entities=[
                    {
                        "alertmanager_name": f"""
                        {'Grafana' if contact_point.datasource_name == 'grafana' else contact_point.datasource_name}
                        """,
                        "contact_point_url": f"/alerting/notifications/receivers/{self.emojized_verbal_name}/"
                        f"edit?alertmanager={contact_point.datasource_name}",
                        "routes_url": f"/alerting/routes?alertmanager={contact_point.datasource_name}",
                    }
                    for contact_point in contact_points
                ],
            )
        else:
            rendered_description = self.config.description
        return rendered_description

    @classmethod
    def get_or_create_manual_integration(cls, defaults, **kwargs):
        try:
            alert_receive_channel = cls.objects.get(
                organization=kwargs["organization"],
                integration=kwargs["integration"],
                team=kwargs["team"],
                deleted_at=None,
            )
        except cls.DoesNotExist:
            kwargs.update(defaults)
            alert_receive_channel = cls.create(**kwargs)
        except cls.MultipleObjectsReturned:
            # general team may inherit integrations from deleted teams
            alert_receive_channel = cls.objects.filter(
                organization=kwargs["organization"],
                integration=kwargs["integration"],
                team=kwargs["team"],
                deleted_at=None,
            ).first()
        return alert_receive_channel

    @property
    def short_name(self):
        if self.verbal_name is None:
            return self.created_name + "" if self.deleted_at is None else "(Deleted)"
        elif self.verbal_name == self.created_name:
            return self.verbal_name
        else:
            return (
                f"{self.verbal_name} - {self.get_integration_display()}"
                f"{'' if self.deleted_at is None else '(Deleted)'}"
            )

    @property
    def short_name_with_maintenance_status(self):
        if self.maintenance_mode is not None:
            return (
                self.short_name + f" *[ on "
                f"{AlertReceiveChannel.MAINTENANCE_MODE_CHOICES[self.maintenance_mode][1]}"
                f" :construction: ]*"
            )
        else:
            return self.short_name

    @property
    def created_name(self):
        return f"{self.get_integration_display()} {self.smile_code}"

    @property
    def web_link(self):
        return urljoin(self.organization.web_link, f"integrations/{self.public_primary_key}")

    @property
    def integration_url(self) -> str | None:
        if self.integration in [
            AlertReceiveChannel.INTEGRATION_MANUAL,
            AlertReceiveChannel.INTEGRATION_SLACK_CHANNEL,
            AlertReceiveChannel.INTEGRATION_INBOUND_EMAIL,
            AlertReceiveChannel.INTEGRATION_MAINTENANCE,
        ]:
            return None
        slug = remove_legacy_prefix(self.config.slug)
        return create_engine_url(f"integrations/v1/{slug}/{self.token}/")

    @property
    def inbound_email(self):
        if self.integration != AlertReceiveChannel.INTEGRATION_INBOUND_EMAIL:
            return None

        return f"{self.token}@{live_settings.INBOUND_EMAIL_DOMAIN}"

    @property
    def default_channel_filter(self):
        return self.channel_filters.filter(is_default=True).first()

    # Templating
    @property
    def templates(self):
        return {
            "grouping_key": self.grouping_id_template,
            "resolve_signal": self.resolve_condition_template,
            "acknowledge_signal": self.acknowledge_condition_template,
            "source_link": self.source_link_template,
            "slack": {
                "title": self.slack_title_template,
                "message": self.slack_message_template,
                "image_url": self.slack_image_url_template,
            },
            "web": {
                "title": self.web_title_template,
                "message": self.web_message_template,
                "image_url": self.web_image_url_template,
            },
            "sms": {
                "title": self.sms_title_template,
            },
            "phone_call": {
                "title": self.phone_call_title_template,
            },
            "telegram": {
                "title": self.telegram_title_template,
                "message": self.telegram_message_template,
                "image_url": self.telegram_image_url_template,
            },
        }

    @property
    def is_available_for_custom_templates(self):
        return True

    # Maintenance
    def start_disable_maintenance_task(self, countdown):
        maintenance_uuid = disable_maintenance.apply_async(
            args=(),
            kwargs={
                "alert_receive_channel_id": self.pk,
            },
            countdown=countdown,
        )
        return maintenance_uuid

    def get_organization(self):
        return self.organization

    def get_team(self):
        return self.team

    def get_verbal(self):
        return self.verbal_name

    def force_disable_maintenance(self, user):
        disable_maintenance(alert_receive_channel_id=self.pk, force=True, user_id=user.pk)

    def notify_about_maintenance_action(self, text, send_to_general_log_channel=True):
        # TODO: this method should be refactored.
        # It's binded to slack and sending maintenance notification only there.
        channel_ids = list(
            self.channel_filters.filter(slack_channel_id__isnull=False, notify_in_slack=False).values_list(
                "slack_channel_id", flat=True
            )
        )

        if send_to_general_log_channel:
            general_log_channel_id = self.organization.general_log_channel_id
            if general_log_channel_id is not None:
                channel_ids.append(general_log_channel_id)
        unique_channels_id = set(channel_ids)
        for channel_id in unique_channels_id:
            post_message_to_channel(self.organization, channel_id, text)

    # Heartbeat
    @property
    def is_available_for_integration_heartbeat(self) -> bool:
        return self.heartbeat_module is not None

    @property
    def heartbeat_restored_title(self):
        return self.heartbeat_module.heartbeat_restored_title

    @property
    def heartbeat_restored_message(self):
        return self.heartbeat_module.heartbeat_restored_message

    @property
    def heartbeat_restored_payload(self):
        return self.heartbeat_module.heartbeat_restored_payload

    @property
    def heartbeat_expired_title(self):
        return self.heartbeat_module.heartbeat_expired_title

    @property
    def heartbeat_expired_message(self):
        return self.heartbeat_module.heartbeat_expired_message

    @property
    def heartbeat_expired_payload(self):
        return self.heartbeat_module.heartbeat_expired_payload

    @property
    def heartbeat_module(self):
        return getattr(heartbeat, self.integration, None)

    # Demo alerts
    def send_demo_alert(self, payload: typing.Optional[typing.Dict] = None) -> None:
        logger.info(f"send_demo_alert integration={self.pk}")

        if not self.is_demo_alert_enabled:
            raise UnableToSendDemoAlert("Unable to send demo alert for this integration.")

        if payload is None:
            payload = self.config.example_payload

        # hack to keep demo alert working for integration with legacy alertmanager behaviour.
        if self.integration in {
            AlertReceiveChannel.INTEGRATION_LEGACY_GRAFANA_ALERTING,
            AlertReceiveChannel.INTEGRATION_LEGACY_ALERTMANAGER,
            AlertReceiveChannel.INTEGRATION_GRAFANA,
        }:
            alerts = payload.get("alerts", None)
            if not isinstance(alerts, list) or not len(alerts):
                raise UnableToSendDemoAlert(
                    "Unable to send demo alert as payload has no 'alerts' key, it is not array, or it is empty."
                )
            for alert in alerts:
                create_alertmanager_alerts.delay(alert_receive_channel_pk=self.pk, alert=alert, is_demo=True)
        else:
            timestamp = timezone.now().isoformat()
            create_alert.delay(
                title="Demo alert",
                message="Demo alert",
                image_url=None,
                link_to_upstream_details=None,
                alert_receive_channel_pk=self.pk,
                integration_unique_data=None,
                raw_request_data=payload,
                is_demo=True,
                received_at=timestamp,
            )

    @property
    def based_on_alertmanager(self):
        return getattr(self.config, "based_on_alertmanager", False)

    # Insight logs
    @property
    def insight_logs_type_verbal(self):
        return "integration"

    @property
    def insight_logs_verbal(self):
        return self.verbal_name

    @property
    def insight_logs_serialized(self):
        result = {
            "name": self.verbal_name,
            "allow_source_based_resolving": self.allow_source_based_resolving,
            "slack_title": self.slack_title_template or "default",
            "slack_message": self.slack_message_template or "default",
            "slack_image_url": self.slack_image_url_template or "default",
            "sms_title": self.sms_title_template or "default",
            "phone_call_title": self.phone_call_title_template or "default",
            "web_title": self.web_title_template or "default",
            "web_message": self.web_message_template or "default",
            "web_image_url_template": self.web_image_url_template or "default",
            "telegram_title": self.telegram_title_template or "default",
            "telegram_message": self.telegram_message_template or "default",
            "telegram_image_url": self.telegram_image_url_template or "default",
            "source_link": self.source_link_template or "default",
            "grouping_id": self.grouping_id_template or "default",
            "resolve_condition": self.resolve_condition_template or "default",
            "acknowledge_condition": self.acknowledge_condition_template or "default",
        }
        if self.team:
            result["team"] = self.team.name
            result["team_id"] = self.team.public_primary_key
        else:
            result["team"] = "General"
        return result

    @property
    def insight_logs_metadata(self):
        result = {}
        if self.team:
            result["team"] = self.team.name
            result["team_id"] = self.team.public_primary_key
        else:
            result["team"] = "General"
        return result


@receiver(post_save, sender=AlertReceiveChannel)
def listen_for_alertreceivechannel_model_save(
    sender: AlertReceiveChannel, instance: AlertReceiveChannel, created: bool, *args, **kwargs
) -> None:
    from apps.alerts.models import ChannelFilter
    from apps.heartbeat.models import IntegrationHeartBeat

    if created:
        write_resource_insight_log(instance=instance, author=instance.author, event=EntityEvent.CREATED)
        default_filter = ChannelFilter(alert_receive_channel=instance, filtering_term=None, is_default=True)
        default_filter.save()
        write_resource_insight_log(instance=default_filter, author=instance.author, event=EntityEvent.CREATED)

        TEN_MINUTES = 600  # this is timeout for cloud heartbeats
        if instance.is_available_for_integration_heartbeat:
            heartbeat = IntegrationHeartBeat.objects.create(alert_receive_channel=instance, timeout_seconds=TEN_MINUTES)
            write_resource_insight_log(instance=heartbeat, author=instance.author, event=EntityEvent.CREATED)

        metrics_add_integrations_to_cache([instance], instance.organization)

    elif instance.deleted_at:
        if instance.is_alerting_integration:
            disconnect_integration_from_alerting_contact_points.apply_async((instance.pk,), countdown=5)

        metrics_remove_deleted_integration_from_cache(instance)
    else:
        metrics_update_integration_cache(instance)
