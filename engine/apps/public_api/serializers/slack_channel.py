from rest_framework import serializers

from apps.slack.models import SlackChannel


class SlackChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SlackChannel
        fields = ["name", "slack_id"]
