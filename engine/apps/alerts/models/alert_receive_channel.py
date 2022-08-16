import logging
from functools import cached_property
from urllib.parse import urljoin

import emoji
from celery import uuid as celery_uuid
from django.apps import apps
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models, transaction
from django.db.models import Count, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.crypto import get_random_string
from emoji import emojize
from jinja2 import Template

from apps.alerts.grafana_alerting_sync_manager.grafana_alerting_sync import GrafanaAlertingSyncManager
from apps.alerts.integration_options_mixin import IntegrationOptionsMixin
from apps.alerts.models.maintainable_object import MaintainableObject
from apps.alerts.tasks import disable_maintenance, sync_grafana_alerting_contact_points
from apps.base.messaging import get_messaging_backend_from_id
from apps.base.utils import live_settings
from apps.integrations.metadata import heartbeat
from apps.integrations.tasks import create_alert, create_alertmanager_alerts
from apps.slack.constants import SLACK_RATE_LIMIT_DELAY, SLACK_RATE_LIMIT_TIMEOUT
from apps.slack.tasks import post_slack_rate_limit_message
from apps.slack.utils import post_message_to_channel
from common.api_helpers.utils import create_engine_url
from common.exceptions import TeamCanNotBeChangedError, UnableToSendDemoAlert
from common.insight_log import EntityEvent, entity_insight_log
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

