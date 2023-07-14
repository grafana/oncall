from rest_framework import serializers

from apps.telegram.models import TelegramToOrganizationConnector, TelegramToUserConnector


class TelegramToUserConnectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramToUserConnector
        fields = ["telegram_nick_name", "telegram_chat_id"]


class TelegramToOrganizationConnectorSerializer(serializers.ModelSerializer):
    id = serializers.CharField(read_only=True, source="public_primary_key")

    class Meta:
        model = TelegramToOrganizationConnector
        fields = [
            "id",
            "channel_chat_id",
            "channel_name",
            "discussion_group_chat_id",
            "discussion_group_name",
            "is_default_channel",
        ]
