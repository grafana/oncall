from rest_framework import serializers

from apps.slack.models import SlackUserGroup


class UserGroupSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")

    class Meta:
        model = SlackUserGroup
        fields = ("id", "name", "handle")
