from rest_framework import serializers

from apps.slack.models import SlackChannel


class SlackChannelSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    display_name = serializers.CharField(source="name")

    class Meta:
        model = SlackChannel
        fields = ["id", "display_name", "slack_id"]
        read_only_fields = ["id", "display_name", "slack_id"]
