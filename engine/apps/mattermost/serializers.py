from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from apps.mattermost.client import MattermostClient
from apps.mattermost.exceptions import MattermostAPIException, MattermostAPITokenInvalid
from apps.mattermost.models import MattermostChannel
from common.api_helpers.utils import CurrentOrganizationDefault


class MattermostChannelSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    channel_id = serializers.CharField()
    channel_name = serializers.CharField()

    class Meta:
        model = MattermostChannel
        fields = [
            "id",
            "organization",
            "channel_id",
            "channel_name",
        ]
        validators = [
            UniqueTogetherValidator(queryset=MattermostChannel.objects.all(), fields=["organization", "channel_id"])
        ]

    def create(self, validated_data):
        return MattermostChannel.objects.create(**validated_data)

    def to_internal_value(self, data):
        team_name = data.get("team_name")
        channel_name = data.get("channel_name")

        if not team_name:
            raise serializers.ValidationError({"team_name": "This field is required."})

        if not channel_name:
            raise serializers.ValidationError({"channel_name": "This field is required."})

        try:
            response = MattermostClient().get_channel_by_name_and_team_name(
                team_name=team_name, channel_name=channel_name
            )
        except (MattermostAPIException, MattermostAPITokenInvalid):
            raise serializers.ValidationError("Unable to fetch channel from mattermost server")

        return super().to_internal_value({"channel_id": response.channel_id, "channel_name": response.channel_name})
