from rest_framework import serializers

from common.api_helpers.utils import CurrentOrganizationDefault


class ZoomUserIdentitySerializer(serializers.Serializer):
    """Serializer for Zoom user identity information."""
    zoom_user_id = serializers.CharField(read_only=True)
    email = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)


class ZoomChannelSerializer(serializers.Serializer):
    """Serializer for Zoom channel."""
    id = serializers.CharField(read_only=True, source="public_primary_key")
    organization = serializers.HiddenField(default=CurrentOrganizationDefault())
    channel_id = serializers.CharField()
    channel_name = serializers.CharField()
    is_default_channel = serializers.BooleanField(read_only=True)

    def create(self, validated_data):
        from apps.zoom.models import ZoomChannel
        return ZoomChannel.objects.create(**validated_data)

    def to_representation(self, instance):
        return {
            "id": instance.public_primary_key,
            "channel_id": instance.channel_id,
            "channel_name": instance.channel_name,
            "is_default_channel": instance.is_default_channel,
        }
