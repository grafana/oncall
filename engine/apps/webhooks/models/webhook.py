import json
import logging
import typing
from json import JSONDecodeError

import requests
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import F
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from mirage import fields as mirage_fields
from requests.auth import HTTPBasicAuth

from apps.webhooks.utils import (
    InvalidWebhookData,
    InvalidWebhookHeaders,
    InvalidWebhookTrigger,
    InvalidWebhookUrl,
    apply_jinja_template_for_json,
    parse_url,
)
from common.jinja_templater import apply_jinja_template
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning
from common.public_primary_keys import generate_public_primary_key, increase_public_primary_key_length

if typing.TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

    from apps.alerts.models import EscalationPolicy

WEBHOOK_FIELD_PLACEHOLDER = "****************"
PUBLIC_WEBHOOK_HTTP_METHODS = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]

logger = get_task_logger(__name__)
logger.setLevel(logging.DEBUG)


def generate_public_primary_key_for_webhook():
    prefix = "WH"
    new_public_primary_key = generate_public_primary_key(prefix)

    failure_counter = 0
    while Webhook.objects.filter(public_primary_key=new_public_primary_key).exists():
        new_public_primary_key = increase_public_primary_key_length(
            failure_counter=failure_counter, prefix=prefix, model_name="Webhook"
        )
        failure_counter += 1

    return new_public_primary_key


class WebhookSession(requests.Session):
    def send(self, request, **kwargs):
        parse_url(request.url)  # validate URL on every redirect
        return super().send(request, **kwargs)


class WebhookQueryset(models.QuerySet):
    def delete(self):
        self.update(deleted_at=timezone.now(), name=F("name") + "_deleted_" + F("public_primary_key"))


