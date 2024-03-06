from collections import defaultdict

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.api.serializers.labels import LabelsSerializerMixin
from apps.webhooks.models import Webhook, WebhookResponse
from apps.webhooks.models.webhook import PUBLIC_WEBHOOK_HTTP_METHODS, WEBHOOK_FIELD_PLACEHOLDER
from apps.webhooks.presets.preset_options import WebhookPresetOptions
from common.api_helpers.custom_fields import IntegrationFilteredByOrganizationField, TeamPrimaryKeyRelatedField
from common.api_helpers.utils import CurrentOrganizationDefault, CurrentUserDefault
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


class WebhookSerializer(LabelsSerializerMixin, serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    team = TeamPrimaryKeyRelatedField(allow_null=True, required=False)
    user = serializers.HiddenField(default=CurrentUserDefault())
    forward_all = serializers.BooleanField(allow_null=True, required=False)
    last_response_log = serializers.SerializerMethodField()
    trigger_type = serializers.CharField(allow_null=True)
    trigger_type_name = serializers.SerializerMethodField()
    integration_filter = IntegrationFilteredByOrganizationField(
        source="filtered_integrations", many=True, required=False
    )

    PREFETCH_RELATED = ["labels", "labels__key", "labels__value"]

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
            "preset",
            "labels",
        ]

        validators = [UniqueTogetherValidator(queryset=Webhook.objects.all(), fields=["name", "organization"])]

    def create(self, validated_data):
        organization = self.context["request"].auth.organization
        labels = validated_data.pop("labels", None)

        instance = super().create(validated_data)
        self.update_labels_association_if_needed(labels, instance, organization)
        return instance

    def update(self, instance, validated_data):
        labels = validated_data.pop("labels", None)
        organization = self.context["request"].auth.organization
        self.update_labels_association_if_needed(labels, instance, organization)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        result = super().to_representation(instance)
        if instance.password:
            result["password"] = WEBHOOK_FIELD_PLACEHOLDER
        if instance.authorization_header:
            result["authorization_header"] = WEBHOOK_FIELD_PLACEHOLDER
        return result

    def to_internal_value(self, data):
        webhook = self.instance

        # Some fields are conditionally required, add none values for missing required fields
        if webhook and webhook.preset and "preset" not in data:
            data["preset"] = webhook.preset
        for key in ["url", "http_method", "trigger_type"]:
            if key not in data:
                if self.instance:
                    data[key] = getattr(self.instance, key)
                else:
                    data[key] = None

        # If webhook is being copied instance won't exist to copy values from
        if not webhook and "id" in data:
            webhook = Webhook.objects.get(
                public_primary_key=data["id"], organization=self.context["request"].auth.organization
            )

        if data.get("password") == WEBHOOK_FIELD_PLACEHOLDER:
            data["password"] = webhook.password
        if data.get("authorization_header") == WEBHOOK_FIELD_PLACEHOLDER:
            data["authorization_header"] = webhook.authorization_header

        if not data.get("integration_filter"):
            data["integration_filter"] = []

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
        if self.is_field_controlled("url"):
            return url

        if not url:
            raise serializers.ValidationError(detail="This field is required.")
        return self._validate_template_field(url)

    def validate_http_method(self, http_method):
        if self.is_field_controlled("http_method"):
            return http_method

        if http_method not in PUBLIC_WEBHOOK_HTTP_METHODS:
            raise serializers.ValidationError(detail=f"This field must be one of {PUBLIC_WEBHOOK_HTTP_METHODS}.")
        return http_method

    def validate_trigger_type(self, trigger_type):
        if self.is_field_controlled("trigger_type"):
            return trigger_type

        if not trigger_type or int(trigger_type) not in Webhook.ALL_TRIGGER_TYPES:
            raise serializers.ValidationError(detail="This field is required.")
        return trigger_type

    def validate_data(self, data):
        if not data:
            return None
        return self._validate_template_field(data)

    def validate_forward_all(self, data):
        if data is None:
            return False
        return data

    def validate_preset(self, preset):
        if self.instance and self.instance.preset != preset:
            raise serializers.ValidationError(detail="This field once set cannot be modified.")

        if preset:
            if preset not in WebhookPresetOptions.WEBHOOK_PRESETS:
                raise serializers.ValidationError(detail=f"{preset} is not a valid preset id.")

            preset_metadata = WebhookPresetOptions.WEBHOOK_PRESETS[preset].metadata
            for controlled_field in preset_metadata.controlled_fields:
                if controlled_field in self.initial_data:
                    if self.instance:
                        if bool(self.initial_data[controlled_field]) and self.initial_data[controlled_field] != getattr(
                            self.instance, controlled_field
                        ):
                            raise serializers.ValidationError(
                                detail=f"{controlled_field} is controlled by preset, cannot update"
                            )
                    elif bool(self.initial_data[controlled_field]):
                        raise serializers.ValidationError(
                            detail=f"{controlled_field} is controlled by preset, cannot create"
                        )

        return preset

    def get_last_response_log(self, obj):
        return WebhookResponseSerializer(obj.responses.last()).data

    def get_trigger_type_name(self, obj):
        trigger_type_name = ""
        if obj.trigger_type is not None:
            trigger_type_name = Webhook.TRIGGER_TYPES[int(obj.trigger_type)][1]
        return trigger_type_name

    def is_field_controlled(self, field_name):
        if self.instance:
            if not self.instance.preset:
                return False
        elif "preset" not in self.initial_data:
            return False

        preset_id = self.instance.preset if self.instance else self.initial_data["preset"]
        if preset_id:
            if preset_id not in WebhookPresetOptions.WEBHOOK_PRESETS:
                raise serializers.ValidationError(detail=f"unknown preset {preset_id} referenced")

            preset = WebhookPresetOptions.WEBHOOK_PRESETS[preset_id]
            if field_name not in preset.metadata.controlled_fields:
                return False
        return True


class WebhookFastSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")

    class Meta:
        model = Webhook
        fields = ["id", "name"]
