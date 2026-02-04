from rest_framework import serializers


class ZoomChannelSerializer(serializers.Serializer):
    """Serializer for Zoom channel in public API."""
    name = serializers.CharField(source="channel_name")
    channel_id = serializers.CharField()
    is_default = serializers.BooleanField(source="is_default_channel")
