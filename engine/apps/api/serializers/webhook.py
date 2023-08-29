from collections import defaultdict

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.webhooks.models import Webhook, WebhookResponse
from apps.webhooks.models.webhook import WEBHOOK_FIELD_PLACEHOLDER
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.utils import CurrentOrganizationDefault, CurrentTeamDefault, CurrentUserDefault
from common.jinja_templater import apply_jinja_template
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning


class WebhookResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookResponse
        fields = [
            "timestamp",
            "url",
            "request_trigger",
            "request_headers",
            "request_data",
            "status_code",
            "content",
            "event_data",
        ]


class WebhookSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    team = TeamPrimaryKeyRelatedField(allow_null=True, default=CurrentTeamDefault())
    user = serializers.HiddenField(default=CurrentUserDefault())
    trigger_type = serializers.CharField(required=True)
    forward_all = serializers.BooleanField(allow_null=True, required=False)
    last_response_log = serializers.SerializerMethodField()
    trigger_type_name = serializers.SerializerMethodField()

    class Meta:
        model = Webhook
        fields = [
            "id",
            "name",
            "is_webhook_enabled",
            "is_legacy",
            "team",
            "user",
            "username",
            "password",
            "authorization_header",
            "organization",
            "trigger_template",
            "headers",
            "url",
            "data",
            "forward_all",
            "http_method",
            "trigger_type",
            "trigger_type_name",
            "last_response_log",
            "integration_filter",
        ]
        extra_kwargs = {
            "name": {"required": True, "allow_null": False, "allow_blank": False},
            "url": {"required": True, "allow_null": False, "allow_blank": False},
        }

        validators = [UniqueTogetherValidator(queryset=Webhook.objects.all(), fields=["name", "organization"])]

    def to_representation(self, instance):
        result = super().to_representation(instance)
        if instance.password:
            result["password"] = WEBHOOK_FIELD_PLACEHOLDER
        if instance.authorization_header:
            result["authorization_header"] = WEBHOOK_FIELD_PLACEHOLDER
        return result

    def to_internal_value(self, data):
        webhook = self.instance

        # If webhook is being copied instance won't exist to copy values from
        if not webhook and "id" in data:
            webhook = Webhook.objects.get(
                public_primary_key=data["id"], organization=self.context["request"].auth.organization
            )

        if data.get("password") == WEBHOOK_FIELD_PLACEHOLDER:
            data["password"] = webhook.password
        if data.get("authorization_header") == WEBHOOK_FIELD_PLACEHOLDER:
            data["authorization_header"] = webhook.authorization_header
        return super().to_internal_value(data)

    def _validate_template_field(self, template):
        try:
            apply_jinja_template(template, alert_payload=defaultdict(str), alert_group_id="alert_group_1")
        except JinjaTemplateError as e:
            raise serializers.ValidationError(e.fallback_message)
        except JinjaTemplateWarning:
            # Suppress render exceptions since we do not have a representative payload to test with
            pass
        return template

    def validate_trigger_template(self, trigger_template):
        if not trigger_template:
            return None
        return self._validate_template_field(trigger_template)

    def validate_headers(self, headers):
        if not headers:
            return None
        return self._validate_template_field(headers)

    def validate_url(self, url):
        if not url:
            return None
        return self._validate_template_field(url)

    def validate_data(self, data):
        if not data:
            return None
        return self._validate_template_field(data)

    def validate_forward_all(self, data):
        if data is None:
            return False
        return data

    def get_last_response_log(self, obj):
        return WebhookResponseSerializer(obj.responses.all().last()).data

    def get_trigger_type_name(self, obj):
        trigger_type_name = ""
        if obj.trigger_type is not None:
            trigger_type_name = Webhook.TRIGGER_TYPES[int(obj.trigger_type)][1]
        return trigger_type_name
