from rest_framework import serializers

from apps.webhooks.models import Webhook
from apps.webhooks.models.webhooks import WebhookLog


class WebhookSerializer(serializers.ModelSerializer):
    pk = serializers.CharField(read_only=True, source="public_primary_key")

    class Meta:
        model = Webhook
        fields = [
            "pk",
            "name",
            "created_at",
            "username",
            "password",
            "authorization_header",
            "trigger_template",
            "headers",
            "headers_template",
            "url",
            "url_template",
            "data",
            "forward_all",
            "http_method",
            "trigger_type",
        ]
        read_only_fields = ["created_at"]
        extra_kwargs = {
            "password": {"write_only": True},
            "authorization_header": {"write_only": True},
        }


class WebhookLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookLog
        fields = [
            "last_run_at",
            "input_data",
            "url",
            "trigger",
            "request",
            "response_status",
            "response",
        ]