class WebhookManager(models.Manager):
    def get_queryset(self):
        return WebhookQueryset(self.model, using=self._db).filter(deleted_at=None)

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class Webhook(models.Model):
    escalation_policies: "RelatedManager['EscalationPolicy']"

    objects = WebhookManager()
    objects_with_deleted = models.Manager()

    (
        TRIGGER_ESCALATION_STEP,
        TRIGGER_ALERT_GROUP_CREATED,
        TRIGGER_ACKNOWLEDGE,
        TRIGGER_RESOLVE,
        TRIGGER_SILENCE,
        TRIGGER_UNSILENCE,
        TRIGGER_UNRESOLVE,
        TRIGGER_UNACKNOWLEDGE,
        TRIGGER_STATUS_CHANGE,
    ) = range(9)

    # Must be the same order as previous
    TRIGGER_TYPES = (
        (TRIGGER_ESCALATION_STEP, "Escalation step"),
        (TRIGGER_ALERT_GROUP_CREATED, "Alert Group Created"),
        (TRIGGER_ACKNOWLEDGE, "Acknowledged"),
        (TRIGGER_RESOLVE, "Resolved"),
        (TRIGGER_SILENCE, "Silenced"),
        (TRIGGER_UNSILENCE, "Unsilenced"),
        (TRIGGER_UNRESOLVE, "Unresolved"),
        (TRIGGER_UNACKNOWLEDGE, "Unacknowledged"),
        (TRIGGER_STATUS_CHANGE, "Status change"),
    )

    ALL_TRIGGER_TYPES = [i[0] for i in TRIGGER_TYPES]
    STATUS_CHANGE_TRIGGERS = {
        TRIGGER_ACKNOWLEDGE,
        TRIGGER_RESOLVE,
        TRIGGER_SILENCE,
        TRIGGER_UNSILENCE,
        TRIGGER_UNRESOLVE,
        TRIGGER_UNACKNOWLEDGE,
    }

    PUBLIC_TRIGGER_TYPES_MAP = {
        TRIGGER_ESCALATION_STEP: "escalation",
        TRIGGER_ALERT_GROUP_CREATED: "alert group created",
        TRIGGER_ACKNOWLEDGE: "acknowledge",
        TRIGGER_RESOLVE: "resolve",
        TRIGGER_SILENCE: "silence",
        TRIGGER_UNSILENCE: "unsilence",
        TRIGGER_UNRESOLVE: "unresolve",
        TRIGGER_UNACKNOWLEDGE: "unacknowledge",
        TRIGGER_STATUS_CHANGE: "status change",
    }

    PUBLIC_ALL_TRIGGER_TYPES = [i for i in PUBLIC_TRIGGER_TYPES_MAP.values()]

    public_primary_key = models.CharField(
        max_length=20,
        validators=[MinLengthValidator(settings.PUBLIC_PRIMARY_KEY_MIN_LENGTH + 1)],
        unique=True,
        default=generate_public_primary_key_for_webhook,
    )

    organization = models.ForeignKey(
        "user_management.Organization", null=True, on_delete=models.CASCADE, related_name="webhooks", default=None
    )

    team = models.ForeignKey(
        "user_management.Team", null=True, on_delete=models.SET_NULL, related_name="webhooks", default=None
    )

    user = models.ForeignKey(
        "user_management.User", null=True, on_delete=models.CASCADE, related_name="webhooks", default=None
    )

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=100, null=True, default=None)
    username = models.CharField(max_length=100, null=True, default=None)
    password = mirage_fields.EncryptedCharField(max_length=1000, null=True, default=None)
    authorization_header = mirage_fields.EncryptedCharField(max_length=2000, null=True, default=None)
    trigger_template = models.TextField(null=True, default=None)
    headers = models.TextField(null=True, default=None)
    url = models.TextField(null=True, default=None)
    data = models.TextField(null=True, default=None)
    forward_all = models.BooleanField(default=True)
    http_method = models.CharField(max_length=32, default="POST", null=True)
    trigger_type = models.IntegerField(choices=TRIGGER_TYPES, default=TRIGGER_ESCALATION_STEP, null=True)
    is_webhook_enabled = models.BooleanField(null=True, default=True)
    # NOTE: integration_filter is deprecated (to be removed), use filtered_integrations instead
    integration_filter = models.JSONField(default=None, null=True, blank=True)
    filtered_integrations = models.ManyToManyField("alerts.AlertReceiveChannel", related_name="webhooks")
    is_legacy = models.BooleanField(null=True, default=False)
    preset = models.CharField(max_length=100, null=True, blank=True, default=None)

    is_from_connected_integration = models.BooleanField(null=True, default=False)

    class Meta:
        unique_together = ("name", "organization")

    def __str__(self):
        return str(self.name)

    def delete(self):
        # TODO: delete related escalation policies on delete, once implemented
        # self.escalation_policies.all().delete()
        self.deleted_at = timezone.now()
        # 100 - 22 = 78. 100 is max len of name field, and 22 is len of suffix _deleted_<public_primary_key>
        # So for case when user created an entry with maximum length name it is needed to trim it to 78 chars
        # to be able to add suffix.
        self.name = f"{self.name[:78]}_deleted_{self.public_primary_key}"
        self.save()

    def hard_delete(self):
        super().delete()

    def get_source_alert_receive_channel(self):
        """Return the webhook source channel if it is connected to an integration."""
        result = None
        if self.is_from_connected_integration:
            filtered_integration = (
                Webhook.filtered_integrations.through.objects.filter(
                    alertreceivechannel__additional_settings__isnull=False, webhook=self
                )
                .order_by("id")
                .first()
            )
            result = filtered_integration.alertreceivechannel if filtered_integration else None
        return result

    def build_request_kwargs(self, event_data, raise_data_errors=False):
        request_kwargs = {}
        if self.username and self.password:
            request_kwargs["auth"] = HTTPBasicAuth(self.username, self.password)

        request_kwargs["headers"] = {}
        if self.headers:
            try:
                rendered_headers = apply_jinja_template_for_json(
                    self.headers,
                    event_data,
                )
                request_kwargs["headers"] = json.loads(rendered_headers)
            except (JinjaTemplateError, JinjaTemplateWarning) as e:
                raise InvalidWebhookHeaders(e.fallback_message)
            except JSONDecodeError:
                raise InvalidWebhookHeaders("Template did not result in json/dict")

        if self.authorization_header:
            request_kwargs["headers"]["Authorization"] = self.authorization_header

        if self.http_method in ["POST", "PUT", "PATCH"]:
            if self.forward_all:
                request_kwargs["json"] = event_data
                if self.is_legacy:
                    request_kwargs["json"] = event_data["alert_payload"]
            elif self.data:
                context_data = event_data
                if self.is_legacy:
                    context_data = {
                        "alert_payload": event_data.get("alert_payload", {}),
                        "alert_group_id": event_data.get("alert_group_id"),
                    }
                try:
                    rendered_data = apply_jinja_template_for_json(
                        self.data,
                        context_data,
                    )
                    try:
                        request_kwargs["json"] = json.loads(rendered_data)
                    except (JSONDecodeError, TypeError):
                        # utf-8 encoding addresses https://github.com/grafana/oncall/issues/3831
                        request_kwargs["data"] = rendered_data.encode("utf-8")
                except (JinjaTemplateError, JinjaTemplateWarning) as e:
                    if raise_data_errors:
                        raise InvalidWebhookData(e.fallback_message)
                    else:
                        request_kwargs["json"] = {"error": e.fallback_message}

        return request_kwargs

    def build_url(self, event_data):
        try:
            url = apply_jinja_template(
                self.url,
                **event_data,
            )
        except (JinjaTemplateError, JinjaTemplateWarning) as e:
            raise InvalidWebhookUrl(e.fallback_message)

        # raise if URL is not valid
        parse_url(url)

        return url

    def check_integration_filter(self, alert_group):
        if self.filtered_integrations.count() == 0:
            return True
        return self.filtered_integrations.filter(id=alert_group.channel.id).exists()

    def check_trigger(self, event_data):
        if not self.trigger_template:
            return True, ""

        try:
            result = apply_jinja_template(self.trigger_template, **event_data)
            return result.lower() in ["true", "1"], result
        except (JinjaTemplateError, JinjaTemplateWarning) as e:
            raise InvalidWebhookTrigger(e.fallback_message)

    def make_request(self, url, request_kwargs):
        if self.http_method not in ("GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"):
            raise ValueError(f"Unsupported http method: {self.http_method}")

        with WebhookSession() as session:
            response = session.request(
                self.http_method, url, timeout=settings.OUTGOING_WEBHOOK_TIMEOUT, **request_kwargs
            )

        return response

    # Insight logs
    @property
    def insight_logs_type_verbal(self):
        return "webhook"

    @property
    def insight_logs_verbal(self):
        return self.name

    def _insight_log_team(self):
        result = {"team": "General"}
        if self.team:
            result["team"] = self.team.name
            result["team_id"] = self.team.public_primary_key
        return result

    @property
    def insight_logs_serialized(self):
        result = {
            "name": self.name,
            "trigger_type": self.trigger_type,
            "url": self.url,
            "data": self.data,
            "forward_all": self.forward_all,
        }
        result.update(self._insight_log_team())
        return result

    @property
    def insight_logs_metadata(self):
        result = {}
        result.update(self._insight_log_team())
        return result