logger = logging.getLogger(__name__)


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

    integration_slack_channel_id = models.CharField(max_length=150, null=True, default=None)

    is_finished_alerting_setup = models.BooleanField(default=False)

    slack_title_template = models.TextField(null=True, default=None)
    slack_message_template = models.TextField(null=True, default=None)
    slack_image_url_template = models.TextField(null=True, default=None)

    sms_title_template = models.TextField(null=True, default=None)

    phone_call_title_template = models.TextField(null=True, default=None)

    web_title_template = models.TextField(null=True, default=None)
    web_message_template = models.TextField(null=True, default=None)
    web_image_url_template = models.TextField(null=True, default=None)

    email_title_template = models.TextField(null=True, default=None)
    email_message_template = models.TextField(null=True, default=None)

    telegram_title_template = models.TextField(null=True, default=None)
    telegram_message_template = models.TextField(null=True, default=None)
    telegram_image_url_template = models.TextField(null=True, default=None)

    source_link_template = models.TextField(null=True, default=None)
    grouping_id_template = models.TextField(null=True, default=None)
    resolve_condition_template = models.TextField(null=True, default=None)
    acknowledge_condition_template = models.TextField(null=True, default=None)

    PUBLIC_TEMPLATES_FIELDS = {
        "grouping_key": "grouping_id_template",
        "resolve_signal": "resolve_condition_template",
        "acknowledge_signal": "acknowledge_condition_template",
        "slack": {
            "title": "slack_title_template",
            "message": "slack_message_template",
            "image_url": "slack_image_url_template",
        },
        "web": {
            "title": "web_title_template",
            "message": "web_message_template",
            "image_url": "web_image_url_template",
        },
        "sms": {
            "title": "sms_title_template",
        },
        "phone_call": {
            "title": "phone_call_title_template",
        },
        "email": {
            "title": "email_title_template",
            "message": "email_message_template",
        },
        "telegram": {
            "title": "telegram_title_template",
            "message": "telegram_message_template",
            "image_url": "telegram_image_url_template",
        },
    }

    # additional messaging backends templates
    # e.g. {'<BACKEND-ID>': {'title': 'title template', 'message': 'message template', 'image_url': 'url template'}}
    messaging_backends_templates = models.JSONField(null=True, default=None)

    rate_limited_in_slack_at = models.DateTimeField(null=True, default=None)
    rate_limit_message_task_id = models.CharField(max_length=100, null=True, default=None)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "verbal_name", "deleted_at"],
                name="unique integration name",
            )
        ]

    def __str__(self):
        short_name_with_emojis = emojize(self.short_name, use_aliases=True)
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
        with transaction.atomic():
            other_channels = cls.objects_with_deleted.select_for_update().filter(organization=kwargs["organization"])
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

    def change_team(self, team_id, user):
        EscalationPolicy = apps.get_model("alerts", "EscalationPolicy")

        if team_id == self.team_id:
            raise TeamCanNotBeChangedError("Integration is already in this team")

        if team_id is not None:
            new_team = user.teams.filter(public_primary_key=team_id).first()
            if not new_team:
                raise TeamCanNotBeChangedError("User is not a member of the selected team")
        else:
            new_team = None  # means General team

        escalation_chains_pks = self.channel_filters.all().values_list("escalation_chain", flat=True)
        escalation_chains = self.organization.escalation_chains.filter(pk__in=escalation_chains_pks).annotate(
            num_integrations=Count(
                "channel_filters__alert_receive_channel",
                distinct=True,
                filter=Q(channel_filters__alert_receive_channel__deleted_at__isnull=True),
            ),
        )
        if escalation_chains:
            # check if escalation chains are connected to routes of other integrations
            shared_escalation_chains = []
            for escalation_chain in escalation_chains:
                if escalation_chain.num_integrations > 1:
                    shared_escalation_chains.append(escalation_chain)
            if shared_escalation_chains:
                shared_escalation_chains_verbal = ", ".join([ec.name for ec in shared_escalation_chains])
                raise TeamCanNotBeChangedError(
                    f"Team cannot be changed because one or more escalation chain of integration routes "
                    f"is connected to other integration: {shared_escalation_chains_verbal}"
                )

            escalation_policies = EscalationPolicy.objects.filter(escalation_chain__in=escalation_chains)

            users_in_escalation = self.organization.users.filter(escalationpolicy__in=escalation_policies)
            if new_team:
                team_members = new_team.users.filter(pk__in=[user.pk for user in users_in_escalation])
            else:
                team_members = self.organization.users.filter(pk__in=[user.pk for user in users_in_escalation])
            not_team_members = set(users_in_escalation) - set(team_members)
            if not_team_members:
                not_team_members_verbal = ", ".join([user.username for user in not_team_members])
                raise TeamCanNotBeChangedError(
                    f"Team cannot be changed because one or more user from escalation chain(s) is not a member "
                    f"of the selected team: {not_team_members_verbal}"
                )

            escalation_chains.update(team=new_team)
        self.team = new_team
        self.save(update_fields=["team"])

    @cached_property
    def grafana_alerting_sync_manager(self):
        return GrafanaAlertingSyncManager(self)

    @property
    def emojized_verbal_name(self):
        return emoji.emojize(self.verbal_name, use_aliases=True)

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
        Alert = apps.get_model("alerts", "Alert")
        return Alert.objects.filter(group__channel=self).count()

    @property
    def is_able_to_autoresolve(self):
        return self.config.is_able_to_autoresolve

    @property
    def is_demo_alert_enabled(self):
        return self.config.is_demo_alert_enabled

    @property
    def description(self):
        if self.integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING:
            contact_points = self.contact_points.all()
            rendered_description = Template(self.config.description).render(
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
            rendered_description = None
        return rendered_description

    @classmethod
    def get_or_create_manual_integration(cls, defaults, **kwargs):
        try:
            alert_receive_channel = cls.objects.get(
                organization=kwargs["organization"],
                integration=kwargs["integration"],
                team=kwargs["team"],
            )
        except cls.DoesNotExist:
            kwargs.update(defaults)
            alert_receive_channel = cls.create(**kwargs)
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
        return urljoin(self.organization.web_link, "?page=settings")

    @property
    def integration_url(self):
        if self.integration in [
            AlertReceiveChannel.INTEGRATION_MANUAL,
            AlertReceiveChannel.INTEGRATION_SLACK_CHANNEL,
            AlertReceiveChannel.INTEGRATION_INBOUND_EMAIL,
            AlertReceiveChannel.INTEGRATION_MAINTENANCE,
        ]:
            return None
        return create_engine_url(f"integrations/v1/{self.config.slug}/{self.token}/")

    @property
    def inbound_email(self):
        return f"{self.token}@{live_settings.SENDGRID_INBOUND_EMAIL_DOMAIN}"

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
            "email": {
                "title": self.email_title_template,
                "message": self.email_message_template,
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
    def is_available_for_integration_heartbeat(self):
        return self.heartbeat_module is not None

    @property
    def heartbeat_restored_title(self):
        return getattr(self.heartbeat_module, "heartbeat_restored_title")

    @property
    def heartbeat_restored_message(self):
        return getattr(self.heartbeat_module, "heartbeat_restored_message")

    @property
    def heartbeat_restored_payload(self):
        return getattr(self.heartbeat_module, "heartbeat_restored_payload")

    @property
    def heartbeat_expired_title(self):
        return getattr(self.heartbeat_module, "heartbeat_expired_title")

    @property
    def heartbeat_expired_message(self):
        return getattr(self.heartbeat_module, "heartbeat_expired_message")

    @property
    def heartbeat_expired_payload(self):
        return getattr(self.heartbeat_module, "heartbeat_expired_payload")

    @property
    def heartbeat_instruction_template(self):
        return getattr(self.heartbeat_module, "heartbeat_instruction_template")

    @property
    def heartbeat_module(self):
        return getattr(heartbeat, self.INTEGRATIONS_TO_REVERSE_URL_MAP[self.integration], None)

    # Demo alerts
    def send_demo_alert(self, force_route_id=None):
        logger.info(f"send_demo_alert integration={self.pk} force_route_id={force_route_id}")
        if self.is_demo_alert_enabled:
            if self.has_alertmanager_payload_structure:
                for alert in self.config.example_payload.get("alerts", []):
                    create_alertmanager_alerts.apply_async(
                        [],
                        {
                            "alert_receive_channel_pk": self.pk,
                            "alert": alert,
                            "is_demo": True,
                            "force_route_id": force_route_id,
                        },
                    )
            else:
                create_alert.apply_async(
                    [],
                    {
                        "title": "Demo alert",
                        "message": "Demo alert",
                        "image_url": None,
                        "link_to_upstream_details": None,
                        "alert_receive_channel_pk": self.pk,
                        "integration_unique_data": None,
                        "raw_request_data": self.config.example_payload,
                        "is_demo": True,
                        "force_route_id": force_route_id,
                    },
                )
        else:
            raise UnableToSendDemoAlert("Unable to send demo alert for this integration")

    @property
    def has_alertmanager_payload_structure(self):
        return self.integration in (
            AlertReceiveChannel.INTEGRATION_ALERTMANAGER,
            AlertReceiveChannel.INTEGRATION_GRAFANA,
            AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING,
        )

    # Insight logs
    @property
    def insight_logs_type_verbal(self):
        return "Integration"

    @property
    def insight_logs_verbal(self):
        return self.verbal_name

    @property
    def insight_logs_serialized(self):
        res = {
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
            "email_title_template": self.email_title_template or "default",
            "email_message": self.email_message_template or "default",
            "telegram_title": self.telegram_title_template or "default",
            "telegram_message": self.telegram_message_template or "default",
            "telegram_image_url": self.telegram_image_url_template or "default",
            "source_link": self.source_link_template or "default",
            "grouping_id": self.grouping_id_template or "default",
            "resolve_condition": self.resolve_condition_template or "default",
            "acknowledge_condition": self.acknowledge_condition_template or "default",
        }
        if self.team:
            res["team"] = self.team.name
            res["team_id"] = self.team.public_primary_key
        else:
            res["team"] = "General"
        return res

    @property
    def insight_logs_metadata(self):
        res = {}
        if self.team:
            res["team"] = self.team.name
            res["team_id"] = self.team.public_primary_key
        else:
            res["team"] = "General"
        return res


@receiver(post_save, sender=AlertReceiveChannel)
def listen_for_alertreceivechannel_model_save(sender, instance, created, *args, **kwargs):
    ChannelFilter = apps.get_model("alerts", "ChannelFilter")
    IntegrationHeartBeat = apps.get_model("heartbeat", "IntegrationHeartBeat")

    if created:
        entity_insight_log(instance=instance, author=instance.author, event=EntityEvent.CREATED)
        default_filter = ChannelFilter(alert_receive_channel=instance, filtering_term=None, is_default=True)
        default_filter.save()
        entity_insight_log(instance=default_filter, author=instance.author, event=EntityEvent.CREATED)

        TEN_MINUTES = 600  # this is timeout for cloud heartbeats
        if instance.is_available_for_integration_heartbeat:
            heartbeat = IntegrationHeartBeat.objects.create(alert_receive_channel=instance, timeout_seconds=TEN_MINUTES)
            entity_insight_log(instance=heartbeat, author=instance.author, event=EntityEvent.CREATED)

    if instance.integration == AlertReceiveChannel.INTEGRATION_GRAFANA_ALERTING:
        if created:
            instance.grafana_alerting_sync_manager.create_contact_points()
        # do not trigger sync contact points if field "is_finished_alerting_setup" was updated
        elif (
            kwargs is None
            or not kwargs.get("update_fields")
            or "is_finished_alerting_setup" not in kwargs["update_fields"]
        ):
            sync_grafana_alerting_contact_points.apply_async((instance.pk,), countdown=5)
