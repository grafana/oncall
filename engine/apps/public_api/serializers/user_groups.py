from rest_framework import serializers

from apps.slack.models import SlackUserGroup


class UserGroupSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    type = serializers.SerializerMethodField(read_only=True)
    slack = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = SlackUserGroup
        fields = [
            "id",
            "type",
            "slack",
        ]

    def get_type(self, obj):
        return "slack_based"  # change when another group types will be able

    def get_slack(self, obj):
        return {
            "id": obj.slack_id,
            "name": obj.name,
            "handle": obj.handle,
        }