class WebhookResponse(models.Model):
    alert_group = models.ForeignKey(
        "alerts.AlertGroup",
        on_delete=models.CASCADE,
        null=True,
        related_name="webhook_responses",
    )
    webhook = models.ForeignKey(
        "webhooks.Webhook",
        on_delete=models.SET_NULL,
        null=True,
        related_name="responses",
    )
    trigger_type = models.IntegerField(choices=Webhook.TRIGGER_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)
    request_trigger = models.TextField(null=True, default=None)
    request_headers = models.TextField(null=True, default=None)
    request_data = models.TextField(null=True, default=None)
    url = models.TextField(null=True, default=None)
    status_code = models.IntegerField(default=None, null=True)
    content = models.TextField(null=True, default=None)
    event_data = models.TextField(null=True, default=None)

    def json(self):
        if self.content:
            return json.loads(self.content)


@receiver(post_save, sender=WebhookResponse)
def webhook_response_post_save(sender, instance, created, *args, **kwargs):
    if not created:
        return

    source_alert_receive_channel = instance.webhook.get_source_alert_receive_channel()
    if source_alert_receive_channel and hasattr(source_alert_receive_channel.config, "on_webhook_response_created"):
        source_alert_receive_channel.config.on_webhook_response_created(instance, source_alert_receive_channel)
