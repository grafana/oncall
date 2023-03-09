import json
from json import JSONDecodeError

import requests
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import F
from django.utils import timezone
from mirage import fields as mirage_fields
from requests.auth import HTTPBasicAuth

from apps.alerts.utils import OUTGOING_WEBHOOK_TIMEOUT
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


class WebhookQueryset(models.QuerySet):
    def delete(self):
        self.update(deleted_at=timezone.now(), name=F("name") + "_deleted_" + F("public_primary_key"))


class WebhookManager(models.Manager):
    def get_queryset(self):
        return WebhookQueryset(self.model, using=self._db).filter(deleted_at=None)

    def hard_delete(self):
        return self.get_queryset().hard_delete()


class Webhook(models.Model):
    objects = WebhookManager()
    objects_with_deleted = models.Manager()

    (
        TRIGGER_ESCALATION_STEP,
        TRIGGER_USER_NOTIFICATION_STEP,
        TRIGGER_NEW,
        TRIGGER_ACKNOWLEDGE,
        TRIGGER_RESOLVE,
        TRIGGER_SILENCE,
        TRIGGER_UNSILENCE,
        TRIGGER_UNRESOLVE,
        TRIGGER_SHIFT_CHANGE,
    ) = range(9)

    # Must be the same order as previous
    TRIGGER_TYPES = (
        (TRIGGER_ESCALATION_STEP, "Escalation step"),
        (TRIGGER_USER_NOTIFICATION_STEP, "User notification"),
        (TRIGGER_NEW, "Triggered"),
        (TRIGGER_ACKNOWLEDGE, "Acknowledged"),
        (TRIGGER_RESOLVE, "Resolved"),
        (TRIGGER_SILENCE, "Silenced"),
        (TRIGGER_UNSILENCE, "Unsilenced"),
        (TRIGGER_UNRESOLVE, "Unresolved"),
        (TRIGGER_SHIFT_CHANGE, "Schedule shift change"),
    )

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
        "user_management.Team", null=True, on_delete=models.CASCADE, related_name="webhooks", default=None
    )

    user = models.ForeignKey(
        "user_management.User", null=True, on_delete=models.CASCADE, related_name="webhooks", default=None
    )

    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(blank=True, null=True)
    name = models.CharField(max_length=100, null=True, default=None)
    username = models.CharField(max_length=100, null=True, default=None)
    password = mirage_fields.EncryptedCharField(max_length=200, null=True, default=None)
    authorization_header = models.CharField(max_length=1000, null=True, default=None)
    trigger_template = models.TextField(null=True, default=None)
    headers = models.TextField(null=True, default=None)
    url = models.TextField(null=True, default=None)
    data = models.TextField(null=True, default=None)
    forward_all = models.BooleanField(default=True)
    http_method = models.CharField(max_length=32, default="POST")
    trigger_type = models.IntegerField(choices=TRIGGER_TYPES, default=None, null=True)

    class Meta:
        unique_together = ("name", "organization")

    def __str__(self):
        return str(self.name)

    def delete(self):
        # TODO: self.escalation_policies.all().delete()
        self.deleted_at = timezone.now()
        # 100 - 22 = 78. 100 is max len of name field, and 22 is len of suffix _deleted_<public_primary_key>
        # So for case when user created button with maximum length name it is needed to trim it to 78 chars to be
        # able to add suffix.
        self.name = f"{self.name[:78]}_deleted_{self.public_primary_key}"
        self.save()

    def hard_delete(self):
        super().delete()

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

        if self.http_method in ["POST", "PUT"]:
            if self.forward_all:
                request_kwargs["json"] = event_data
            elif self.data:
                try:
                    rendered_data = apply_jinja_template_for_json(
                        self.data,
                        event_data,
                    )
                    try:
                        request_kwargs["json"] = json.loads(rendered_data)
                    except (JSONDecodeError, TypeError):
                        request_kwargs["data"] = rendered_data
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

    def check_trigger(self, event_data):
        if not self.trigger_template:
            return True, ""

        try:
            result = apply_jinja_template(self.trigger_template, **event_data)
            return result.lower() in ["true", "1"], result
        except (JinjaTemplateError, JinjaTemplateWarning) as e:
            raise InvalidWebhookTrigger(e.fallback_message)

    def make_request(self, url, request_kwargs):
        if self.http_method == "GET":
            r = requests.get(url, timeout=OUTGOING_WEBHOOK_TIMEOUT, **request_kwargs)
        elif self.http_method == "POST":
            r = requests.post(url, timeout=OUTGOING_WEBHOOK_TIMEOUT, **request_kwargs)
        elif self.http_method == "PUT":
            r = requests.put(url, timeout=OUTGOING_WEBHOOK_TIMEOUT, **request_kwargs)
        elif self.http_method == "DELETE":
            r = requests.delete(url, timeout=OUTGOING_WEBHOOK_TIMEOUT, **request_kwargs)
        elif self.http_method == "OPTIONS":
            r = requests.options(url, timeout=OUTGOING_WEBHOOK_TIMEOUT, **request_kwargs)
        else:
            raise Exception(f"Unsupported http method: {self.http_method}")
        return r

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


class WebhookLog(models.Model):
    last_run_at = models.DateTimeField(blank=True, null=True)
    input_data = models.JSONField(default=None)
    url = models.TextField(null=True, default=None)
    trigger = models.TextField(null=True, default=None)
    headers = models.TextField(null=True, default=None)
    data = models.TextField(null=True, default=None)
    response_status = models.CharField(max_length=100, null=True, default=None)
    response = models.TextField(null=True, default=None)
    webhook = models.ForeignKey(
        to="webhooks.Webhook",
        on_delete=models.CASCADE,
        related_name="logs",
        blank=False,
        null=False,
    )
