from collections import defaultdict

from rest_framework import fields, serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.alerts.models import AlertReceiveChannel
from apps.webhooks.models import Webhook, WebhookResponse
from apps.webhooks.models.webhook import PUBLIC_WEBHOOK_HTTP_METHODS, WEBHOOK_FIELD_PLACEHOLDER
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.utils import CurrentOrganizationDefault, CurrentTeamDefault, CurrentUserDefault
from common.jinja_templater import apply_jinja_template
from common.jinja_templater.apply_jinja_template import JinjaTemplateError, JinjaTemplateWarning

INTEGRATION_FILTER_MESSAGE = "integration_filter must be a list of valid integration ids"


class WebhookTriggerTypeField(fields.CharField):
    def to_representation(self, value):
        return Webhook.PUBLIC_TRIGGER_TYPES_MAP[value]

    def to_internal_value(self, data):
        try:
            trigger_type = [
                key
                for key, value in Webhook.PUBLIC_TRIGGER_TYPES_MAP.items()
                if value == data and key in Webhook.PUBLIC_TRIGGER_TYPES_MAP
            ][0]
        except IndexError:
            raise BadRequest(detail=f"trigger_type must one of {Webhook.PUBLIC_ALL_TRIGGER_TYPES}")
        return trigger_type


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


class WebhookCreateSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    team = TeamPrimaryKeyRelatedField(allow_null=True, default=CurrentTeamDefault())
    user = serializers.HiddenField(default=CurrentUserDefault())
    trigger_type = WebhookTriggerTypeField()

    class Meta:
        model = Webhook
        fields = [
            "id",
            "name",
            "is_webhook_enabled",
            "organization",
            "team",
            "user",
            "data",
            "username",
            "password",
            "authorization_header",
            "trigger_template",
            "headers",
            "url",
            "forward_all",
            "http_method",
            "trigger_type",
            "integration_filter",
        ]
        extra_kwargs = {
            "name": {"required": True, "allow_null": False, "allow_blank": False},
            "url": {"required": True, "allow_null": False, "allow_blank": False},
            "http_method": {"required": True, "allow_null": False, "allow_blank": False},
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

    def validate_http_method(self, http_method):
        if http_method not in PUBLIC_WEBHOOK_HTTP_METHODS:
            raise serializers.ValidationError(f"Must be one of {PUBLIC_WEBHOOK_HTTP_METHODS}")
        return http_method

    def validate_integration_filter(self, integration_filter):
        if integration_filter:
            if type(integration_filter) is not list:
                raise serializers.ValidationError(INTEGRATION_FILTER_MESSAGE)
            integrations = AlertReceiveChannel.objects.filter(
                organization=self.context["request"].auth.organization, public_primary_key__in=integration_filter
            )
            if len(integrations) != len(integration_filter):
                raise serializers.ValidationError(INTEGRATION_FILTER_MESSAGE)
        return integration_filter


class WebhookUpdateSerializer(WebhookCreateSerializer):
    trigger_type = WebhookTriggerTypeField(required=False)

    class Meta(WebhookCreateSerializer.Meta):
        extra_kwargs = {
            "name": {"required": False, "allow_null": False, "allow_blank": False},
            "is_webhook_enabled": {"required": False, "allow_null": False},
            "username": {"required": False, "allow_null": True, "allow_blank": False},
            "password": {"required": False, "allow_null": True, "allow_blank": False},
            "authorization_header": {"required": False, "allow_null": True, "allow_blank": False},
            "trigger_template": {"required": False, "allow_null": True, "allow_blank": False},
            "headers": {"required": False, "allow_null": True, "allow_blank": False},
            "url": {"required": False, "allow_null": False, "allow_blank": False},
            "data": {"required": False, "allow_null": True, "allow_blank": False},
            "forward_all": {"required": False, "allow_null": False},
            "http_method": {"required": False, "allow_null": False, "allow_blank": False},
            "integration_filter": {"required": False, "allow_null": True},
        }
