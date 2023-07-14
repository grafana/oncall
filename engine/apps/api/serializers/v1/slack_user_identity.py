from rest_framework import serializers

from apps.slack.models import SlackUserIdentity


class SlackUserIdentitySerializer(serializers.ModelSerializer):
    slack_login = serializers.CharField(read_only=True, source="cached_slack_login")
    avatar = serializers.CharField(read_only=True, source="cached_avatar")
    name = serializers.CharField(read_only=True, source="cached_name")
    display_name = serializers.SerializerMethodField()

    class Meta:
        model = SlackUserIdentity
        fields = ["slack_login", "slack_id", "avatar", "name", "display_name"]
        read_only_fields = ["slack_login", "slack_id", "avatar", "name", "display_name"]

    def get_display_name(self, obj):
        return obj.profile_display_name or obj.slack_verbal
