from rest_framework import serializers

from apps.alerts.models.channel_filter import ChannelFilter


class ChannelFilterSnapshotSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = ChannelFilter
        fields = [
            "id",
            "str_for_clients",
            "notify_in_slack",
            "notify_in_telegram",
            "notification_backends",
        ]

    def to_internal_value(self, data):
        result = super().to_internal_value(data)
        result["str_for_clients"] = data.get("str_for_clients")
        result["notification_backends"] = data.get("notification_backends")
        return result
