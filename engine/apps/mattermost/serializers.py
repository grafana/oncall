from rest_framework import serializers

from apps.mattermost.client import MattermostClient
from apps.mattermost.exceptions import MattermostAPIException, MattermostAPITokenInvalid
from apps.mattermost.models import MattermostChannel
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.utils import CurrentOrganizationDefault


class MattermostChannelSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())

    class Meta:
        model = MattermostChannel
        fields = [
            "id",
            "organization",
            "mattermost_team_id",
            "channel_id",
            "channel_name",
            "display_name",
            "is_default_channel",
        ]
        extra_kwargs = {
            "mattermost_team_id": {"required": True, "write_only": True},
            "channel_id": {"required": True},
        }

    def create(self, validated_data):
        return MattermostChannel.objects.create(**validated_data)

    def to_internal_value(self, data):
        channel_id = data.get("channel_id")

        if not channel_id:
            raise serializers.ValidationError({"channel_id": "This field is required."})

        try:
            response = MattermostClient().get_channel_by_id(channel_id=channel_id)
        except MattermostAPIException as ex:
            raise BadRequest(detail=ex.msg)
        except MattermostAPITokenInvalid:
            raise BadRequest(detail="Mattermost API token is invalid.")

        return super().to_internal_value(
            {
                "channel_id": response.channel_id,
                "mattermost_team_id": response.team_id,
                "channel_name": response.channel_name,
                "display_name": response.display_name,
            }
        )
