from rest_framework import serializers

from apps.zoom.client import ZoomClient
from apps.zoom.exceptions import ZoomAPIException, ZoomAPITokenInvalid
from apps.zoom.models import ZoomChannel
from common.api_helpers.exceptions import BadRequest
from common.api_helpers.utils import CurrentOrganizationDefault


class ZoomChannelSerializer(serializers.ModelSerializer):
    """Serializer for ZoomChannel model."""
    
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())

    class Meta:
        model = ZoomChannel
        fields = [
            "id",
            "organization",
            "channel_id",
            "channel_name",
            "is_default_channel",
        ]
        extra_kwargs = {
            "channel_id": {"required": True},
        }

    def create(self, validated_data):
        return ZoomChannel.objects.create(**validated_data)

    def to_internal_value(self, data):
        channel_id = data.get("channel_id")

        if not channel_id:
            raise serializers.ValidationError({"channel_id": "This field is required."})

        try:
            client = ZoomClient()
            response = client.get_channel(channel_id=channel_id)
        except ZoomAPIException as ex:
            raise BadRequest(detail=ex.msg)
        except ZoomAPITokenInvalid:
            raise BadRequest(detail="Zoom API token is invalid.")

        return super().to_internal_value(
            {
                "channel_id": response.channel_id,
                "channel_name": response.channel_name,
            }
        )
