from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.public_api.serializers.webhooks import WebhookCreateSerializer, WebhookTriggerTypeField
from apps.webhooks.models import Webhook
from common.api_helpers.custom_fields import TeamPrimaryKeyRelatedField
from common.api_helpers.utils import CurrentTeamDefault


class ActionCreateSerializer(WebhookCreateSerializer):
    team_id = TeamPrimaryKeyRelatedField(allow_null=True, default=CurrentTeamDefault(), source="team")
    user = serializers.CharField(required=False, source="username", allow_null=True, allow_blank=True)
    trigger_type = WebhookTriggerTypeField(required=False)
    forward_whole_payload = serializers.BooleanField(required=False, source="forward_all")

    class Meta:
        model = Webhook
        fields = [
            "id",
            "name",
            "is_webhook_enabled",
            "organization",
            "team_id",
            "user",
            "data",
            "password",
            "authorization_header",
            "trigger_template",
            "headers",
            "url",
            "forward_whole_payload",
            "http_method",
            "trigger_type",
            "integration_filter",
        ]
        extra_kwargs = {
            "name": {"required": True, "allow_null": False, "allow_blank": False},
            "url": {"required": True, "allow_null": False, "allow_blank": False},
            "data": {"required": False, "allow_null": True, "allow_blank": True},
            "password": {"required": False, "allow_null": True, "allow_blank": True},
            "authorization_header": {"required": False, "allow_null": True, "allow_blank": True},
            "trigger_template": {"required": False, "allow_null": True, "allow_blank": True},
            "headers": {"required": False, "allow_null": True, "allow_blank": True},
            "integration_filter": {"required": False, "allow_null": True},
        }

        validators = [UniqueTogetherValidator(queryset=Webhook.objects.all(), fields=["name", "organization"])]


class ActionUpdateSerializer(ActionCreateSerializer):
    user = serializers.CharField(required=False, source="username", allow_null=True, allow_blank=True)
    trigger_type = WebhookTriggerTypeField(required=False)
    forward_whole_payload = serializers.BooleanField(required=False, source="forward_all")

    class Meta(ActionCreateSerializer.Meta):
        extra_kwargs = {
            "name": {"required": False, "allow_null": False, "allow_blank": False},
            "is_webhook_enabled": {"required": False, "allow_null": False},
            "user": {"required": False, "allow_null": True, "allow_blank": True},
            "password": {"required": False, "allow_null": True, "allow_blank": True},
            "authorization_header": {"required": False, "allow_null": True, "allow_blank": True},
            "trigger_template": {"required": False, "allow_null": True, "allow_blank": True},
            "headers": {"required": False, "allow_null": True, "allow_blank": True},
            "url": {"required": False, "allow_null": False, "allow_blank": False},
            "data": {"required": False, "allow_null": True, "allow_blank": True},
            "http_method": {"required": False, "allow_null": False, "allow_blank": False},
            "integration_filter": {"required": False, "allow_null": True},
        }
