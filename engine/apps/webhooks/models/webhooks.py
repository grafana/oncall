import json
from json import JSONDecodeError

import requests
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.db import models
from mirage import fields as mirage_fields
from requests.auth import HTTPBasicAuth

from apps.alerts.utils import OUTGOING_WEBHOOK_TIMEOUT
from apps.webhooks.utils import InvalidWebhookTrigger, InvalidWebhookUrl, apply_jinja_template_for_json, parse_url
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


class Webhook(models.Model):

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
    name = models.CharField(max_length=100)
    username = models.CharField(max_length=100, null=True, default=None)
    password = mirage_fields.EncryptedCharField(max_length=200, null=True, default=None)
    authorization_header = models.CharField(max_length=1000, null=True, default=None)
    trigger_template = models.TextField(null=True, default=None)
    headers = models.JSONField(default=dict)
    headers_template = models.TextField(null=True, default=None)
    url = models.CharField(max_length=1000, null=True, default=None)
    url_template = models.TextField(null=True, default=None)
    data = models.TextField(null=True, default=None)
    forward_all = models.BooleanField(default=True)
    http_method = models.CharField(max_length=32, default="POST")

    def build_request_kwargs(self, event_data):
        request_kwargs = {}
        if self.user and self.password:
            request_kwargs["auth"] = HTTPBasicAuth(self.user, self.password)

        request_kwargs["headers"] = self.headers
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
                except (JinjaTemplateError, JinjaTemplateWarning) as e:
                    request_kwargs["json"] = {"error": e.fallback_message}

                try:
                    request_kwargs["json"] = json.loads(rendered_data)
                except JSONDecodeError:
                    request_kwargs["data"] = rendered_data

        return request_kwargs

    def build_url(self, event_data):
        url = self.url
        if self.url_template:
            try:
                url = apply_jinja_template(
                    self.url_template,
                    **event_data,
                )
            except (JinjaTemplateError, JinjaTemplateWarning) as e:
                raise InvalidWebhookUrl(e.fallback_message)

        parse_url(url)
        return url

    def check_trigger(self, event_data):
        if not self.trigger_template:
            return True

        try:
            result = apply_jinja_template(self.trigger_template, **event_data)
            return result.lower() in ["true", "1"]
        except (JinjaTemplateError, JinjaTemplateWarning) as e:
            raise InvalidWebhookTrigger(e.fallback_message)

        return True

    def make_request(self, event_data):
        url = self.build_url(event_data)
        request_kwargs = self.build_request_kwargs(event_data)
        if self.http_method == "GET":
            return requests.get(url, timeout=OUTGOING_WEBHOOK_TIMEOUT, **request_kwargs)
        elif self.http_method == "POST":
            return requests.post(url, timeout=OUTGOING_WEBHOOK_TIMEOUT, **request_kwargs)
        elif self.http_method == "PUT":
            return requests.put(url, timeout=OUTGOING_WEBHOOK_TIMEOUT, **request_kwargs)
        elif self.http_method == "DELETE":
            return requests.delete(url, timeout=OUTGOING_WEBHOOK_TIMEOUT, **request_kwargs)
        elif self.http_method == "OPTIONS":
            return requests.options(url, timeout=OUTGOING_WEBHOOK_TIMEOUT, **request_kwargs)
